from django.test import TestCase
from rest_framework.exceptions import PermissionDenied, ValidationError
from apps.checklists import services as checklist_services
from apps.reference_architectures import services as ra_services
from . import services
from .models import Answer, ChecklistEvaluation
from .permissions import available_questions
from .test_answers import AnswerFixture


class ReportingFixture(AnswerFixture):
    def begin_reporting(self):
        services.save_participant(user=self.owner, evaluation=self.evaluation, participant=self.participation,
                                  stakeholder_role_ids=[self.role.pk, self.role2.pk])
        services.start_evaluation(user=self.owner, evaluation=self.evaluation)

    def report(self):
        return self.client.get(self.url + 'progress/')

    def complete(self, confirm=False):
        return self.write(self.url + 'complete/', {'confirm_incomplete': confirm})

    def results(self):
        return self.client.get(self.url + 'results/')

    def save(self, question, *, user=None, **data):
        return services.save_answer(user=user or self.reader, evaluation_id=self.evaluation.pk,
                                    question_id=question.pk, data=data)

    def finish(self):
        return services.complete_evaluation(user=self.owner, evaluation=self.evaluation, confirm_incomplete=True)

    def fill_all(self):
        for participant in self.evaluation.participants.select_related('user', 'checklist_evaluation'):
            for question in available_questions(participant):
                self.save(question, user=participant.user, **(
                    {'response_option_id': question.options.first().pk, 'comment': 'Justificativa'}
                    if question.response_type == 'SINGLE_CHOICE' else
                    {'text_value': 'Texto persistido', 'comment': 'Comentário' if question.comment_mode != 'NONE' else ''}))


class ProgressTests(ReportingFixture, TestCase):
    def setUp(self):
        super().setUp()
        self.begin_reporting()

    def test_no_roles_common_only_and_multiple_roles_union(self):
        response = self.report()
        self.assertEqual(response.status_code, 200)
        rows = {row['id']: row for row in response.data['participants']}
        self.assertEqual(rows[self.other_participation.pk]['total'], 1)
        self.assertEqual(rows[self.other_participation.pk]['pending_questions'], [{'id': self.common.pk, 'statement': self.common.statement}])
        own = rows[self.participation.pk]
        self.assertEqual((own['total'], own['answered'], own['pending'], own['percentage']), (5, 0, 5, 0))
        self.assertEqual(len({row['id'] for row in own['pending_questions']}), 5)
        self.assertEqual(len(own['stakeholder_roles']), 2)
        self.assertEqual(response.data['totals'], {'participants': 2, 'expected': 6, 'answered': 0, 'pending': 6,
                                                  'percentage': 0, 'participants_with_pending': 2})

    def test_general_denominator_counts_each_assignment_and_upsert_only_once(self):
        self.save(self.common, text_value='Resposta A')
        self.save(self.common, user=self.other, text_value='Resposta B')
        self.save(self.common, text_value='Resposta A revisada')
        response = self.report().data
        self.assertEqual(response['totals']['answered'], 2)
        self.assertEqual(response['totals']['expected'], 6)
        self.assertEqual(response['totals']['pending'], 4)
        self.assertEqual(response['totals']['percentage'], 33.33)
        self.assertEqual(response['totals']['participants_with_pending'], 1)
        self.assertEqual(response['participants'][0]['percentage'], 20)
        self.assertEqual(response['participants'][1]['percentage'], 100)
        self.assertEqual(Answer.objects.count(), 2)

    def test_progress_has_no_response_values_or_comments(self):
        self.save(self.text, text_value='Texto secreto', comment='Comentário secreto')
        response = self.report()
        self.assertEqual(response.data['totals']['answered'], 1)
        self.assertNotIn('Texto secreto', str(response.data))
        self.assertNotIn('Comentário secreto', str(response.data))
        self.assertNotIn('email', str(response.data))

    def test_query_count_does_not_grow_with_participants(self):
        from django.test.utils import CaptureQueriesContext
        from django.db import connection
        from django.contrib.auth import get_user_model
        with CaptureQueriesContext(connection) as first:
            services.evaluation_progress(user=self.owner, evaluation=self.evaluation)
        for index in range(5):
            user = get_user_model().objects.create_user(email=f'bulk{index}@test.example', name=f'Pessoa {index}')
            self.evaluation.participants.create(user=user)
        with CaptureQueriesContext(connection) as second:
            services.evaluation_progress(user=self.owner, evaluation=self.evaluation)
        self.assertEqual(len(first), len(second))

    def test_bulk_assignment_matches_existing_workspace_selection(self):
        from .reporting import snapshot
        progress, questions, assignments, _ = snapshot(self.evaluation)
        for participant in self.evaluation.participants.all():
            self.assertEqual([q.pk for q in assignments[participant.pk]], list(available_questions(participant).values_list('pk', flat=True)))
        self.assertEqual(progress['totals']['expected'], 6)

    def test_progress_creator_only_draft_rejected_completed_allowed(self):
        for user, status in [(self.reader, 403), (self.other, 403)]:
            self.client.force_login(user)
            self.assertEqual(self.report().status_code, status)
        outsider = type(self.owner).objects.create_user(email='unrelated@test.example', name='Sem acesso')
        self.client.force_login(outsider)
        self.assertEqual(self.report().status_code, 404)
        self.client.force_login(self.owner)
        draft = services.create_evaluation(user=self.owner, ra_version_id=self.ra_version.pk, checklist_version_id=self.version.pk)
        self.assertEqual(self.client.get(f'/api/checklist-evaluations/{draft.pk}/progress/').status_code, 400)
        self.finish()
        self.assertEqual(self.report().status_code, 200)


