from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from threading import Barrier, Event
from time import monotonic, sleep
from django.db import close_old_connections, connection, transaction
from django.test import TransactionTestCase
from rest_framework.exceptions import ValidationError
from apps.reference_architectures import services as ra_services
from apps.checklists import services as checklist_services
from .models import ChecklistEvaluation
from . import services
from .tests import EvaluationFixture


class EvaluationConcurrencyTests(EvaluationFixture, TransactionTestCase):
    """Real independent PostgreSQL transactions and observable row-lock contention."""

    def worker(self, action):
        close_old_connections()
        try:
            return action()
        finally:
            connection.close()

    def assert_waiting_for_lock(self, pid):
        deadline = monotonic() + 5
        while monotonic() < deadline:
            with connection.cursor() as cursor:
                cursor.execute('SELECT wait_event_type FROM pg_stat_activity WHERE pid = %s', [pid])
                row = cursor.fetchone()
            if row and row[0] == 'Lock':
                return
            sleep(0.02)
        self.fail('A transação concorrente não aguardou o bloqueio esperado.')

    def contend(self, hold_action, waiting_action):
        held, release = Event(), Event()
        pids = Queue()
        def hold():
            with transaction.atomic():
                result = hold_action()
                held.set()
                if not release.wait(10): raise RuntimeError('Timeout liberando transação de teste.')
                return result
        def wait():
            with connection.cursor() as cursor:
                cursor.execute('SELECT pg_backend_pid()')
                pids.put(cursor.fetchone()[0])
            return waiting_action()
        with ThreadPoolExecutor(max_workers=2) as executor:
            holder = executor.submit(self.worker, hold)
            try:
                self.assertTrue(held.wait(5))
                waiter = executor.submit(self.worker, wait)
                self.assert_waiting_for_lock(pids.get(timeout=5))
            finally:
                release.set()
            holder.result(timeout=10)
            return waiter.result(timeout=10)

    def test_start_commits_before_ra_edit_checks_usage(self):
        self.participant()
        def edit():
            try:
                ra_services.update_element(user=self.owner, element=self.element, data={'name': 'Não persistir'})
            except ValidationError:
                return 'blocked'
            return 'edited'
        result = self.contend(lambda: services.start_evaluation(user=self.owner, evaluation=self.evaluation), edit)
        self.assertEqual(result, 'blocked')
        self.element.refresh_from_db(); self.assertEqual(self.element.name, 'Elemento')

    def test_start_commits_before_checklist_edit_checks_usage(self):
        self.participant()
        def edit():
            try:
                checklist_services.save_question(user=self.owner, version=self.version, instance=self.question,
                    data={'options': [{'label': 'Não persistir', 'order_index': 0}]})
            except ValidationError:
                return 'blocked'
            return 'edited'
        result = self.contend(lambda: services.start_evaluation(user=self.owner, evaluation=self.evaluation), edit)
        self.assertEqual(result, 'blocked')
        self.assertEqual(self.question.options.get().label, 'Alternativa própria')

    def test_start_waits_for_checklist_edit_then_validates_committed_questions(self):
        self.participant()
        self.question.delete()
        def prepare():
            return checklist_services.save_question(user=self.owner, version=self.version,
                data={'statement': 'Pronta para iniciar', 'response_type': 'TEXT', 'comment_mode': 'NONE'})
        result = self.contend(prepare, lambda: services.start_evaluation(user=self.owner, evaluation=self.evaluation))
        self.assertEqual(result.status, 'IN_PROGRESS')
        self.assertEqual(self.version.questions.get().statement, 'Pronta para iniciar')

    def test_concurrent_start_same_evaluation_has_one_transition(self):
        self.participant()
        barrier = Barrier(2)
        def start():
            barrier.wait(timeout=5)
            try:
                services.start_evaluation(user=self.owner, evaluation=self.evaluation)
                return 'started'
            except ValidationError:
                return 'rejected'
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(self.worker, start) for _ in range(2)]
            self.assertCountEqual([future.result(timeout=10) for future in futures], ['started', 'rejected'])
        self.evaluation.refresh_from_db(); self.assertEqual(self.evaluation.status, 'IN_PROGRESS')

    def test_distinct_evaluations_share_versions_without_deadlock(self):
        self.participant()
        other = services.create_evaluation(user=self.owner, ra_version_id=self.ra_version.pk, checklist_version_id=self.version.pk)
        services.save_participant(user=self.owner, evaluation=other, email=self.reader.email, stakeholder_role_ids=[])
        barrier = Barrier(2)
        def start(evaluation):
            barrier.wait(timeout=5)
            return services.start_evaluation(user=self.owner, evaluation=evaluation).status
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(self.worker, lambda evaluation=evaluation: start(evaluation)) for evaluation in [self.evaluation, other]]
            self.assertEqual([future.result(timeout=10) for future in futures], ['IN_PROGRESS', 'IN_PROGRESS'])
        self.assertEqual(ChecklistEvaluation.objects.filter(status='IN_PROGRESS').count(), 2)
