from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework.test import APIClient

User = get_user_model()
PASSWORD = 'Semente!Lunar-4829'


class AuthTests(TestCase):
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)
        self.data = {'name': 'Ana Silva', 'email': 'ana@example.com', 'password': PASSWORD}

    def post(self, path, data=None, csrf=True):
        headers = {}
        if csrf:
            token = self.client.get('/api/auth/csrf/').json()['csrfToken']
            headers['HTTP_X_CSRFTOKEN'] = token
        return self.client.post('/api/auth/' + path + '/', data or {}, format='json', **headers)

    def register(self):
        return self.post('register', self.data)

    def login(self):
        return self.post('login', {'email': 'ANA@example.com', 'password': PASSWORD})

    def test_registration_and_hash(self):
        response = self.register()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(set(response.json()), {'id', 'name', 'email'})
        user = User.objects.get()
        self.assertNotEqual(user.password, PASSWORD)
        self.assertTrue(user.check_password(PASSWORD))
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 403)

    def test_duplicate_email(self):
        self.register()
        for email in ['ana@example.com', 'ANA@EXAMPLE.COM']:
            with self.subTest(email=email):
                self.assertEqual(self.post('register', {**self.data, 'email': email}).status_code, 400)
        self.assertEqual(User.objects.count(), 1)

    def test_database_case_insensitive_constraint(self):
        user = User.objects.create_user(**self.data)
        other = User.objects.create_user(name='Outra', email='other@example.com', password=PASSWORD)
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.filter(pk=other.pk).update(email=user.email.upper())

    def test_invalid_registration(self):
        for changes in [{'name': ' '}, {'email': 'invalido'}, {'password': '123'}, {'password': 'password'}]:
            with self.subTest(changes=changes):
                self.assertEqual(self.post('register', {**self.data, **changes}).status_code, 400)
        self.assertEqual(User.objects.count(), 0)

    def test_login_me_and_persistent_session(self):
        self.register()
        self.assertEqual(self.login().status_code, 200)
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['email'], 'ana@example.com')
        second_client = APIClient(enforce_csrf_checks=True)
        second_client.cookies = self.client.cookies.copy()
        self.assertEqual(second_client.get('/api/auth/me/').status_code, 200)
        self.assertTrue(self.client.cookies['sessionid']['httponly'])
        self.assertEqual(self.client.cookies['sessionid']['samesite'], 'Lax')

    def test_invalid_login_and_inactive_user(self):
        self.register()
        for email, password in [('ana@example.com', 'errada'), ('missing@example.com', PASSWORD)]:
            self.assertEqual(self.post('login', {'email': email, 'password': password}).status_code, 400)
        User.objects.update(is_active=False)
        self.assertEqual(self.login().status_code, 400)
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 403)

    def test_anonymous_access(self):
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 403)
        self.assertEqual(self.post('logout').status_code, 403)

    def test_logout_invalidates_session(self):
        self.register()
        self.login()
        stale = APIClient(enforce_csrf_checks=True)
        stale.cookies = self.client.cookies.copy()
        self.assertEqual(self.post('logout').status_code, 204)
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 403)
        self.assertEqual(stale.get('/api/auth/me/').status_code, 403)

    def test_public_operations_require_csrf(self):
        for path in ['register', 'login']:
            self.assertEqual(self.post(path, self.data, csrf=False).status_code, 403)
        self.assertEqual(User.objects.count(), 0)
        self.client.get('/api/auth/csrf/')
        self.assertEqual(self.post('register', self.data, csrf=False).status_code, 403)
        self.assertEqual(self.client.post('/api/auth/register/', self.data, format='json', HTTP_X_CSRFTOKEN='invalid').status_code, 403)

    def test_logout_requires_csrf_and_login_rotates_token(self):
        self.register()
        old_token = self.client.get('/api/auth/csrf/').json()['csrfToken']
        self.login()
        self.assertEqual(self.post('logout', csrf=False).status_code, 403)
        self.assertEqual(self.client.post('/api/auth/logout/', {}, format='json', HTTP_X_CSRFTOKEN=old_token).status_code, 403)
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 200)
        self.assertEqual(self.post('logout').status_code, 204)

    def test_untrusted_origin_rejected(self):
        token = self.client.get('/api/auth/csrf/').json()['csrfToken']
        self.assertEqual(self.client.post('/api/auth/register/', self.data, format='json',
            HTTP_X_CSRFTOKEN=token, HTTP_ORIGIN='http://untrusted.example').status_code, 403)

    def test_health_and_csrf(self):
        self.assertEqual(self.client.get('/api/health/').status_code, 200)
        self.assertEqual(self.client.get('/api/health/').json(), {'status': 'ok'})
        self.assertEqual(self.client.get('/api/auth/csrf/').status_code, 200)
        self.assertIn('csrftoken', self.client.cookies)

    def test_superuser_and_admin(self):
        user = User.objects.create_superuser(email='admin@example.com', name='Admin', password=PASSWORD)
        self.client.force_login(user)
        self.assertEqual(self.client.get('/admin/users/user/').status_code, 200)
        self.assertEqual(self.client.get('/admin/users/user/add/').status_code, 200)