class ZeroAssignmentTests(ReportingFixture, TestCase):
    def setUp(self):
        super().setUp()
        self.common.stakeholders.add(self.unassigned_role)
        services.save_participant(user=self.owner, evaluation=self.evaluation, participant=self.participation, stakeholder_role_ids=[])
        services.start_evaluation(user=self.owner, evaluation=self.evaluation)

    def test_zero_denominator_is_not_applicable_and_not_pending(self):
        data = self.report().data
        self.assertEqual(data['totals']['expected'], 0)
        self.assertIsNone(data['totals']['percentage'])
        self.assertEqual(data['totals']['pending'], 0)
        self.assertEqual(data['totals']['participants_with_pending'], 0)
        for row in data['participants']:
            self.assertIsNone(row['percentage'])
            self.assertEqual((row['total'], row['answered'], row['pending'], row['pending_questions']), (0, 0, 0, []))
        self.assertEqual(self.complete().status_code, 200)
        self.assertEqual(Answer.objects.count(), 0)
        self.assertTrue(all(q['expected'] == 0 for q in self.results().data['questions']))


class CompletionTests(ReportingFixture, TestCase):
    def setUp(self):
        super().setUp()
        self.begin_reporting()

    def test_complete_without_pending_accepts_empty_payload(self):
        self.fill_all()
        result = self.write(self.url + 'complete/')
        self.assertEqual(result.status_code, 200, result.data)
        self.assertEqual(result.data, {'id': self.evaluation.pk, 'status': 'COMPLETED'})
        self.assertEqual(self.report().data['totals']['pending'], 0)

    def test_incomplete_requires_confirmation_with_counts_and_no_partial_transition(self):
        result = self.complete()
        self.assertEqual(result.status_code, 400)
        self.assertEqual(int(str(result.data['pending'])), 6)
        self.assertEqual(int(str(result.data['participants_with_pending'])), 2)
        self.evaluation.refresh_from_db()
        self.assertEqual(self.evaluation.status, 'IN_PROGRESS')
        self.assertEqual(self.complete(True).status_code, 200)
        self.assertEqual(Answer.objects.count(), 0)

    def test_completion_preserves_actual_answers_and_creates_none_for_missing(self):
        answer = self.save(self.common, text_value='Manter exatamente')
        before = list(Answer.objects.values())
        self.assertEqual(self.complete(True).status_code, 200)
        self.assertEqual(list(Answer.objects.values()), before)
        self.assertEqual(Answer.objects.get().pk, answer.pk)
        self.assertEqual(self.results().data['totals']['pending'], 5)

    def test_cannot_complete_draft_or_complete_twice(self):
        draft = services.create_evaluation(user=self.owner, ra_version_id=self.ra_version.pk, checklist_version_id=self.version.pk)
        self.assertEqual(self.write(f'/api/checklist-evaluations/{draft.pk}/complete/', {'confirm_incomplete': True}).status_code, 400)
        self.finish()
        self.assertEqual(self.complete(True).status_code, 400)
        self.evaluation.refresh_from_db()
        self.assertEqual(self.evaluation.status, 'COMPLETED')

    def test_participants_and_outsiders_cannot_complete(self):
        self.client.force_login(self.reader)
        self.assertEqual(self.complete(True).status_code, 403)
        with self.assertRaises(PermissionDenied):
            services.complete_evaluation(user=self.reader, evaluation=self.evaluation, confirm_incomplete=True)
        outsider = type(self.owner).objects.create_user(email='outside@test.example', name='Externo')
        self.client.force_login(outsider)
        self.assertEqual(self.complete(True).status_code, 404)

    def test_csrf_and_strict_completion_payload(self):
        self.assertEqual(self.write(self.url + 'complete/', {'confirm_incomplete': True}, csrf=False).status_code, 403)
        for payload in [{'status': 'COMPLETED'}, {'confirm_incomplete': 'invalid'}, {'confirm_incomplete': None}]:
            self.assertEqual(self.write(self.url + 'complete/', payload).status_code, 400)

    def test_completed_answers_and_all_configuration_remain_immutable(self):
        self.save(self.common, text_value='Original')
        self.finish()
        self.client.force_login(self.reader)
        for question in [self.common, self.multiple]:
            self.assertEqual(self.write(self.answer_url(question), {'text_value': 'Não salvar'}, 'put').status_code, 400)
        self.assertEqual(self.client.get(self.questions_url).status_code, 400)
        self.client.force_login(self.owner)
        self.assertEqual(self.write(self.url, {'ra_version_id': self.ra_version.pk}, 'patch').status_code, 400)
        self.assertEqual(self.write(self.url + f'participants/{self.participation.pk}/', {'stakeholder_role_ids': []}, 'patch').status_code, 400)
        self.assertEqual(self.write(self.url + f'participants/{self.participation.pk}/', method='delete').status_code, 400)
        self.assertEqual(self.add(email=self.owner.email).status_code, 400)
        self.assertEqual(Answer.objects.get().text_value, 'Original')
        with self.assertRaises(ValidationError):
            ra_services.update_element(user=self.owner, element=self.element, data={'name': 'Não editar'})
        with self.assertRaises(ValidationError):
            checklist_services.save_question(user=self.owner, version=self.version, instance=self.question,
                data={'options': [{'label': 'Não trocar IDs', 'order_index': 0}]})


