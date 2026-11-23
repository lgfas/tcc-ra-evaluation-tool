from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db import IntegrityError
from django.test import TestCase
from rest_framework.exceptions import NotAuthenticated, ValidationError
from rest_framework.test import APIClient
from apps.version_protection import version_is_frozen
from . import services
from .models import Checklist, ChecklistVersion, ChecklistSection, StakeholderRole, Question, ResponseOption, QuestionStakeholder


class DerivationFixture:
    def setUp(self):
        super().setUp()
        self.owner = get_user_model().objects.create_user(email='source@derive.test', name='Autoria original')
        self.user = get_user_model().objects.create_user(email='derived@derive.test', name='Autoria derivada')
        self.source = services.create_checklist(user=self.owner, name='Instrumento original', origin='Fonte acadêmica',
                                               visibility='PUBLIC', initial_version={'version': '2.0'})
        self.version = self.source.versions.get()
        self.sections = [services.save_section(user=self.owner, version=self.version, data={'name': name})
                         for name in ['Objetivos', 'Estrutura']]
        self.roles = [services.save_stakeholder(user=self.owner, version=self.version,
                     data={'name': name, 'description': f'Descrição de {name}'}) for name in ['Arquiteto', 'Especialista', 'Não associado']]
        specs = [('Comum textual', 'TEXT', 'NONE', None, []),
                 ('Escolha com dois papéis', 'SINGLE_CHOICE', 'OPTIONAL', self.sections[0], self.roles[:2]),
                 ('Texto e justificativa', 'TEXT', 'REQUIRED', self.sections[1], self.roles[:1]),
                 ('Escolha comum', 'SINGLE_CHOICE', 'REQUIRED', None, []),
                 ('Texto opcional', 'TEXT', 'OPTIONAL', None, self.roles[1:2])]
        self.questions = []
        for statement, response_type, comment_mode, section, roles in specs:
            data = {'statement': statement, 'response_type': response_type, 'comment_mode': comment_mode,
                    'section_id': section.pk if section else None, 'stakeholder_ids': [role.pk for role in roles]}
            if response_type == 'SINGLE_CHOICE':
                data['options'] = [{'label': 'Própria alternativa B', 'order_index': 8}, {'label': 'Própria alternativa A', 'order_index': 2}]
            self.questions.append(services.save_question(user=self.owner, version=self.version, data=data))
        self.other_version = services.create_version(user=self.owner, checklist=self.source, version='3.0')
        services.save_question(user=self.owner, version=self.other_version,
            data={'statement': 'Não copiar outra versão', 'response_type': 'TEXT', 'comment_mode': 'NONE'})
        self.client = APIClient(enforce_csrf_checks=True)
        self.client.force_login(self.user)
        self.payload = {'source_checklist_version_id': self.version.pk, 'name': 'Adaptação independente',
                        'origin': 'Origem confirmada pelo usuário', 'visibility': 'PRIVATE', 'initial_version': {'version': '1.0'}}

    def derive(self, **changes):
        return services.derive_checklist(user=self.user, **{**self.payload, **changes})

    def post(self, payload=None, *, csrf=True):
        headers = {'HTTP_X_CSRFTOKEN': self.client.get('/api/auth/csrf/').json()['csrfToken']} if csrf else {}
        return self.client.post('/api/checklists/derive/', self.payload if payload is None else payload, format='json', **headers)

    def graph(self, version):
        return {
            'sections': list(version.sections.values_list('name', 'order_index')),
            'roles': list(version.stakeholders.values_list('name', 'description')),
            'questions': [{'statement': q.statement, 'response_type': q.response_type, 'comment_mode': q.comment_mode,
                'order_index': q.order_index, 'section': q.section.name if q.section_id else None,
                'roles': list(q.stakeholders.values_list('name', flat=True)),
                'options': list(q.options.values_list('label', 'order_index'))} for q in version.questions.select_related('section')],
        }

    def counts(self):
        return [model.objects.count() for model in [Checklist, ChecklistVersion, ChecklistSection, StakeholderRole,
                                                    Question, ResponseOption, QuestionStakeholder]]


