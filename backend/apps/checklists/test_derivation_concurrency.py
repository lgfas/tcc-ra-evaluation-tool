from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from threading import Event
from time import monotonic, sleep
from django.db import close_old_connections, connection, transaction
from django.test import TransactionTestCase
from rest_framework.exceptions import NotFound
from . import services
from .test_derivation import DerivationFixture


class DerivationConcurrencyTests(DerivationFixture, TransactionTestCase):
    """Independent PostgreSQL transactions and observed row-lock contention."""
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
                    raise RuntimeError('Timeout liberando a transação de derivação.')
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
                while monotonic() < deadline:
                    with connection.cursor() as cursor:
                        cursor.execute('SELECT wait_event_type FROM pg_stat_activity WHERE pid = %s', [pid])
                        row = cursor.fetchone()
                    if row and row[0] == 'Lock':
                        break
                    sleep(0.02)
                else:
                    self.fail('A operação concorrente não aguardou o bloqueio esperado.')
            finally:
                release.set()
            return holder.result(timeout=10), waiter.result(timeout=10)

    def edit_source(self):
        return services.save_question(user=self.owner, version=self.version, instance=self.questions[1],
            data={'statement': 'Alteração concorrente confirmada',
                  'options': [{'label': 'Alternativa após edição', 'order_index': 0}],
                  'stakeholder_ids': [self.roles[1].pk]})

    def test_edit_first_derivation_copies_the_committed_graph(self):
        _, derived = self.contend(self.edit_source, self.derive)
        self.assertEqual(self.graph(derived.versions.get()), self.graph(self.version))
        copied = derived.versions.get().questions.get(order_index=self.questions[1].order_index)
        self.assertEqual(copied.statement, 'Alteração concorrente confirmada')
        self.assertEqual(list(copied.options.values_list('label', flat=True)), ['Alternativa após edição'])
        self.assertEqual(list(copied.stakeholders.values_list('name', flat=True)), [self.roles[1].name])

    def test_derivation_first_keeps_pre_edit_graph_and_does_not_freeze_source(self):
        before = self.graph(self.version)
        derived, _ = self.contend(self.derive, self.edit_source)
        self.assertEqual(self.graph(derived.versions.get()), before)
        self.assertNotEqual(self.graph(self.version), before)

    def test_visibility_change_first_rejects_waiting_derivation(self):
        before = self.counts()
        def derive_after():
            try:
                self.derive()
            except NotFound:
                return 'rejected'
            return 'derived'
        _, result = self.contend(lambda: services.update_checklist(user=self.owner, checklist=self.source,
            data={'visibility': 'PRIVATE'}), derive_after)
        self.assertEqual(result, 'rejected')
        self.assertEqual(self.counts(), before)

    def test_derivation_first_visibility_update_waits_and_copied_data_remains(self):
        before = self.graph(self.version)
        derived, _ = self.contend(self.derive, lambda: services.update_checklist(
            user=self.owner, checklist=self.source, data={'visibility': 'PRIVATE'}))
        self.assertEqual(self.graph(derived.versions.get()), before)
        self.source.refresh_from_db()
        self.assertEqual(self.source.visibility, 'PRIVATE')

    def test_start_and_derivation_share_version_lock_without_deadlock(self):
        from apps.reference_architectures import services as ra_services
        from apps.checklist_evaluations import services as evaluations
        from apps.version_protection import version_is_frozen
        ra = ra_services.create_reference_architecture(user=self.owner, name='RA', visibility='PRIVATE',
            initial_version={'version': '1', 'description_markdown': ''})
        evaluation = evaluations.create_evaluation(user=self.owner, ra_version_id=ra.versions.get().pk,
                                                  checklist_version_id=self.version.pk)
        evaluations.save_participant(user=self.owner, evaluation=evaluation, email=self.owner.email, stakeholder_role_ids=[])
        derived, started = self.contend(self.derive, lambda: evaluations.start_evaluation(user=self.owner, evaluation=evaluation))
        self.assertEqual(started.status, 'IN_PROGRESS')
        self.assertEqual(self.graph(derived.versions.get()), self.graph(self.version))
        self.assertTrue(version_is_frozen(checklist_version_id=self.version.pk))
        self.assertFalse(version_is_frozen(checklist_version_id=derived.versions.get().pk))