class ResultsTests(ReportingFixture, TestCase):
    def setUp(self):
        super().setUp()
        # Arbitrary configured labels, including an unchosen option.
        self.second_option = self.question.options.create(label='Outra escolha', order_index=1)
        self.third_option = self.question.options.create(label='Nunca escolhida', order_index=2)
        services.save_participant(user=self.owner, evaluation=self.evaluation, participant=self.other_participation,
                                  stakeholder_role_ids=[self.role.pk])
        self.begin_reporting()

    def question_result(self, question):
        return next(q for q in self.results().data['questions'] if q['id'] == question.pk)

    def test_distribution_denominator_and_zero_option_counts(self):
        self.save(self.question, response_option_id=self.question.options.first().pk, comment='Justificativa A')
        self.save(self.question, user=self.other, response_option_id=self.second_option.pk, comment='Justificativa B')
        self.finish()
        q = self.question_result(self.question)
        self.assertEqual((q['expected'], q['answered'], q['pending']), (2, 2, 0))
        self.assertEqual([(o['label'], o['count'], o['percentage']) for o in q['distribution']],
                         [('Alternativa própria', 1, 50), ('Outra escolha', 1, 50), ('Nunca escolhida', 0, 0)])
        self.assertEqual([r['answer']['comment'] for r in q['responses']], ['Justificativa A', 'Justificativa B'])

    def test_percentages_exclude_missing_answers(self):
        self.save(self.question, response_option_id=self.second_option.pk, comment='Uma resposta')
        self.finish()
        q = self.question_result(self.question)
        self.assertEqual((q['answered'], q['pending']), (1, 1))
        self.assertEqual(q['distribution'][1]['percentage'], 100)
        self.assertIsNone(q['responses'][1]['answer'])

    def test_no_answers_no_division_by_zero(self):
        self.finish()
        q = self.question_result(self.question)
        self.assertEqual(q['answered'], 0)
        self.assertTrue(all(o['count'] == 0 and o['percentage'] is None for o in q['distribution']))

    def test_text_comments_and_common_individual_responses(self):
        self.save(self.common, text_value='Resposta do participante')
        self.save(self.common, user=self.other, text_value='Resposta diferente')
        self.save(self.text, text_value='Valor principal', comment='Comentário adicional')
        self.finish()
        common = self.question_result(self.common)
        self.assertEqual([r['answer']['text_value'] for r in common['responses']], ['Resposta do participante', 'Resposta diferente'])
        q = self.question_result(self.text)
        self.assertEqual(q['responses'][0]['answer']['text_value'], 'Valor principal')
        self.assertEqual(q['responses'][0]['answer']['comment'], 'Comentário adicional')
        self.assertEqual(q['distribution'], [])
        self.assertEqual(q['section'], {'id': self.section.pk, 'name': self.section.name})

    def test_unassigned_not_pending_and_multiple_roles_not_duplicated(self):
        self.save(self.multiple, text_value='Uma única resposta')
        self.finish()
        q = self.question_result(self.restricted)
        self.assertEqual(q['expected'], 1)
        self.assertEqual(q['responses'], [{'participant_id': self.participation.pk, 'answer': None}])
        q = self.question_result(self.multiple)
        self.assertEqual((q['expected'], q['answered'], q['pending']), (2, 1, 1))
        self.assertEqual(len({r['participant_id'] for r in q['responses']}), 2)
        hidden = self.question_result(self.hidden)
        self.assertEqual((hidden['expected'], hidden['pending'], hidden['responses']), (0, 0, []))
        self.assertNotIn(self.foreign.pk, [q['id'] for q in self.results().data['questions']])

    def test_results_only_completed_and_creator_only(self):
        self.assertEqual(self.results().status_code, 400)
        draft = services.create_evaluation(user=self.owner, ra_version_id=self.ra_version.pk, checklist_version_id=self.version.pk)
        self.assertEqual(self.client.get(f'/api/checklist-evaluations/{draft.pk}/results/').status_code, 400)
        self.finish()
        self.assertEqual(self.results().status_code, 200)
        for user in [self.reader, self.other]:
            self.client.force_login(user)
            self.assertEqual(self.results().status_code, 403)
        outsider = type(self.owner).objects.create_user(email='outside@test.example', name='Externo')
        self.client.force_login(outsider)
        self.assertEqual(self.results().status_code, 404)
        self.assertEqual(self.report().status_code, 404)
        self.client.logout()
        self.assertEqual(self.results().status_code, 403)

    def test_other_evaluation_answers_never_included(self):
        second = services.create_evaluation(user=self.owner, ra_version_id=self.ra_version.pk, checklist_version_id=self.version.pk)
        services.save_participant(user=self.owner, evaluation=second, email=self.reader.email, stakeholder_role_ids=[])
        services.start_evaluation(user=self.owner, evaluation=second)
        services.save_answer(user=self.reader, evaluation_id=second.pk, question_id=self.common.pk, data={'text_value': 'Não vazar outra avaliação'})
        self.save(self.common, text_value='Apenas desta avaliação')
        self.finish()
        result = self.results()
        self.assertNotIn('Não vazar outra avaliação', str(result.data))
        self.assertEqual(result.data['totals']['answered'], 1)
        self.assertEqual(result.data['ra_version']['id'], self.ra_version.pk)
        self.assertEqual(result.data['checklist_version']['id'], self.version.pk)
