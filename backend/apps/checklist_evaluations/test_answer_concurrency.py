from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from django.db import close_old_connections, connection
from django.test import TransactionTestCase
from rest_framework.test import APIClient
from .test_answers import AnswerFixture
from .models import Answer


class AnswerConcurrencyTests(AnswerFixture, TransactionTestCase):
    def test_simultaneous_puts_upsert_one_answer(self):
        self.begin()
        barrier = Barrier(2)

        def save(text):
            close_old_connections()
            try:
                client = APIClient(enforce_csrf_checks=True)
                client.force_login(self.reader)
                token = client.get('/api/auth/csrf/').json()['csrfToken']
                barrier.wait(timeout=5)
                result = client.put(self.answer_url(self.common), {'text_value': text}, format='json', HTTP_X_CSRFTOKEN=token)
                return result.status_code, result.json()
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(save, text) for text in ['Primeira requisição', 'Segunda requisição']]
            results = [future.result(timeout=15) for future in futures]
        self.assertEqual([status for status, _ in results], [200, 200], results)
        self.assertEqual(results[0][1]['id'], results[1][1]['id'])
        self.assertEqual(Answer.objects.filter(evaluation_participant=self.participation, question=self.common).count(), 1)
        self.assertIn(Answer.objects.get().text_value, ['Primeira requisição', 'Segunda requisição'])
