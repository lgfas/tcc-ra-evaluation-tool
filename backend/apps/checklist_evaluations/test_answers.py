from django.core.exceptions import ValidationError as ModelValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from apps.checklists import services as checklist_services
from apps.checklists.models import Question
from .tests import EvaluationFixture
from .models import Answer, ChecklistEvaluation
from . import services


class AnswerFixture(EvaluationFixture):
    def setUp(self):
        super().setUp()
        self.common = self.question_for('Comum', 'TEXT', 'NONE')
        self.text = self.question_for('Texto com comentário', 'TEXT', 'REQUIRED', [self.role.pk])
        self.multiple = self.question_for('Dois papéis', 'TEXT', 'OPTIONAL', [self.role.pk, self.role2.pk])
        self.restricted = self.question_for('Especialista', 'TEXT', 'NONE', [self.role2.pk])
        self.unassigned_role = checklist_services.save_stakeholder(user=self.owner, version=self.version, data={'name': 'Outro papel'})
        self.hidden = self.question_for('Oculta', 'TEXT', 'NONE', [self.unassigned_role.pk])
        other_version = checklist_services.create_version(user=self.owner, checklist=self.checklist, version='2')
        self.foreign = checklist_services.save_question(user=self.owner, version=other_version,
            data={'statement': 'Outra versão', 'response_type': 'SINGLE_CHOICE', 'comment_mode': 'NONE',
                  'options': [{'label': 'Não usar', 'order_index': 0}]})
        self.participation = self.participant()
        self.other_participation = services.save_participant(user=self.owner, evaluation=self.evaluation,
            email=self.other.email, stakeholder_role_ids=[])
        self.questions_url = self.url + 'my-questions/'

    def question_for(self, statement, response_type, comment_mode, roles=None):
        data = {'statement': statement, 'response_type': response_type, 'comment_mode': comment_mode,
                'stakeholder_ids': roles or [], 'section_id': self.section.pk}
        if response_type == 'SINGLE_CHOICE':
            data['options'] = [{'label': 'Alternativa', 'order_index': 0}]
        return checklist_services.save_question(user=self.owner, version=self.version, data=data)

    def begin(self):
        services.start_evaluation(user=self.owner, evaluation=self.evaluation)
        self.client.force_login(self.reader)

    def answer_url(self, question):
        return self.url + f'my-answers/{question.pk}/'

    def put(self, question, data, csrf=True):
        return self.write(self.answer_url(question), data, 'put', csrf=csrf)


