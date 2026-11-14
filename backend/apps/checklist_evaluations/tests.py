from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.test import APIClient
from apps.reference_architectures import services as ra_services
from apps.reference_architectures.models import ReferenceArchitectureMember, ArchitecturalElementType, RAElement
from apps.checklists import services as checklist_services
from apps.checklists.models import ChecklistSection, Question
from .models import ChecklistEvaluation, EvaluationParticipant, ParticipantRole
from . import services

BASE = '/api/checklist-evaluations/'


class EvaluationFixture:
    def setUp(self):
        super().setUp()
        self.owner = get_user_model().objects.create_user(email='owner@evaluation.test', name='Responsável')
        self.reader = get_user_model().objects.create_user(email='reader@evaluation.test', name='Participante')
        self.other = get_user_model().objects.create_user(email='other@evaluation.test', name='Externo')
        self.ra = ra_services.create_reference_architecture(user=self.owner, name='RA', visibility='PRIVATE',
            initial_version={'version': '1', 'description_markdown': 'Descrição privada'})
        self.ra_version = self.ra.versions.get()
        self.checklist = checklist_services.create_checklist(user=self.owner, name='Checklist', visibility='PRIVATE', origin='', initial_version={'version': '1'})
        self.version = self.checklist.versions.get()
        self.section = checklist_services.save_section(user=self.owner, version=self.version, data={'name': 'Geral'})
        self.role = checklist_services.save_stakeholder(user=self.owner, version=self.version, data={'name': 'Arquiteto'})
        self.role2 = checklist_services.save_stakeholder(user=self.owner, version=self.version, data={'name': 'Especialista'})
        self.question = checklist_services.save_question(user=self.owner, version=self.version,
            data={'statement': 'Critério', 'response_type': 'SINGLE_CHOICE', 'comment_mode': 'REQUIRED',
                  'section_id': self.section.pk, 'stakeholder_ids': [self.role.pk], 'options': [{'label': 'Alternativa própria', 'order_index': 0}]})
        self.type = ArchitecturalElementType.objects.create(name='Tipo', created_by_user=self.owner)
        self.element = ra_services.create_element(user=self.owner, version=self.ra_version,
            data={'name': 'Elemento', 'element_type': self.type, 'description_markdown': 'Descrição'})
        self.evaluation = services.create_evaluation(user=self.owner, ra_version_id=self.ra_version.pk, checklist_version_id=self.version.pk)
        self.url = f'{BASE}{self.evaluation.pk}/'
        self.client = APIClient(enforce_csrf_checks=True)
        self.client.force_login(self.owner)

    def write(self, url, data=None, method='post', csrf=True):
        headers = {'HTTP_X_CSRFTOKEN': self.client.get('/api/auth/csrf/').json()['csrfToken']} if csrf else {}
        return getattr(self.client, method)(url, data or {}, format='json', **headers)

    def add(self, roles=None, email=None):
        return self.write(self.url + 'participants/', {'email': email or self.reader.email, 'stakeholder_role_ids': roles or []})

    def participant(self):
        return services.save_participant(user=self.owner, evaluation=self.evaluation, email=self.reader.email, stakeholder_role_ids=[self.role.pk])

    def start(self):
        self.participant()
        return services.start_evaluation(user=self.owner, evaluation=self.evaluation)


