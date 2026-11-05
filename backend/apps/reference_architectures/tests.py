from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework.test import APIClient
from .models import ReferenceArchitecture as RA, ReferenceArchitectureMember as Member, RAVersion
from .services import create_reference_architecture

BASE = '/api/reference-architectures/'


class ArchitectureTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(email='owner@example.com', name='Owner', password='Test!Senha-891')
        self.editor = get_user_model().objects.create_user(email='editor@example.com', name='Editor')
        self.other = get_user_model().objects.create_user(email='other@example.com', name='Other')
        self.client = APIClient(enforce_csrf_checks=True)
        self.client.force_login(self.owner)
        self.payload = {'name': 'RA exemplo', 'visibility': 'PRIVATE', 'initial_version': {'version': '1.0', 'description_markdown': '# Original\nDescrição'}}
        self.ra = create_reference_architecture(user=self.owner, **self.payload)
        Member.objects.create(reference_architecture=self.ra, user=self.editor, role='EDITOR')
        self.url = f'{BASE}{self.ra.pk}/'

    def write(self, url, data, method='post', csrf=True):
        headers = {'HTTP_X_CSRFTOKEN': self.client.get('/api/auth/csrf/').json()['csrfToken']} if csrf else {}
        return getattr(self.client, method)(url, data, format='json', **headers)

    def test_create_and_owner(self):
        response = self.write(BASE, {**self.payload, 'owner_id': self.other.pk})
        self.assertEqual(response.status_code, 201)
        ra = RA.objects.get(pk=response.json()['id'])
        self.assertEqual(ra.members.filter(role='OWNER').count(), 1)
        self.assertEqual(ra.members.get().user, self.owner)
        self.assertEqual(ra.versions.get().description_markdown, '# Original\nDescrição')
        self.assertEqual(response.json()['version_count'], 1)
        self.assertNotIn('members', response.json())

    def test_member_constraints(self):
        for user, role in [(self.owner, 'EDITOR'), (self.other, 'OWNER')]:
            with self.subTest(role=role), self.assertRaises(IntegrityError), transaction.atomic():
                Member.objects.create(reference_architecture=self.ra, user=user, role=role)
        self.assertEqual(self.ra.members.filter(role='OWNER').count(), 1)

    def test_atomic_creation(self):
        before = (RA.objects.count(), Member.objects.count(), RAVersion.objects.count())
        with patch('apps.reference_architectures.services.RAVersion.objects.create', side_effect=IntegrityError('failure')):
            with self.assertRaises(IntegrityError):
                create_reference_architecture(user=self.owner, **self.payload)
        self.assertEqual((RA.objects.count(), Member.objects.count(), RAVersion.objects.count()), before)

    def test_anonymous_endpoints(self):
        self.client.logout()
        version = self.ra.versions.get()
        for url in [BASE, self.url, self.url + 'versions/', self.url + f'versions/{version.pk}/']:
            self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.write(BASE, self.payload).status_code, 403)
        self.assertEqual(self.write(self.url, {'name': 'x'}, 'patch').status_code, 403)
        self.assertEqual(self.write(self.url + 'versions/', {'version': '2', 'description_markdown': 'x'}).status_code, 403)

    def test_new_version_preserves_history(self):
        old = self.ra.versions.values().get()
        response = self.write(self.url + 'versions/', {'version': '2.0', 'description_markdown': 'Nova'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.ra.versions.values().get(pk=old['id']), old)
        self.assertEqual(self.ra.versions.count(), 2)
        self.assertEqual(response.json()['description_markdown'], 'Nova')

    def test_duplicate_version_and_different_ra(self):
        self.assertEqual(self.write(self.url + 'versions/', self.payload['initial_version']).status_code, 400)
        with self.assertRaises(IntegrityError), transaction.atomic():
            RAVersion.objects.create(reference_architecture=self.ra, **self.payload['initial_version'])
        self.assertEqual(self.write(BASE, self.payload).status_code, 201)

    def test_private_owner_and_editor_read(self):
        for user in [self.owner, self.editor]:
            self.client.force_login(user)
            self.assertEqual(self.client.get(self.url).status_code, 200)
            self.assertEqual(self.client.get(self.url + 'versions/').status_code, 200)

    def test_private_outsider_hidden_including_versions(self):
        self.client.force_login(self.other)
        for url in [self.url, self.url + 'versions/', self.url + f'versions/{self.ra.versions.get().pk}/']:
            self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.write(self.url + 'versions/', self.payload['initial_version']).status_code, 404)

    def test_public_read_only(self):
        self.ra.visibility = 'PUBLIC'; self.ra.save()
        self.client.force_login(self.other)
        for url in [self.url, self.url + 'versions/', self.url + f'versions/{self.ra.versions.get().pk}/']:
            self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.write(self.url, {'visibility': 'PRIVATE'}, 'patch').status_code, 403)
        self.assertEqual(self.write(self.url + 'versions/', self.payload['initial_version']).status_code, 403)

    def test_owner_metadata_does_not_change_versions(self):
        old = list(self.ra.versions.values())
        self.assertEqual(self.write(self.url, {'name': 'Novo nome', 'visibility': 'PUBLIC'}, 'patch').status_code, 200)
        self.ra.refresh_from_db()
        self.assertEqual((self.ra.name, self.ra.visibility), ('Novo nome', 'PUBLIC'))
        self.assertEqual(list(self.ra.versions.values()), old)

    def test_editor_permissions(self):
        self.client.force_login(self.editor)
        self.assertEqual(self.write(self.url, {'visibility': 'PUBLIC'}, 'patch').status_code, 403)
        self.assertEqual(self.write(self.url, {'name': 'Outro'}, 'patch').status_code, 403)
        self.assertEqual(self.write(self.url + 'versions/', {'version': '2', 'description_markdown': 'Editor'}).status_code, 201)

    def test_membership_list_only(self):
        outsider = create_reference_architecture(user=self.other, **{**self.payload, 'visibility': 'PUBLIC'})
        response = self.client.get(BASE).json()
        self.assertEqual([item['id'] for item in response], [self.ra.pk])
        self.assertEqual(response[0]['role'], 'OWNER')
        self.assertEqual(response[0]['version_count'], 1)
        self.client.force_login(self.editor)
        self.assertEqual(self.client.get(BASE).json()[0]['role'], 'EDITOR')
        self.client.force_login(self.other)
        self.assertEqual([item['id'] for item in self.client.get(BASE).json()], [outsider.pk])

    def test_version_scoped_to_architecture(self):
        other_ra = create_reference_architecture(user=self.owner, **self.payload)
        self.assertEqual(self.client.get(self.url + f'versions/{other_ra.versions.get().pk}/').status_code, 404)

    def test_validation(self):
        for changes in [{'name': ' '}, {'visibility': 'INVALID'}, {'initial_version': {}}, {'initial_version': {'version': ' ', 'description_markdown': 'x'}}]:
            self.assertEqual(self.write(BASE, {**self.payload, **changes}).status_code, 400)
        for changes in [{'name': ''}, {'visibility': 'invalid'}]:
            self.assertEqual(self.write(self.url, changes, 'patch').status_code, 400)
        self.assertEqual(self.write(self.url + 'versions/', {'version': '', 'description_markdown': 'x'}).status_code, 400)

    def test_mutations_require_csrf(self):
        for url, data, method in [(BASE, self.payload, 'post'), (self.url, {'name': 'x'}, 'patch'), (self.url + 'versions/', {'version': '2', 'description_markdown': 'x'}, 'post')]:
            self.assertEqual(self.write(url, data, method, csrf=False).status_code, 403)
            self.assertEqual(getattr(self.client, method)(url, data, format='json', HTTP_X_CSRFTOKEN='invalid').status_code, 403)
        self.assertEqual(RA.objects.count(), 1)
        self.assertEqual(self.ra.versions.count(), 1)

    def test_no_delete_or_version_update(self):
        self.assertEqual(self.write(self.url, {}, 'delete').status_code, 405)
        self.assertEqual(self.write(self.url + f'versions/{self.ra.versions.get().pk}/', {'description_markdown': 'changed'}, 'patch').status_code, 405)
