from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.exceptions import PermissionDenied
from .models import Checklist, ChecklistVersion, ChecklistSection, StakeholderRole, Question, ResponseOption, QuestionStakeholder
from . import services

BASE = '/api/checklists/'


class ChecklistTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(email='owner@check.test', name='Owner')
        self.other = get_user_model().objects.create_user(email='other@check.test', name='Other')
        self.client = APIClient(enforce_csrf_checks=True)
        self.client.force_login(self.owner)
        self.payload = {'name': 'Instrumento', 'origin': 'Fonte acadêmica', 'visibility': 'PRIVATE', 'initial_version': {'version': '1.0'}}
        self.checklist = services.create_checklist(user=self.owner, **self.payload)
        self.version = self.checklist.versions.get()
        self.url = f'{BASE}{self.checklist.pk}/'
        self.path = self.url + f'versions/{self.version.pk}/'
        self.section = services.save_section(user=self.owner, version=self.version, data={'name': 'Geral'})
        self.role = services.save_stakeholder(user=self.owner, version=self.version, data={'name': 'Arquiteto', 'description': 'Projeta'})
        self.text = {'statement': 'Descreva os objetivos.', 'response_type': 'TEXT', 'comment_mode': 'NONE'}
        self.choice = {**self.text, 'response_type': 'SINGLE_CHOICE', 'comment_mode': 'OPTIONAL',
                       'options': [{'label': 'Adequado', 'order_index': 9}, {'label': 'Rever', 'order_index': 2}]}

    def write(self, url, data, method='post', csrf=True):
        headers = {'HTTP_X_CSRFTOKEN': self.client.get('/api/auth/csrf/').json()['csrfToken']} if csrf else {}
        return getattr(self.client, method)(url, data, format='json', **headers)

    def question(self, data=None):
        response = self.write(self.path + 'questions/', data or self.text)
        self.assertEqual(response.status_code, 201, response.data)
        return response.json()

    def question_url(self, question):
        return self.path + f'questions/{question["id"]}/'

    def test_create_owner_origin_and_initial_version(self):
        response = self.write(BASE, self.payload)
        self.assertEqual(response.status_code, 201)
        item = Checklist.objects.get(pk=response.data['id'])
        self.assertEqual(item.owner_user, self.owner)
        self.assertEqual(item.origin, 'Fonte acadêmica')
        self.assertIsNone(item.derived_from_checklist_version)
        self.assertEqual(item.versions.get().version, '1.0')
        self.assertEqual(response.data['version_count'], 1)
        self.assertTrue(response.data['can_edit'])

    def test_initial_creation_is_atomic(self):
        before = (Checklist.objects.count(), ChecklistVersion.objects.count())
        with patch('apps.checklists.services.ChecklistVersion.objects.create', side_effect=IntegrityError('test')):
            with self.assertRaises(IntegrityError):
                services.create_checklist(user=self.owner, **self.payload)
        self.assertEqual((Checklist.objects.count(), ChecklistVersion.objects.count()), before)
        self.assertEqual(self.write(BASE, {**self.payload, 'initial_version': {'version': ''}}).status_code, 400)
        self.assertEqual((Checklist.objects.count(), ChecklistVersion.objects.count()), before)

    def test_reject_owner_and_derivation_injection(self):
        for key, value in [('owner_user', self.other.pk), ('owner_user_id', self.other.pk),
                           ('derived_from_checklist_version', self.version.pk), ('derived_from_checklist_version_id', self.version.pk)]:
            self.assertEqual(self.write(BASE, {**self.payload, key: value}).status_code, 400)
            self.assertEqual(self.write(self.url, {key: value}, 'patch').status_code, 400)

    def test_optional_origin_and_metadata(self):
        data = {key: value for key, value in self.payload.items() if key != 'origin'}
        self.assertEqual(self.write(BASE, data).data['origin'], '')
        self.assertEqual(self.write(self.url, {'name': 'Novo', 'origin': '', 'visibility': 'PUBLIC'}, 'patch').status_code, 200)
        self.checklist.refresh_from_db()
        self.assertEqual((self.checklist.name, self.checklist.origin, self.checklist.visibility), ('Novo', '', 'PUBLIC'))

    def test_duplicate_version_api_and_database(self):
        self.assertEqual(self.write(self.url + 'versions/', {'version': '1.0'}).status_code, 400)
        with self.assertRaises(IntegrityError), transaction.atomic():
            ChecklistVersion.objects.create(checklist=self.checklist, version='1.0')
        self.assertEqual(self.write(BASE, self.payload).status_code, 201)

    def test_new_version_empty_previous_unchanged(self):
        question = self.question(self.choice)
        before = self.client.get(self.question_url(question)).json()
        response = self.write(self.url + 'versions/', {'version': '2.0'})
        self.assertEqual(response.status_code, 201)
        new = ChecklistVersion.objects.get(pk=response.data['id'])
        self.assertFalse(new.questions.exists())
        self.assertFalse(new.sections.exists())
        self.assertFalse(new.stakeholders.exists())
        self.assertEqual(self.client.get(self.question_url(question)).json(), before)

    def test_list_only_owned_checklists(self):
        services.create_checklist(user=self.other, **{**self.payload, 'visibility': 'PUBLIC'})
        self.assertEqual([item['id'] for item in self.client.get(BASE).data], [self.checklist.pk])

    def test_sections_create_edit_and_insert_order(self):
        response = self.write(self.path + 'sections/', {'name': 'Primeira', 'order_index': 0})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['order_index'], 0)
        self.section.refresh_from_db()
        self.assertEqual(self.section.order_index, 1)
        url = self.path + f'sections/{response.data["id"]}/'
        self.assertEqual(self.write(url, {'name': 'Renomeada', 'order_index': 1}, 'patch').status_code, 200)
        self.assertEqual(list(self.version.sections.values_list('name', 'order_index')), [('Geral', 0), ('Renomeada', 1)])

    def test_stakeholders_create_edit(self):
        response = self.write(self.path + 'stakeholders/', {'name': 'Domínio', 'description': ''})
        self.assertEqual(response.status_code, 201)
        url = self.path + f'stakeholders/{response.data["id"]}/'
        self.assertEqual(self.write(url, {'name': 'Especialista', 'description': 'Conhece o domínio'}, 'patch').status_code, 200)
        self.assertEqual(StakeholderRole.objects.get(pk=response.data['id']).description, 'Conhece o domínio')

    def test_sections_reorder_exact_permutation(self):
        second = services.save_section(user=self.owner, version=self.version, data={'name': 'Outra'})
        response = self.write(self.path + 'sections/reorder/', {'ids': [second.pk, self.section.pk]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([(item['id'], item['order_index']) for item in response.data], [(second.pk, 0), (self.section.pk, 1)])
        before = list(self.version.sections.values())
        for ids in [[second.pk], [second.pk, second.pk], [second.pk, 999999]]:
            self.assertEqual(self.write(self.path + 'sections/reorder/', {'ids': ids}).status_code, 400)
            self.assertEqual(list(self.version.sections.values()), before)

    def test_text_without_sections_or_stakeholders(self):
        result = self.question()
        self.assertIsNone(result['section'])
        self.assertEqual(result['stakeholders'], [])
        self.assertEqual(result['options'], [])
        self.assertEqual(QuestionStakeholder.objects.count(), 0)

    def test_choice_options_sorted_and_normalized(self):
        result = self.question(self.choice)
        self.assertEqual([(option['label'], option['order_index']) for option in result['options']], [('Rever', 0), ('Adequado', 1)])
        self.assertEqual(ResponseOption.objects.count(), 2)

    def test_choice_requires_options(self):
        for options in [None, []]:
            data = {**self.text, 'response_type': 'SINGLE_CHOICE'}
            if options is not None:
                data['options'] = options
            self.assertEqual(self.write(self.path + 'questions/', data).status_code, 400)
        self.assertEqual(Question.objects.count(), 0)

    def test_text_rejects_nonempty_options(self):
        self.assertEqual(self.write(self.path + 'questions/', {**self.text, 'options': self.choice['options']}).status_code, 400)
        self.assertEqual(Question.objects.count(), 0)

    def test_complete_options_replacement_and_omitted_preservation(self):
        question = self.question(self.choice)
        before_ids = [option['id'] for option in question['options']]
        url = self.question_url(question)
        unchanged = self.write(url, {'statement': 'Novo enunciado'}, 'patch')
        self.assertEqual([option['id'] for option in unchanged.data['options']], before_ids)
        replacement = self.write(url, {'options': [{'label': 'Uma opção própria', 'order_index': 0}]}, 'patch')
        self.assertEqual(replacement.status_code, 200)
        self.assertEqual(len(replacement.data['options']), 1)
        self.assertFalse(ResponseOption.objects.filter(pk__in=before_ids).exists())

    def test_question_options_transaction_rollback(self):
        question = self.question(self.choice)
        before = self.client.get(self.question_url(question)).json()
        instance = Question.objects.get(pk=question['id'])
        with patch('apps.checklists.services.ResponseOption.objects.bulk_create', side_effect=IntegrityError('test')):
            with self.assertRaises(IntegrityError):
                services.save_question(user=self.owner, version=self.version, instance=instance,
                    data={'statement': 'Não persistir', 'options': [{'label': 'Nova', 'order_index': 0}]})
        self.assertEqual(self.client.get(self.question_url(question)).json(), before)

    def test_switch_choice_to_text_clears_options(self):
        question = self.question(self.choice)
        response = self.write(self.question_url(question), {'response_type': 'TEXT'}, 'patch')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['options'], [])
        self.assertFalse(ResponseOption.objects.exists())

    def test_switch_text_to_choice_requires_options(self):
        question = self.question()
        self.assertEqual(self.write(self.question_url(question), {'response_type': 'SINGLE_CHOICE'}, 'patch').status_code, 400)
        response = self.write(self.question_url(question), {'response_type': 'SINGLE_CHOICE', 'options': self.choice['options']}, 'patch')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['options']), 2)

    def test_comments_independent_of_response_type(self):
        for mode in ['NONE', 'OPTIONAL', 'REQUIRED']:
            for base in [self.text, self.choice]:
                with self.subTest(mode=mode, response_type=base['response_type']):
                    self.assertEqual(self.question({**base, 'comment_mode': mode})['comment_mode'], mode)

    def test_same_version_section_and_multiple_roles(self):
        second = services.save_stakeholder(user=self.owner, version=self.version, data={'name': 'Domínio'})
        question = self.question({**self.text, 'section_id': self.section.pk, 'stakeholder_ids': [self.role.pk, second.pk]})
        self.assertEqual(question['section']['id'], self.section.pk)
        self.assertEqual({role['id'] for role in question['stakeholders']}, {self.role.pk, second.pk})
        response = self.write(self.question_url(question), {'section_id': None, 'stakeholder_ids': []}, 'patch')
        self.assertIsNone(response.data['section'])
        self.assertEqual(response.data['stakeholders'], [])
        self.assertFalse(QuestionStakeholder.objects.exists())

    def test_cross_version_relations_rejected(self):
        for checklist in [self.checklist, services.create_checklist(user=self.owner, **self.payload)]:
            version = services.create_version(user=self.owner, checklist=checklist, version='x')
            section = services.save_section(user=self.owner, version=version, data={'name': 'Externa'})
            role = services.save_stakeholder(user=self.owner, version=version, data={'name': 'Externo'})
            for data in [{'section_id': section.pk}, {'stakeholder_ids': [role.pk]}, {'stakeholder_ids': [self.role.pk, role.pk]}]:
                self.assertEqual(self.write(self.path + 'questions/', {**self.text, **data}).status_code, 400)
                question = self.question()
                self.assertEqual(self.write(self.question_url(question), data, 'patch').status_code, 400)
        self.assertEqual(QuestionStakeholder.objects.count(), 0)

    def test_duplicate_role_rejected_and_db_constraint(self):
        self.assertEqual(self.write(self.path + 'questions/', {**self.text, 'stakeholder_ids': [self.role.pk] * 2}).status_code, 400)
        question = self.question({**self.text, 'stakeholder_ids': [self.role.pk]})
        with self.assertRaises(IntegrityError), transaction.atomic():
            QuestionStakeholder.objects.create(question_id=question['id'], stakeholder_role=self.role)

    def test_question_global_order_insert_patch_and_reorder(self):
        first = self.question()
        second = self.question({**self.text, 'section_id': self.section.pk, 'order_index': 0})
        self.assertEqual([item['id'] for item in self.client.get(self.path + 'questions/').data], [second['id'], first['id']])
        self.assertEqual(self.write(self.question_url(first), {'order_index': 0}, 'patch').status_code, 200)
        response = self.write(self.path + 'questions/reorder/', {'ids': [second['id'], first['id']]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['order_index'] for item in response.data], [0, 1])

    def test_reorder_rejects_other_version_ids(self):
        other = services.create_version(user=self.owner, checklist=self.checklist, version='2')
        section = services.save_section(user=self.owner, version=other, data={'name': 'Outra'})
        question = services.save_question(user=self.owner, version=other, data=self.text)
        self.assertEqual(self.write(self.path + 'sections/reorder/', {'ids': [section.pk]}).status_code, 400)
        own = self.question()
        self.assertEqual(self.write(self.path + 'questions/reorder/', {'ids': [own['id'], question.pk]}).status_code, 400)

    def test_invalid_options_and_partial_option_payload(self):
        question = self.question(self.choice)
        before = self.client.get(self.question_url(question)).json()
        for options in [[{'label': 'x'}], [{'order_index': 0}], [{'label': ' ', 'order_index': 0}],
                        [{'label': 'x', 'order_index': -1}], [{'label': 'x', 'order_index': 0}] * 2,
                        [{'id': question['options'][0]['id'], 'label': 'x', 'order_index': 0}]]:
            self.assertEqual(self.write(self.question_url(question), {'statement': 'Não persistir', 'options': options}, 'patch').status_code, 400)
            self.assertEqual(self.client.get(self.question_url(question)).json(), before)

    def test_invalid_enums_and_order(self):
        for data in [{'response_type': 'MULTIPLE_CHOICE'}, {'comment_mode': 'INVALID'}, {'statement': ' '}, {'order_index': -1}, {'order_index': 4}]:
            self.assertEqual(self.write(self.path + 'questions/', {**self.text, **data}).status_code, 400)
        self.assertEqual(self.write(BASE, {**self.payload, 'visibility': 'INVALID'}).status_code, 400)
        self.assertEqual(self.write(self.path + 'sections/', {'name': '', 'order_index': 0}).status_code, 400)

    def test_nested_url_scoping(self):
        foreign = services.create_checklist(user=self.owner, **self.payload)
        foreign_version = foreign.versions.get()
        question = self.question()
        self.assertEqual(self.client.get(self.url + f'versions/{foreign_version.pk}/').status_code, 404)
        for endpoint, pk in [('sections', self.section.pk), ('stakeholders', self.role.pk), ('questions', question['id'])]:
            wrong = self.url + f'versions/{foreign_version.pk}/{endpoint}/{pk}/'
            self.assertEqual(self.write(wrong, {'name': 'x'}, 'patch').status_code, 404)
        for key in ['checklist_version', 'checklist_version_id', 'checklist_id']:
            self.assertEqual(self.write(self.question_url(question), {key: foreign_version.pk}, 'patch').status_code, 400)

    def read_urls(self):
        question = self.question()
        return [BASE, self.url, self.url + 'versions/', self.path, self.path + 'sections/',
                self.path + 'stakeholders/', self.path + 'questions/', self.question_url(question)]

    def write_requests(self):
        question = self.question()
        return [(BASE, self.payload, 'post'), (self.url, {'name': 'Alterado'}, 'patch'),
                (self.url + 'versions/', {'version': '2'}, 'post'),
                (self.path + 'sections/', {'name': 'x'}, 'post'),
                (self.path + f'sections/{self.section.pk}/', {'name': 'x'}, 'patch'),
                (self.path + 'stakeholders/', {'name': 'x'}, 'post'),
                (self.path + f'stakeholders/{self.role.pk}/', {'name': 'x'}, 'patch'),
                (self.path + 'questions/', self.text, 'post'), (self.question_url(question), {'statement': 'x'}, 'patch'),
                (self.path + 'sections/reorder/', {'ids': [self.section.pk]}, 'post'),
                (self.path + 'questions/reorder/', {'ids': [question['id']]}, 'post')]

    def test_anonymous_access_denied(self):
        urls = self.read_urls()
        requests = self.write_requests()
        self.client.logout()
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 403)
        for url, data, method in requests:
            self.assertEqual(self.write(url, data, method).status_code, 403)

    def test_private_direct_and_indirect_access_blocked(self):
        urls = self.read_urls()[1:]
        requests = self.write_requests()[1:]
        self.client.force_login(self.other)
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 404)
        for url, data, method in requests:
            self.assertEqual(self.write(url, data, method).status_code, 404)
        self.assertEqual(self.client.get(BASE).data, [])

    def test_public_read_only_all_structures(self):
        urls = self.read_urls()[1:]
        requests = self.write_requests()[1:]
        self.checklist.visibility = 'PUBLIC'
        self.checklist.save()
        self.client.force_login(self.other)
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 200)
        self.assertFalse(self.client.get(self.url).data['can_edit'])
        for url, data, method in requests:
            self.assertEqual(self.write(url, data, method).status_code, 403)
        self.assertEqual(self.client.get(BASE).data, [])

    def test_all_mutations_require_csrf(self):
        requests = self.write_requests()
        for url, data, method in requests:
            self.assertEqual(self.write(url, data, method, csrf=False).status_code, 403)
            self.assertEqual(getattr(self.client, method)(url, data, format='json', HTTP_X_CSRFTOKEN='invalid').status_code, 403)

    def test_services_enforce_ownership(self):
        for operation in [
            lambda: services.create_version(user=self.other, checklist=self.checklist, version='2'),
            lambda: services.update_checklist(user=self.other, checklist=self.checklist, data={'name': 'x'}),
            lambda: services.save_section(user=self.other, version=self.version, data={'name': 'x'}),
            lambda: services.save_stakeholder(user=self.other, version=self.version, data={'name': 'x'}),
            lambda: services.save_question(user=self.other, version=self.version, data=self.text),
            lambda: services.reorder(user=self.other, version=self.version, model=Question, ids=[]),
        ]:
            with self.assertRaisesMessage(PermissionDenied, 'Somente o proprietário'):
                operation()

    def test_no_deletes_or_version_edits(self):
        question = self.question()
        for url in [self.url, self.path, self.path + f'sections/{self.section.pk}/', self.path + f'stakeholders/{self.role.pk}/', self.question_url(question)]:
            self.assertEqual(self.write(url, {}, 'delete').status_code, 405)
        self.assertEqual(self.write(self.path, {'version': 'x'}, 'patch').status_code, 405)