class EvaluationTests(EvaluationFixture, TestCase):
    def test_creation_draft_exact_versions_and_creator(self):
        result = self.write(BASE, {'ra_version_id': self.ra_version.pk, 'checklist_version_id': self.version.pk})
        self.assertEqual(result.status_code, 201)
        evaluation = ChecklistEvaluation.objects.get(pk=result.data['id'])
        self.assertEqual((evaluation.status, evaluation.created_by_user_id, evaluation.ra_version_id, evaluation.checklist_version_id),
                         ('DRAFT', self.owner.pk, self.ra_version.pk, self.version.pk))
        self.assertFalse(evaluation.participants.exists())
        self.assertEqual(result.data['ra_version']['architecture_id'], self.ra.pk)
        self.assertEqual(result.data['checklist_version']['checklist_id'], self.checklist.pk)

    def test_reject_client_creator_status_and_redundant_fields(self):
        payload = {'ra_version_id': self.ra_version.pk, 'checklist_version_id': self.version.pk}
        for key, value in [('created_by_user', self.other.pk), ('created_by_user_id', self.other.pk), ('status', 'COMPLETED'), ('reference_architecture_id', self.ra.pk), ('checklist_id', self.checklist.pk), ('title', 'extra')]:
            self.assertEqual(self.write(BASE, {**payload, key: value}).status_code, 400)
            self.assertEqual(self.write(self.url, {key: value}, 'patch').status_code, 400)

    def test_deliberate_duplicate_combinations_allowed(self):
        payload = {'ra_version_id': self.ra_version.pk, 'checklist_version_id': self.version.pk}
        first = self.write(BASE, payload)
        second = self.write(BASE, payload)
        self.assertEqual((first.status_code, second.status_code), (201, 201))
        self.assertNotEqual(first.data['id'], second.data['id'])

    def test_public_artifacts_reused_without_edit_rights(self):
        self.ra.visibility = 'PUBLIC'; self.ra.save()
        self.checklist.visibility = 'PUBLIC'; self.checklist.save()
        self.client.force_login(self.other)
        response = self.write(BASE, {'ra_version_id': self.ra_version.pk, 'checklist_version_id': self.version.pk})
        self.assertEqual(response.status_code, 201)
        self.assertFalse(self.ra.members.filter(user=self.other).exists())
        self.assertEqual(self.write(f'/api/reference-architectures/{self.ra.pk}/', {'name': 'x'}, 'patch').status_code, 403)
        self.assertEqual(self.write(f'/api/checklists/{self.checklist.pk}/', {'name': 'x'}, 'patch').status_code, 403)
        self.assertEqual(self.checklist.owner_user_id, self.owner.pk)

    def test_ra_editor_can_select_private_version(self):
        ReferenceArchitectureMember.objects.create(reference_architecture=self.ra, user=self.other, role='EDITOR')
        self.checklist.visibility = 'PUBLIC'; self.checklist.save()
        self.client.force_login(self.other)
        self.assertEqual(self.write(BASE, {'ra_version_id': self.ra_version.pk, 'checklist_version_id': self.version.pk}).status_code, 201)

    def test_private_and_nonexistent_versions_rejected(self):
        self.client.force_login(self.other)
        for ra_id, checklist_id in [(self.ra_version.pk, self.version.pk), (999999, self.version.pk), (self.ra_version.pk, 999999)]:
            self.assertEqual(self.write(BASE, {'ra_version_id': ra_id, 'checklist_version_id': checklist_id}).status_code, 404)
        self.ra.visibility = 'PUBLIC'; self.ra.save()
        self.assertEqual(self.write(BASE, {'ra_version_id': self.ra_version.pk, 'checklist_version_id': self.version.pk}).status_code, 404)

    def test_selection_choices_only_accessible_metadata(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(BASE + 'choices/').data, {'architectures': [], 'checklists': []})
        self.ra.visibility = 'PUBLIC'; self.ra.save()
        self.checklist.visibility = 'PUBLIC'; self.checklist.save()
        choices = self.client.get(BASE + 'choices/').json()
        self.assertEqual(choices['architectures'][0]['versions'][0]['id'], self.ra_version.pk)
        self.assertEqual(choices['checklists'][0]['versions'][0]['id'], self.version.pk)
        self.assertNotIn('description_markdown', str(choices))
        self.assertNotIn('owner_user', str(choices))

    def test_registered_email_case_insensitive_and_optional_roles(self):
        response = self.add(email=self.reader.email.upper())
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['id'], self.reader.pk)
        self.assertEqual(response.data['stakeholder_roles'], [])
        self.assertFalse(ParticipantRole.objects.exists())

    def test_multiple_distinct_roles(self):
        response = self.add(roles=[self.role.pk, self.role2.pk])
        self.assertEqual(response.status_code, 201)
        self.assertEqual({role['id'] for role in response.data['stakeholder_roles']}, {self.role.pk, self.role2.pk})

    def test_creator_not_automatic_but_can_join(self):
        self.assertFalse(self.evaluation.participants.exists())
        self.assertEqual(self.add(email=self.owner.email).status_code, 201)
        self.assertEqual(self.client.get(self.url).data['own_participation']['user']['id'], self.owner.pk)

    def test_unknown_email_duplicate_user_and_duplicate_roles(self):
        self.assertEqual(self.add(email='missing@example.test').status_code, 400)
        self.assertFalse(self.evaluation.participants.exists())
        self.assertEqual(self.add(roles=[self.role.pk, self.role.pk]).status_code, 400)
        self.assertFalse(self.evaluation.participants.exists())
        self.assertEqual(self.add().status_code, 201)
        self.assertEqual(self.add().status_code, 400)
        self.assertEqual(self.evaluation.participants.count(), 1)

    def test_database_uniqueness_and_status_constraints(self):
        participant = self.participant()
        for operation in [
            lambda: EvaluationParticipant.objects.create(checklist_evaluation=self.evaluation, user=self.reader),
            lambda: ParticipantRole.objects.create(evaluation_participant=participant, stakeholder_role=self.role),
            lambda: ChecklistEvaluation.objects.filter(pk=self.evaluation.pk).update(status='LOCKED'),
        ]:
            with self.assertRaises(IntegrityError), transaction.atomic(): operation()

    def test_roles_from_other_version_or_checklist_rejected(self):
        version = checklist_services.create_version(user=self.owner, checklist=self.checklist, version='2')
        foreign = checklist_services.save_stakeholder(user=self.owner, version=version, data={'name': 'Externo'})
        for roles in [[foreign.pk], [self.role.pk, 999999], [self.role.pk, foreign.pk]]:
            self.assertEqual(self.add(roles=roles).status_code, 400)
        self.assertFalse(self.evaluation.participants.exists())
        self.assertEqual(self.add([self.role.pk]).status_code, 201)
        participant = self.evaluation.participants.get()
        self.assertEqual(self.write(self.url + f'participants/{participant.pk}/', {'stakeholder_role_ids': [foreign.pk]}, 'patch').status_code, 400)
        self.assertEqual(list(participant.stakeholder_roles.values_list('pk', flat=True)), [self.role.pk])

    def test_participant_and_roles_transaction_rollback(self):
        with patch('apps.checklist_evaluations.services.ParticipantRole.objects.bulk_create', side_effect=IntegrityError('test')):
            with self.assertRaises(IntegrityError): self.participant()
        self.assertFalse(self.evaluation.participants.exists())
        participant = self.participant()
        with patch('apps.checklist_evaluations.services.ParticipantRole.objects.bulk_create', side_effect=IntegrityError('test')):
            with self.assertRaises(IntegrityError):
                services.save_participant(user=self.owner, evaluation=self.evaluation, participant=participant, stakeholder_role_ids=[self.role2.pk])
        self.assertEqual(list(participant.stakeholder_roles.values_list('pk', flat=True)), [self.role.pk])

    def test_update_roles_and_remove_before_start(self):
        participant = self.participant()
        url = self.url + f'participants/{participant.pk}/'
        self.assertEqual(self.write(url, {'stakeholder_role_ids': []}, 'patch').status_code, 200)
        self.assertFalse(participant.stakeholder_roles.exists())
        self.assertEqual(self.write(url, {'stakeholder_role_ids': [self.role2.pk]}, 'patch').status_code, 200)
        self.assertEqual(self.write(url, method='delete').status_code, 204)
        self.assertFalse(self.evaluation.participants.exists())
        self.assertFalse(ParticipantRole.objects.exists())

    def test_participant_url_scoped_to_evaluation(self):
        participant = self.participant()
        other = services.create_evaluation(user=self.owner, ra_version_id=self.ra_version.pk, checklist_version_id=self.version.pk)
        self.assertEqual(self.write(f'{BASE}{other.pk}/participants/{participant.pk}/', {'stakeholder_role_ids': []}, 'patch').status_code, 404)
        self.assertEqual(self.write(f'{BASE}{other.pk}/participants/{participant.pk}/', method='delete').status_code, 404)

    def test_draft_change_checklist_clears_roles_and_preserves_people(self):
        participant = self.participant()
        version = checklist_services.create_version(user=self.owner, checklist=self.checklist, version='2')
        response = self.write(self.url, {'checklist_version_id': version.pk}, 'patch')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.evaluation.participants.count(), 1)
        self.assertFalse(participant.stakeholder_roles.exists())
        self.assertEqual(response.data['checklist_version']['id'], version.pk)

    def test_draft_same_checklist_or_ra_change_keeps_roles(self):
        participant = self.participant()
        version = ra_services.create_version(architecture=self.ra, version='2', description_markdown='Nova')
        self.assertEqual(self.write(self.url, {'ra_version_id': version.pk, 'checklist_version_id': self.version.pk}, 'patch').status_code, 200)
        self.assertEqual(list(participant.stakeholder_roles.values_list('pk', flat=True)), [self.role.pk])

    def test_invalid_version_revision_does_not_clear_roles(self):
        participant = self.participant()
        self.assertEqual(self.write(self.url, {'checklist_version_id': 999999}, 'patch').status_code, 404)
        self.assertTrue(participant.stakeholder_roles.exists())

    def test_start_valid_evaluation(self):
        self.add([self.role.pk])
        response = self.write(self.url + 'start/')
        self.assertEqual(response.status_code, 200)
        self.evaluation.refresh_from_db()
        self.assertEqual(self.evaluation.status, 'IN_PROGRESS')
        self.assertEqual(response.data, {'id': self.evaluation.pk, 'status': 'IN_PROGRESS'})

    def test_start_requires_participants_and_questions(self):
        self.assertEqual(self.write(self.url + 'start/').status_code, 400)
        self.participant()
        self.question.delete()
        self.assertEqual(self.write(self.url + 'start/').status_code, 400)
        self.evaluation.refresh_from_db()
        self.assertEqual(self.evaluation.status, 'DRAFT')

    def test_start_rejects_invalid_question_configurations(self):
        self.participant()
        for changes in [{'statement': ' '}, {'response_type': 'TEXT'}]:
            with transaction.atomic():
                Question.objects.filter(pk=self.question.pk).update(**changes)
                self.assertEqual(self.write(self.url + 'start/').status_code, 400)
                transaction.set_rollback(True)
        self.question.options.all().delete()
        self.assertEqual(self.write(self.url + 'start/').status_code, 400)

    def test_start_rechecks_artifact_access(self):
        self.ra.visibility = 'PUBLIC'; self.ra.save()
        self.checklist.visibility = 'PUBLIC'; self.checklist.save()
        evaluation = services.create_evaluation(user=self.other, ra_version_id=self.ra_version.pk, checklist_version_id=self.version.pk)
        services.save_participant(user=self.other, evaluation=evaluation, email=self.reader.email, stakeholder_role_ids=[])
        self.client.force_login(self.other)
        self.checklist.visibility = 'PRIVATE'; self.checklist.save()
        self.assertEqual(self.write(f'{BASE}{evaluation.pk}/start/').status_code, 400)
        self.assertEqual(self.client.get(f'{BASE}{evaluation.pk}/').data['available_stakeholders'], [])
        self.checklist.visibility = 'PUBLIC'; self.checklist.save()
        self.ra.visibility = 'PRIVATE'; self.ra.save()
        self.assertEqual(self.write(f'{BASE}{evaluation.pk}/start/').status_code, 400)
        evaluation.refresh_from_db(); self.assertEqual(evaluation.status, 'DRAFT')

    def test_after_start_no_restart_version_roles_or_removal(self):
        self.start()
        participant = self.evaluation.participants.get()
        for url, data, method in [(self.url + 'start/', {}, 'post'), (self.url, {'ra_version_id': self.ra_version.pk}, 'patch'),
                                 (self.url + 'participants/', {'email': self.other.email, 'stakeholder_role_ids': []}, 'post'),
                                 (self.url + f'participants/{participant.pk}/', {'stakeholder_role_ids': []}, 'patch'),
                                 (self.url + f'participants/{participant.pk}/', {}, 'delete')]:
            self.assertEqual(self.write(url, data, method).status_code, 400)
        self.assertEqual(self.write(self.url, {'status': 'DRAFT'}, 'patch').status_code, 400)

    def test_external_and_participant_cannot_configure(self):
        participant = self.participant()
        for user, status in [(self.other, 404), (self.reader, 403)]:
            self.client.force_login(user)
            for url, data, method in [(self.url, {'ra_version_id': self.ra_version.pk}, 'patch'),
                (self.url + 'participants/', {'email': self.owner.email, 'stakeholder_role_ids': []}, 'post'),
                (self.url + f'participants/{participant.pk}/', {'stakeholder_role_ids': []}, 'patch'),
                (self.url + f'participants/{participant.pk}/', {}, 'delete'), (self.url + 'start/', {}, 'post')]:
                self.assertEqual(self.write(url, data, method).status_code, status)

    def test_lists_and_participant_limited_context(self):
        self.participant()
        services.save_participant(user=self.owner, evaluation=self.evaluation, email=self.other.email, stakeholder_role_ids=[])
        self.client.force_login(self.reader)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('participants', response.data)
        self.assertNotIn('available_stakeholders', response.data)
        self.assertNotIn(self.other.email, str(response.data))
        self.assertNotIn('description_markdown', str(response.data))
        self.assertEqual(response.data['own_participation']['user']['id'], self.reader.pk)
        self.assertTrue(response.data['is_participant']); self.assertFalse(response.data['is_creator'])
        self.assertEqual([item['user']['id'] for item in self.client.get(self.url + 'participants/').data], [self.reader.pk])
        self.assertEqual(len(self.client.get(BASE).data), 1)
        self.assertEqual(self.client.get(f'/api/reference-architectures/{self.ra.pk}/').status_code, 404)
        self.assertEqual(self.client.get(f'/api/checklists/{self.checklist.pk}/').status_code, 404)
        external = get_user_model().objects.create_user(email='external@evaluation.test', name='Externo')
        self.client.force_login(external)
        self.assertEqual(self.client.get(BASE).data, [])
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.client.get(self.url + 'participants/').status_code, 404)

    def test_anonymous_and_csrf_all_mutations(self):
        participant = self.participant()
        payload = {'ra_version_id': self.ra_version.pk, 'checklist_version_id': self.version.pk}
        writes = [(BASE, payload, 'post'), (self.url, payload, 'patch'), (self.url + 'start/', {}, 'post'),
                  (self.url + 'participants/', {'email': self.other.email, 'stakeholder_role_ids': []}, 'post'),
                  (self.url + f'participants/{participant.pk}/', {'stakeholder_role_ids': []}, 'patch'),
                  (self.url + f'participants/{participant.pk}/', {}, 'delete')]
        for url, data, method in writes:
            self.assertEqual(self.write(url, data, method, csrf=False).status_code, 403)
        self.client.logout()
        for url in [BASE, self.url, self.url + 'participants/', BASE + 'choices/']:
            self.assertEqual(self.client.get(url).status_code, 403)
        for url, data, method in writes:
            self.assertEqual(self.write(url, data, method).status_code, 403)

    def test_no_evaluation_deletion_or_completion_of_draft(self):
        self.assertEqual(self.write(self.url, method='delete').status_code, 405)
        # AVA-03 adds completion, but a DRAFT still cannot transition directly to COMPLETED.
        self.assertEqual(self.write(self.url + 'complete/').status_code, 400)
        self.assertEqual(self.write(self.url + 'start/', {'status': 'COMPLETED'}).status_code, 400)

    def structural_writes(self):
        qpath = f'/api/checklists/{self.checklist.pk}/versions/{self.version.pk}/'
        rpath = f'/api/reference-architectures/{self.ra.pk}/versions/{self.ra_version.pk}/elements/'
        return [
            (rpath, {'name': 'Novo', 'element_type_id': self.type.pk, 'description_markdown': 'x'}, 'post'),
            (rpath + f'{self.element.pk}/', {'name': 'Editado'}, 'patch'),
            (qpath + 'sections/', {'name': 'Nova'}, 'post'),
            (qpath + f'sections/{self.section.pk}/', {'name': 'Editada'}, 'patch'),
            (qpath + 'stakeholders/', {'name': 'Novo'}, 'post'),
            (qpath + f'stakeholders/{self.role.pk}/', {'name': 'Editado'}, 'patch'),
            (qpath + 'questions/', {'statement': 'Nova', 'response_type': 'TEXT', 'comment_mode': 'NONE'}, 'post'),
            (qpath + f'questions/{self.question.pk}/', {'statement': 'Editada', 'stakeholder_ids': []}, 'patch'),
            (qpath + f'questions/{self.question.pk}/', {'options': [{'label': 'Substituída', 'order_index': 0}]}, 'patch'),
            (qpath + 'sections/reorder/', {'ids': [self.section.pk]}, 'post'),
            (qpath + 'questions/reorder/', {'ids': [self.question.pk]}, 'post'),
        ]

    def test_all_structural_mutations_blocked_after_start(self):
        before = list(self.question.options.values())
        self.start()
        for url, data, method in self.structural_writes():
            response = self.write(url, data, method)
            self.assertEqual(response.status_code, 400, (url, response.data))
            self.assertIn('nova versão', str(response.data))
        self.assertEqual(list(self.question.options.values()), before)
        self.assertEqual(RAElement.objects.get(pk=self.element.pk).name, 'Elemento')

    def test_completed_and_additional_draft_do_not_unfreeze_versions(self):
        self.start()
        ChecklistEvaluation.objects.filter(pk=self.evaluation.pk).update(status='COMPLETED')
        services.create_evaluation(user=self.owner, ra_version_id=self.ra_version.pk, checklist_version_id=self.version.pk)
        for url, data, method in self.structural_writes():
            self.assertEqual(self.write(url, data, method).status_code, 400)

    def test_draft_versions_remain_editable(self):
        for url, data, method in self.structural_writes()[:6]:
            self.assertIn(self.write(url, data, method).status_code, [200, 201])
        self.assertEqual(self.write(self.structural_writes()[7][0], {'statement': 'Editada'}, 'patch').status_code, 200)

    def test_new_versions_and_metadata_remain_editable(self):
        self.start()
        rurl = f'/api/reference-architectures/{self.ra.pk}/'
        curl = f'/api/checklists/{self.checklist.pk}/'
        self.assertEqual(self.write(rurl, {'name': 'Novo nome', 'visibility': 'PUBLIC'}, 'patch').status_code, 200)
        self.assertEqual(self.write(curl, {'name': 'Novo nome', 'visibility': 'PUBLIC'}, 'patch').status_code, 200)
        self.assertEqual(self.write(rurl + 'versions/', {'version': '2', 'description_markdown': 'Nova'}).status_code, 201)
        self.assertEqual(self.write(curl + 'versions/', {'version': '2'}).status_code, 201)
        ra_new = self.ra.versions.get(version='2')
        checklist_new = self.checklist.versions.get(version='2')
        ra_services.create_element(user=self.owner, version=ra_new, data={'name': 'Livre', 'element_type': self.type, 'description_markdown': 'x'})
        checklist_services.save_section(user=self.owner, version=checklist_new, data={'name': 'Livre'})

    def test_frozen_status_is_derived_not_stored_flag(self):
        self.assertFalse(self.client.get(f'/api/reference-architectures/{self.ra.pk}/').data['versions'][0]['is_frozen'])
        self.start()
        self.assertTrue(self.client.get(f'/api/reference-architectures/{self.ra.pk}/').data['versions'][0]['is_frozen'])
        self.assertTrue(self.client.get(f'/api/checklists/{self.checklist.pk}/').data['versions'][0]['is_frozen'])

    def test_services_enforce_creator_without_views(self):
        with self.assertRaises(PermissionDenied): services.start_evaluation(user=self.other, evaluation=self.evaluation)
        with self.assertRaises(PermissionDenied): services.update_versions(user=self.other, evaluation=self.evaluation, data={})
        with self.assertRaises(PermissionDenied): services.save_participant(user=self.other, evaluation=self.evaluation, email=self.reader.email, stakeholder_role_ids=[])