class DerivationTests(DerivationFixture, TestCase):
    def test_public_third_party_derivation_has_new_owner_ids_metadata_and_exact_source(self):
        response = self.post()
        self.assertEqual(response.status_code, 201, response.data)
        derived = Checklist.objects.get(pk=response.data['id'])
        self.assertNotEqual(derived.pk, self.source.pk)
        self.assertEqual(derived.owner_user, self.user)
        self.assertEqual(derived.derived_from_checklist_version, self.version)
        self.assertEqual((derived.name, derived.origin, derived.visibility),
                         (self.payload['name'], self.payload['origin'], 'PRIVATE'))
        version = derived.versions.get()
        self.assertNotEqual(version.pk, self.version.pk)
        self.assertEqual(version.version, '1.0')
        self.assertEqual(response.data['version_count'], 1)
        self.assertTrue(response.data['can_edit'])
        self.assertFalse(response.data['versions'][0]['is_frozen'])
        self.assertEqual(response.data['versions'][0]['id'], version.pk)
        self.assertEqual(response.data['derivation_source'], {'available': True, 'checklist_id': self.source.pk,
            'name': self.source.name, 'version_id': self.version.pk, 'version': '2.0'})
        own_ids = [item['id'] for item in self.client.get('/api/checklists/').data]
        self.assertIn(derived.pk, own_ids)
        self.assertNotIn(self.source.pk, own_ids)
        self.client.force_login(self.owner)
        self.assertNotIn(derived.pk, [item['id'] for item in self.client.get('/api/checklists/').data])

    def test_public_self_derivation_is_allowed_and_independent(self):
        self.client.force_login(self.owner)
        response = self.post()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['owner_user'], self.owner.pk)
        self.assertNotEqual(response.data['id'], self.source.pk)

    def test_all_structure_and_order_copied_from_only_selected_version(self):
        version = self.derive().versions.get()
        self.assertEqual(self.graph(version), self.graph(self.version))
        self.assertEqual(version.questions.count(), 5)
        self.assertEqual(version.stakeholders.count(), 3)
        self.assertNotIn('Não copiar outra versão', str(self.graph(version)))

    def test_new_ids_and_remapped_sections_roles_options_links(self):
        version = self.derive().versions.get()
        for original, copied in [(self.version.sections, version.sections), (self.version.stakeholders, version.stakeholders),
                                 (self.version.questions, version.questions)]:
            self.assertFalse(set(original.values_list('pk', flat=True)) & set(copied.values_list('pk', flat=True)))
        original_options = set(ResponseOption.objects.filter(question__checklist_version=self.version).values_list('pk', flat=True))
        new_options = ResponseOption.objects.filter(question__checklist_version=version)
        self.assertEqual(new_options.count(), len(original_options))
        self.assertFalse(original_options & set(new_options.values_list('pk', flat=True)))
        original_links = set(QuestionStakeholder.objects.filter(question__checklist_version=self.version).values_list('pk', flat=True))
        links = QuestionStakeholder.objects.filter(question__checklist_version=version)
        self.assertEqual(links.count(), len(original_links))
        self.assertFalse(original_links & set(links.values_list('pk', flat=True)))
        self.assertTrue(all(link.stakeholder_role.checklist_version_id == version.pk for link in links.select_related('stakeholder_role')))
        for question in version.questions.select_related('section'):
            self.assertTrue(question.section_id is None or question.section.checklist_version_id == version.pk)
            self.assertTrue(all(role.checklist_version_id == version.pk for role in question.stakeholders.all()))

    def test_unsectioned_common_multiple_roles_types_comments_and_options(self):
        copied = list(self.derive().versions.get().questions.all())
        self.assertIsNone(copied[0].section_id)
        self.assertFalse(copied[0].stakeholders.exists())
        self.assertIsNone(copied[3].section_id)
        self.assertFalse(copied[3].stakeholders.exists())
        self.assertEqual(copied[1].stakeholders.count(), 2)
        self.assertEqual([q.comment_mode for q in copied], ['NONE', 'OPTIONAL', 'REQUIRED', 'REQUIRED', 'OPTIONAL'])
        for question in copied:
            self.assertEqual(question.options.count(), 0 if question.response_type == 'TEXT' else 2)

    def test_order_indices_preserved_even_when_not_contiguous(self):
        self.questions[-1].order_index = 15
        self.questions[-1].save()
        last_option = self.questions[1].options.last()
        last_option.order_index = 6
        last_option.save()
        self.assertEqual(self.graph(self.derive().versions.get()), self.graph(self.version))

    def test_empty_public_source_can_be_derived(self):
        empty = services.create_version(user=self.owner, checklist=self.source, version='Vazia')
        self.assertEqual(self.graph(self.derive(source_checklist_version_id=empty.pk).versions.get()),
                         {'sections': [], 'roles': [], 'questions': []})

    def test_anonymous_and_csrf_are_blocked(self):
        self.assertEqual(self.post(csrf=False).status_code, 403)
        self.client.logout()
        self.assertEqual(self.post().status_code, 403)
        with self.assertRaises(NotAuthenticated):
            services.derive_checklist(user=AnonymousUser(), **self.payload)

    def test_private_source_is_rejected_even_for_its_owner(self):
        services.update_checklist(user=self.owner, checklist=self.source, data={'visibility': 'PRIVATE'})
        before = self.counts()
        for user in [self.user, self.owner]:
            self.client.force_login(user)
            self.assertEqual(self.post().status_code, 404)
        self.assertEqual(self.counts(), before)

    def test_missing_and_invalid_version_ids(self):
        for value, status in [(999999, 404), (0, 400), (-1, 400), (None, 400), ('wrong', 400), (2**63, 400)]:
            self.assertEqual(self.post({**self.payload, 'source_checklist_version_id': value}).status_code, status)

    def test_strict_payload_prevents_forged_owner_relations_and_structure(self):
        before = self.counts()
        for field, value in [('owner_user', self.owner.pk), ('owner_user_id', self.owner.pk),
            ('derived_from_checklist_version', self.other_version.pk), ('source_checklist_id', self.source.pk),
            ('derived_from_checklist_version_id', self.other_version.pk), ('questions', []), ('sections', []),
            ('stakeholders', []), ('id', self.source.pk)]:
            self.assertEqual(self.post({**self.payload, field: value}).status_code, 400, field)
        self.assertEqual(self.post({**self.payload, 'initial_version': {'version': '1', 'checklist': self.source.pk}}).status_code, 400)
        self.assertEqual(self.counts(), before)
        self.assertEqual(self.client.post('/api/checklists/', {**{k:v for k,v in self.payload.items() if k != 'source_checklist_version_id'},
            'derived_from_checklist_version': self.version.pk}, format='json',
            HTTP_X_CSRFTOKEN=self.client.get('/api/auth/csrf/').json()['csrfToken']).status_code, 400)

    def test_metadata_and_initial_version_validation(self):
        for changes in [{'name': ' '}, {'name': 'x' * 256}, {'visibility': 'INVALID'}, {'origin': None},
                        {'initial_version': {'version': ''}}, {'initial_version': {'version': 'x' * 101}}]:
            self.assertEqual(self.post({**self.payload, **changes}).status_code, 400)
        payload = {key: value for key, value in self.payload.items() if key != 'origin'}
        self.assertEqual(self.post(payload).data['origin'], '')

    def test_derived_public_checklist_enters_catalog(self):
        response = self.post({**self.payload, 'visibility': 'PUBLIC'})
        self.assertEqual(response.status_code, 201)
        self.assertIn(response.data['id'], [item['id'] for item in self.client.get('/api/catalog/?type=checklist').data])

    def test_original_and_derived_have_no_mutual_edit_rights(self):
        derived = self.derive(visibility='PUBLIC')
        for user, target in [(self.user, self.source), (self.owner, derived)]:
            self.client.force_login(user)
            token = self.client.get('/api/auth/csrf/').json()['csrfToken']
            self.assertEqual(self.client.patch(f'/api/checklists/{target.pk}/', {'name': 'Não permitido'},
                format='json', HTTP_X_CSRFTOKEN=token).status_code, 403)

    def test_derived_structure_can_change_without_modifying_source(self):
        before = self.graph(self.version)
        derived = self.derive()
        version = derived.versions.get()
        choice = version.questions.get(statement=self.questions[1].statement)
        services.save_question(user=self.user, version=version, instance=choice,
            data={'statement': 'Nova questão', 'options': [{'label': 'Alternativa independente', 'order_index': 0}], 'stakeholder_ids': []})
        services.save_stakeholder(user=self.user, version=version, instance=version.stakeholders.first(),
                                 data={'name': 'Papel independente', 'description': 'Nova descrição'})
        services.save_section(user=self.user, version=version, instance=version.sections.first(), data={'name': 'Seção independente'})
        self.assertEqual(self.graph(self.version), before)
        self.assertFalse(version_is_frozen(checklist_version_id=version.pk))

    def test_later_version_is_empty_and_original_edits_do_not_sync(self):
        derived = self.derive()
        before = self.graph(derived.versions.get())
        empty = services.create_version(user=self.user, checklist=derived, version='2')
        self.assertEqual(self.graph(empty), {'sections': [], 'roles': [], 'questions': []})
        services.save_question(user=self.owner, version=self.version, instance=self.questions[0], data={'statement': 'Mudança posterior na origem'})
        self.assertEqual(self.graph(derived.versions.get(version='1.0')), before)
        self.assertFalse(version_is_frozen(checklist_version_id=self.version.pk))

    def test_source_becomes_private_without_affecting_derivative_or_leaking_new_metadata(self):
        derived = self.derive(visibility='PUBLIC')
        before = self.graph(derived.versions.get())
        services.update_checklist(user=self.owner, checklist=self.source, data={'visibility': 'PRIVATE', 'name': 'Nome privado posterior'})
        self.assertEqual(self.post().status_code, 404)
        data = self.client.get(f'/api/checklists/{derived.pk}/').data
        self.assertEqual(data['derivation_source'], {'available': False})
        self.assertNotIn('Nome privado posterior', str(data))
        self.assertEqual(data['derived_from_checklist_version'], self.version.pk)
        self.assertEqual(self.client.get(f'/api/checklists/{self.source.pk}/').status_code, 404)
        self.assertEqual(self.graph(derived.versions.get()), before)
        outsider = get_user_model().objects.create_user(email='reader@derive.test', name='Leitor')
        self.client.force_login(outsider)
        self.assertEqual(self.client.get(f'/api/checklists/{derived.pk}/').data['derivation_source'], {'available': False})
        self.client.force_login(self.owner)
        self.assertTrue(self.client.get(f'/api/checklists/{derived.pk}/').data['derivation_source']['available'])

    def test_normal_checklist_has_no_provenance_metadata(self):
        self.assertIsNone(self.client.get(f'/api/checklists/{self.source.pk}/').data['derivation_source'])

    def test_rollback_at_copy_stages_leaves_no_partial_records(self):
        for target in ['ChecklistSection.objects.create', 'StakeholderRole.objects.create', 'Question.objects.create',
                       'ResponseOption.objects.bulk_create', 'QuestionStakeholder.objects.bulk_create']:
            before = self.counts()
            with patch('apps.checklists.services.' + target, side_effect=IntegrityError('Falha durante cópia')):
                with self.assertRaises(IntegrityError):
                    self.derive()
            self.assertEqual(self.counts(), before, target)
        before = self.counts()
        with self.assertRaises(ValidationError):
            self.derive(initial_version={'version': ''})
        self.assertEqual(self.counts(), before)

    def test_inconsistent_cross_version_source_relationships_are_rejected(self):
        foreign = services.save_section(user=self.owner, version=self.other_version, data={'name': 'Seção externa'})
        Question.objects.filter(pk=self.questions[0].pk).update(section=foreign)
        before = self.counts()
        with self.assertRaises(ValidationError):
            self.derive()
        self.assertEqual(self.counts(), before)
        Question.objects.filter(pk=self.questions[0].pk).update(section=None)
        foreign_role = services.save_stakeholder(user=self.owner, version=self.other_version, data={'name': 'Papel externo'})
        QuestionStakeholder.objects.create(question=self.questions[0], stakeholder_role=foreign_role)
        before = self.counts()
        with self.assertRaises(ValidationError):
            self.derive()
        self.assertEqual(self.counts(), before)

    def test_frozen_in_progress_and_completed_sources_preserve_history_and_answers(self):
        from apps.reference_architectures import services as ra_services
        from apps.checklist_evaluations import services as evaluations
        from apps.checklist_evaluations.models import ChecklistEvaluation, EvaluationParticipant, ParticipantRole, Answer
        ra = ra_services.create_reference_architecture(user=self.owner, name='RA', visibility='PRIVATE',
            initial_version={'version': '1', 'description_markdown': ''})
        evaluation = evaluations.create_evaluation(user=self.owner, ra_version_id=ra.versions.get().pk, checklist_version_id=self.version.pk)
        evaluations.save_participant(user=self.owner, evaluation=evaluation, email=self.owner.email, stakeholder_role_ids=[])
        evaluations.start_evaluation(user=self.owner, evaluation=evaluation)
        evaluations.save_answer(user=self.owner, evaluation_id=evaluation.pk, question_id=self.questions[0].pk, data={'text_value': 'Não copiar resposta'})
        for completed in [False, True]:
            if completed:
                evaluations.complete_evaluation(user=self.owner, evaluation=evaluation, confirm_incomplete=True)
            before = {model: list(model.objects.values()) for model in [ChecklistEvaluation, EvaluationParticipant, ParticipantRole, Answer]}
            source_before = self.graph(self.version)
            derived = self.derive()
            self.assertEqual(self.graph(derived.versions.get()), source_before)
            self.assertEqual(self.graph(self.version), source_before)
            self.assertEqual({model: list(model.objects.values()) for model in before}, before)
            self.assertTrue(version_is_frozen(checklist_version_id=self.version.pk))
            self.assertFalse(version_is_frozen(checklist_version_id=derived.versions.get().pk))
            with self.assertRaises(ValidationError):
                services.save_question(user=self.owner, version=self.version, instance=self.questions[0], data={'statement': 'Não modificar'})
            self.assertFalse(Answer.objects.filter(question__checklist_version=derived.versions.get()).exists())