class AnswerTests(AnswerFixture, TestCase):
    def question_ids(self):
        response = self.client.get(self.questions_url)
        self.assertEqual(response.status_code, 200, response.data)
        return [question['id'] for question in response.data['questions']]

    def test_no_roles_only_common_questions(self):
        services.save_participant(user=self.owner, evaluation=self.evaluation, participant=self.participation, stakeholder_role_ids=[])
        self.begin()
        self.assertEqual(self.question_ids(), [self.common.pk])

    def test_one_role_and_common_order_and_section(self):
        self.begin()
        self.assertEqual(self.question_ids(), [self.question.pk, self.common.pk, self.text.pk, self.multiple.pk])
        data = self.client.get(self.questions_url).data
        self.assertEqual(data['questions'][0]['section'], {'id': self.section.pk, 'name': 'Geral', 'order_index': 0})
        self.assertEqual(data['questions'][0]['options'][0]['id'], self.question.options.get().pk)
        self.assertEqual(data['progress'], {'answered': 0, 'total': 4})
        self.assertTrue(all(question['answer'] is None for question in data['questions']))

    def test_multiple_roles_union_without_duplicate_or_foreign_questions(self):
        services.save_participant(user=self.owner, evaluation=self.evaluation, participant=self.participation, stakeholder_role_ids=[self.role.pk, self.role2.pk])
        self.begin()
        ids = self.question_ids()
        self.assertEqual(ids, [self.question.pk, self.common.pk, self.text.pk, self.multiple.pk, self.restricted.pk])
        self.assertEqual(ids.count(self.multiple.pk), 1)
        self.assertNotIn(self.hidden.pk, ids)
        self.assertNotIn(self.foreign.pk, ids)

    def test_single_choice_save_and_recovery(self):
        self.begin()
        payload = {'response_option_id': self.question.options.get().pk, 'comment': 'Justificativa'}
        response = self.put(self.question, payload)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['response_option_id'], payload['response_option_id'])
        saved = Answer.objects.get()
        self.assertEqual(saved.evaluation_participant, self.participation)
        self.assertEqual(saved.question, self.question)
        data = self.client.get(self.questions_url).data
        self.assertEqual(data['questions'][0]['answer'], response.data)
        self.assertEqual(data['progress'], {'answered': 1, 'total': 4})

    def test_choice_rejects_other_question_version_missing_and_text(self):
        other_choice = self.question_for('Outra seleção', 'SINGLE_CHOICE', 'OPTIONAL')
        self.begin()
        for payload in [
            {'response_option_id': other_choice.options.get().pk}, {'response_option_id': self.foreign.options.get().pk},
            {}, {'response_option_id': None}, {'response_option_id': 999999},
            {'response_option_id': self.question.options.get().pk, 'text_value': 'Não permitido'},
        ]:
            self.assertEqual(self.put(self.question, {**payload, 'comment': 'Obrigatório'}).status_code, 400)
        self.assertFalse(Answer.objects.exists())

    def test_text_save_preserves_content(self):
        self.begin()
        response = self.put(self.common, {'text_value': '  Resposta\n<script>texto</script>  '})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['text_value'], '  Resposta\n<script>texto</script>  ')
        self.assertIsNone(response.data['response_option_id'])

    def test_text_rejects_blank_and_choice(self):
        self.begin()
        for data in [{}, {'text_value': ''}, {'text_value': ' \n '}, {'text_value': 'Válido', 'response_option_id': self.question.options.get().pk}]:
            self.assertEqual(self.put(self.common, data).status_code, 400)
        self.assertFalse(Answer.objects.exists())

    def test_update_does_not_duplicate_and_invalid_update_preserves_saved(self):
        self.begin()
        first = self.put(self.common, {'text_value': 'Primeira'}).data
        second = self.put(self.common, {'text_value': 'Segunda'}).data
        self.assertEqual(first['id'], second['id'])
        self.assertEqual(Answer.objects.count(), 1)
        self.assertEqual(self.put(self.common, {'text_value': ''}).status_code, 400)
        self.assertEqual(Answer.objects.get().text_value, 'Segunda')
        self.assertEqual(self.client.get(self.questions_url).data['progress']['answered'], 1)

    def test_database_unique_participant_question(self):
        self.begin()
        self.put(self.common, {'text_value': 'Salva'})
        with self.assertRaises(IntegrityError), transaction.atomic():
            Answer.objects.create(evaluation_participant=self.participation, question=self.common, text_value='Duplicada')

    def test_database_rejects_empty_or_dual_primary_value(self):
        for text, option in [('', None), ('  \n', None), ('Texto', self.question.options.get())]:
            with self.subTest(text=text), self.assertRaises(IntegrityError), transaction.atomic():
                Answer.objects.create(evaluation_participant=self.participation, question=self.common, text_value=text, response_option=option)

    def test_none_rejects_nonempty_comment_both_types(self):
        choice = self.question_for('Sem comentário', 'SINGLE_CHOICE', 'NONE')
        self.begin()
        for question, value in [(self.common, {'text_value': 'Texto'}), (choice, {'response_option_id': choice.options.get().pk})]:
            for comment in ['Indevido', ' ']:
                self.assertEqual(self.put(question, {**value, 'comment': comment}).status_code, 400)
            self.assertEqual(self.put(question, {**value, 'comment': ''}).status_code, 200)

    def test_optional_comments_both_types(self):
        choice = self.question_for('Opcional', 'SINGLE_CHOICE', 'OPTIONAL')
        self.begin()
        for question, value in [(self.multiple, {'text_value': 'Texto'}), (choice, {'response_option_id': choice.options.get().pk})]:
            for comment in ['', 'Comentário']:
                response = self.put(question, {**value, 'comment': comment})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data['comment'], comment)

    def test_required_comments_both_types(self):
        self.begin()
        for question, value in [(self.text, {'text_value': 'Texto'}), (self.question, {'response_option_id': self.question.options.get().pk})]:
            for comment in ['', ' \n ']:
                self.assertEqual(self.put(question, {**value, 'comment': comment}).status_code, 400)
            self.assertEqual(self.put(question, {**value, 'comment': 'Justificativa'}).status_code, 200)

    def test_external_and_creator_nonparticipant_cannot_answer_or_read(self):
        self.begin()
        from django.contrib.auth import get_user_model
        outsider = get_user_model().objects.create_user(email='outsider@answer.test', name='Externo')
        for user in [self.owner, outsider]:
            self.client.force_login(user)
            self.assertEqual(self.client.get(self.questions_url).status_code, 404)
            self.assertEqual(self.put(self.common, {'text_value': 'Não'}).status_code, 404)

    def test_creator_can_answer_if_explicit_participant(self):
        services.save_participant(user=self.owner, evaluation=self.evaluation, email=self.owner.email, stakeholder_role_ids=[])
        self.begin()
        self.client.force_login(self.owner)
        self.assertEqual(self.put(self.common, {'text_value': 'Criador participante'}).status_code, 200)

    def test_own_answers_only_and_identity_injection_rejected(self):
        self.begin()
        response = self.put(self.common, {'text_value': 'Resposta privada A'})
        self.client.force_login(self.other)
        data = self.client.get(self.questions_url).data
        self.assertEqual(data['progress'], {'answered': 0, 'total': 1})
        self.assertIsNone(data['questions'][0]['answer'])
        self.assertNotIn('Resposta privada A', str(data))
        for field in ['evaluation_participant', 'evaluation_participant_id', 'question_id', 'question', 'id', 'checklist_evaluation_id', 'user_id']:
            self.assertEqual(self.put(self.common, {'text_value': 'Inválida', field: self.participation.pk}).status_code, 400)
        own = self.put(self.common, {'text_value': 'Resposta privada B'})
        self.assertEqual(own.status_code, 200)
        self.assertNotEqual(response.data['id'], own.data['id'])
        self.assertNotIn('Resposta privada A', str(self.client.get(self.questions_url).data))
        self.assertEqual(Answer.objects.filter(evaluation_participant=self.participation).get().text_value, 'Resposta privada A')

    def test_private_artifacts_remain_private(self):
        self.begin()
        self.assertEqual(self.client.get(self.questions_url).status_code, 200)
        self.assertEqual(self.put(self.common, {'text_value': 'Autorizada'}).status_code, 200)
        for url in [f'/api/checklists/{self.checklist.pk}/', f'/api/reference-architectures/{self.ra.pk}/']:
            self.assertEqual(self.client.get(url).status_code, 404)
        result = str(self.client.get(self.questions_url).data)
        for private in ['Descrição privada', self.owner.email, self.other.email, self.hidden.statement]:
            self.assertNotIn(private, result)

    def test_draft_and_completed_reject_reads_and_writes(self):
        self.client.force_login(self.reader)
        self.assertEqual(self.client.get(self.questions_url).status_code, 400)
        self.assertEqual(self.put(self.common, {'text_value': 'DRAFT'}).status_code, 400)
        self.begin()
        self.put(self.common, {'text_value': 'Preservada'})
        ChecklistEvaluation.objects.filter(pk=self.evaluation.pk).update(status='COMPLETED')
        self.assertEqual(self.client.get(self.questions_url).status_code, 400)
        self.assertEqual(self.put(self.common, {'text_value': 'COMPLETED'}).status_code, 400)
        self.assertEqual(Answer.objects.get().text_value, 'Preservada')

    def test_unavailable_question_and_mismatched_ids(self):
        other_evaluation = services.create_evaluation(user=self.owner, ra_version_id=self.ra_version.pk, checklist_version_id=self.version.pk)
        self.begin()
        for question in [self.hidden, self.restricted, self.foreign]:
            self.assertEqual(self.put(question, {'text_value': 'Não'}).status_code, 404)
        self.assertEqual(self.write(self.url + 'my-answers/999999/', {'text_value': 'Não'}, 'put').status_code, 404)
        self.assertEqual(self.write(f'/api/checklist-evaluations/{other_evaluation.pk}/my-answers/{self.common.pk}/', {'text_value': 'Não'}, 'put').status_code, 404)
        self.assertFalse(Answer.objects.exists())

    def test_anonymous_and_csrf(self):
        self.begin()
        self.assertEqual(self.put(self.common, {'text_value': 'x'}, csrf=False).status_code, 403)
        self.assertEqual(self.client.put(self.answer_url(self.common), {'text_value': 'x'}, format='json', HTTP_X_CSRFTOKEN='invalid').status_code, 403)
        token = self.client.get('/api/auth/csrf/').json()['csrfToken']
        self.assertEqual(self.client.put(self.answer_url(self.common), {'text_value': 'x'}, format='json', HTTP_X_CSRFTOKEN=token, HTTP_ORIGIN='https://untrusted.example').status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(self.questions_url).status_code, 403)
        self.assertEqual(self.put(self.common, {'text_value': 'x'}).status_code, 403)
        self.assertFalse(Answer.objects.exists())

    def test_no_available_questions(self):
        self.common.delete()
        services.save_participant(user=self.owner, evaluation=self.evaluation, participant=self.participation, stakeholder_role_ids=[])
        self.begin()
        result = self.client.get(self.questions_url).data
        self.assertEqual(result['questions'], [])
        self.assertEqual(result['progress'], {'answered': 0, 'total': 0})

    def test_list_query_count_is_independent_of_question_count(self):
        for index in range(10):
            self.question_for(f'Comum {index}', 'TEXT', 'NONE')
        self.begin()
        with self.assertNumQueries(7):
            response = self.client.get(self.questions_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['questions']), 14)

    def test_model_validation_rejects_question_from_other_version(self):
        answer = Answer(evaluation_participant=self.participation, question=self.foreign, response_option=self.foreign.options.get())
        with self.assertRaises(ModelValidationError):
            answer.full_clean()
