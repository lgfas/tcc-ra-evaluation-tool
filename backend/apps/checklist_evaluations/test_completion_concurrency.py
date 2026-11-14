from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from threading import Event
from time import monotonic, sleep
from django.db import close_old_connections, connection, transaction
from django.test import TransactionTestCase
from rest_framework.exceptions import ValidationError
from . import services
from .models import Answer, ChecklistEvaluation
from .test_results import ReportingFixture


class CompletionConcurrencyTests(ReportingFixture, TransactionTestCase):
    """Independent PostgreSQL sessions; assert the waiter really waits for a lock."""
    def setUp(self):
        super().setUp()
        self.begin_reporting()
        self.fill_all()

    def worker(self, action):
        close_old_connections()
        try:
            return action()
        finally:
            connection.close()

    def contend(self, first, second):
        held, release = Event(), Event()
        pids = Queue()
        def hold():
            with transaction.atomic():
                result = first()
                held.set()
                if not release.wait(10):
                    raise RuntimeError('Timeout liberando a transação.')
                return result
        def wait():
            with connection.cursor() as cursor:
                cursor.execute('SELECT pg_backend_pid()')
                pids.put(cursor.fetchone()[0])
            return second()
        with ThreadPoolExecutor(max_workers=2) as executor:
            holder = executor.submit(self.worker, hold)
            try:
                self.assertTrue(held.wait(5))
                waiter = executor.submit(self.worker, wait)
                pid = pids.get(timeout=5)
                deadline = monotonic() + 5
                blocked = False
                while monotonic() < deadline:
                    with connection.cursor() as cursor:
                        cursor.execute('SELECT wait_event_type FROM pg_stat_activity WHERE pid = %s', [pid])
                        row = cursor.fetchone()
                    if row and row[0] == 'Lock':
                        blocked = True
                        break
                    sleep(0.02)
                self.assertTrue(blocked, 'A operação não aguardou o bloqueio da avaliação.')
            finally:
                release.set()
            holder.result(timeout=10)
            return waiter.result(timeout=10)

    def test_answer_commits_first_completion_recalculates_instead_of_rejecting(self):
        Answer.objects.filter(evaluation_participant=self.participation, question=self.common).delete()
        self.assertEqual(services.evaluation_progress(user=self.owner, evaluation=self.evaluation)['totals']['pending'], 1)
        result = self.contend(lambda: self.save(self.common, text_value='Última resposta confirmada'),
            lambda: services.complete_evaluation(user=self.owner, evaluation=self.evaluation))
        self.assertEqual(result.status, 'COMPLETED')
        totals = services.evaluation_results(user=self.owner, evaluation=self.evaluation)['totals']
        self.assertEqual((totals['answered'], totals['pending']), (6, 0))

    def test_completion_first_rejects_waiting_edit_without_changing_answer(self):
        before = Answer.objects.get(evaluation_participant=self.participation, question=self.common).text_value
        def save_after():
            try:
                self.save(self.common, text_value='Não persistir depois de COMPLETED')
            except ValidationError:
                return 'rejected'
            return 'saved'
        result = self.contend(lambda: services.complete_evaluation(user=self.owner, evaluation=self.evaluation), save_after)
        self.assertEqual(result, 'rejected')
        self.assertEqual(Answer.objects.get(evaluation_participant=self.participation, question=self.common).text_value, before)

    def test_completion_first_rejects_waiting_new_answer(self):
        Answer.objects.filter(evaluation_participant=self.participation, question=self.common).delete()
        def save_after():
            try:
                self.save(self.common, text_value='Não criar depois de COMPLETED')
            except ValidationError:
                return 'rejected'
            return 'saved'
        self.assertEqual(self.contend(lambda: self.finish(), save_after), 'rejected')
        self.assertFalse(Answer.objects.filter(evaluation_participant=self.participation, question=self.common).exists())

    def test_two_completions_only_one_transition(self):
        def second():
            try:
                services.complete_evaluation(user=self.owner, evaluation=self.evaluation)
            except ValidationError:
                return 'rejected'
            return 'completed'
        self.assertEqual(self.contend(lambda: services.complete_evaluation(user=self.owner, evaluation=self.evaluation), second), 'rejected')
        self.evaluation.refresh_from_db()
        self.assertEqual(self.evaluation.status, ChecklistEvaluation.Status.COMPLETED)
        self.assertEqual(Answer.objects.count(), 6)
