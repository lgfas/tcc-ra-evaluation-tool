from importlib import import_module
from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import IntegrityError, connection, transaction
from django.test import TestCase
from rest_framework.test import APIClient
from .models import ArchitecturalElementType as ElementType, RAElement, ReferenceArchitectureMember as Member, RAVersion
from .services import create_reference_architecture

TYPES = '/api/architectural-element-types/'


class ElementTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(email='owner@elements.test', name='Owner')
        self.editor = get_user_model().objects.create_user(email='editor@elements.test', name='Editor')
        self.other = get_user_model().objects.create_user(email='other@elements.test', name='Other')
        self.ra = create_reference_architecture(user=self.owner, name='RA', visibility='PRIVATE',
                                              initial_version={'version': '1.0', 'description_markdown': 'Primeira'})
        self.version = self.ra.versions.get()
        Member.objects.create(reference_architecture=self.ra, user=self.editor, role='EDITOR')
        self.predefined = ElementType.objects.get(name='Componente', created_by_user=None)
        self.custom = ElementType.objects.create(name='Tipo da proprietária', created_by_user=self.owner)
        self.private_type = ElementType.objects.create(name='Tipo privado externo', created_by_user=self.other)
        self.element = RAElement.objects.create(ra_version=self.version, element_type=self.custom,
                                               name='API', description_markdown='# Original\n<script>alert(1)</script>')
        self.path = f'/api/reference-architectures/{self.ra.pk}/versions/{self.version.pk}/elements/'
        self.detail = f'{self.path}{self.element.pk}/'
        self.data = {'name': 'Backend', 'description_markdown': '## Serviços\nDescrição', 'element_type_id': self.predefined.pk}
        self.client = APIClient(enforce_csrf_checks=True)
        self.client.force_login(self.owner)

    def write(self, path, data, method='post', csrf=True):
        headers = {'HTTP_X_CSRFTOKEN': self.client.get('/api/auth/csrf/').json()['csrfToken']} if csrf else {}
        return getattr(self.client, method)(path, data, format='json', **headers)

    def test_create_relationships_and_markdown(self):
        response = self.write(self.path, self.data)
        self.assertEqual(response.status_code, 201)
        element = RAElement.objects.get(pk=response.json()['id'])
        self.assertEqual(element.ra_version, self.version)
        self.assertEqual(element.element_type, self.predefined)
        self.assertEqual(element.description_markdown, self.data['description_markdown'])
        self.assertEqual(response.json()['element_type'], {'id': self.predefined.pk, 'name': 'Componente'})
        self.assertEqual(self.client.get(self.detail).json()['description_markdown'], self.element.description_markdown)

    def test_required_model_relationships(self):
        for fields in [{'ra_version_id': None, 'element_type': self.predefined}, {'ra_version': self.version, 'element_type_id': None}]:
            with self.subTest(fields=fields), self.assertRaises(IntegrityError), transaction.atomic():
                RAElement.objects.create(name='Invalid', description_markdown='x', **fields)

    def test_missing_version_or_type(self):
        missing_path = f'/api/reference-architectures/{self.ra.pk}/versions/999999/elements/'
        self.assertEqual(self.write(missing_path, self.data).status_code, 404)
        self.assertEqual(self.write(self.path, {**self.data, 'element_type_id': 999999}).status_code, 400)
        self.assertEqual(self.write(self.detail, {'element_type_id': 999999}, 'patch').status_code, 400)

    def test_cannot_transfer_version(self):
        version = RAVersion.objects.create(reference_architecture=self.ra, version='2', description_markdown='x')
        for field in ['ra_version', 'ra_version_id']:
            self.assertEqual(self.write(self.detail, {field: version.pk, 'name': 'Changed'}, 'patch').status_code, 400)
        self.element.refresh_from_db()
        self.assertEqual(self.element.ra_version, self.version)
        self.assertEqual(self.element.name, 'API')

    def test_duplicate_element_names_allowed(self):
        for _ in range(2):
            self.assertEqual(self.write(self.path, {**self.data, 'name': 'API'}).status_code, 201)
        self.assertEqual(self.version.elements.filter(name='API').count(), 3)

    def test_predefined_types_and_idempotent_seed(self):
        seed = import_module('apps.reference_architectures.migrations.0003_seed_element_types')
        with connection.schema_editor() as schema_editor:
            seed.seed_types(apps, schema_editor)
            seed.seed_types(apps, schema_editor)
        for name in ['Componente', 'Conector']:
            self.assertEqual(ElementType.objects.filter(name=name, created_by_user=None).count(), 1)
        result = self.client.get(TYPES).json()
        self.assertIn({'id': self.predefined.pk, 'name': 'Componente'}, result)

    def test_custom_type_creator_is_session_user(self):
        for creator in [self.other.pk, None]:
            response = self.write(TYPES, {'name': 'Evento', 'created_by_user': creator, 'created_by_user_id': creator})
            self.assertEqual(response.status_code, 201)
            element_type = ElementType.objects.get(pk=response.json()['id'])
            self.assertEqual(element_type.created_by_user, self.owner)
            self.assertEqual(set(response.json()), {'id', 'name'})
            self.assertEqual(self.write(self.path, {**self.data, 'element_type_id': element_type.pk}).status_code, 201)

    def test_type_names_are_validated(self):
        for name in ['', ' ', 'x' * 256]:
            self.assertEqual(self.write(TYPES, {'name': name}).status_code, 400)

    def test_types_private_by_default(self):
        self.client.force_login(self.editor)
        ids = [item['id'] for item in self.client.get(TYPES).json()]
        self.assertNotIn(self.custom.pk, ids)
        self.assertNotIn(self.private_type.pk, ids)
        self.assertIn(self.predefined.pk, ids)
        self.assertEqual(self.write(self.path, {**self.data, 'element_type_id': self.private_type.pk}).status_code, 400)

    def test_contextual_type_reuse_by_members(self):
        self.client.force_login(self.editor)
        url = f'{TYPES}?reference_architecture_id={self.ra.pk}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn({'id': self.custom.pk, 'name': self.custom.name}, response.json())
        self.assertNotIn(self.private_type.pk, [item['id'] for item in response.json()])
        self.assertEqual(self.write(self.path, {**self.data, 'element_type_id': self.custom.pk}).status_code, 201)
        self.assertEqual(self.write(self.detail, {'element_type_id': self.custom.pk}, 'patch').status_code, 200)

    def test_unassociated_type_not_shared_with_editor(self):
        unused = ElementType.objects.create(name='Não utilizado', created_by_user=self.owner)
        self.client.force_login(self.editor)
        self.assertNotIn(unused.pk, [item['id'] for item in self.client.get(f'{TYPES}?reference_architecture_id={self.ra.pk}').json()])
        self.assertEqual(self.write(self.path, {**self.data, 'element_type_id': unused.pk}).status_code, 400)

    def test_context_requires_access_and_valid_id(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(f'{TYPES}?reference_architecture_id={self.ra.pk}').status_code, 404)
        for invalid in ['invalid', '-1', '0', '999999999999999999999999999999']:
            self.assertEqual(self.client.get(f'{TYPES}?reference_architecture_id={invalid}').status_code, 400)
        self.assertEqual(self.client.get(f'{TYPES}?reference_architecture_id=999999').status_code, 404)

    def test_owner_and_editor_can_create_edit(self):
        for user in [self.owner, self.editor]:
            self.client.force_login(user)
            self.assertEqual(self.write(self.path, self.data).status_code, 201)
            response = self.write(self.detail, {'name': user.name, 'element_type_id': self.predefined.pk, 'description_markdown': '# Atualizada'}, 'patch')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['name'], user.name)
            self.assertEqual(response.json()['description_markdown'], '# Atualizada')

    def test_public_outsider_read_only_and_type_privacy(self):
        self.ra.visibility = 'PUBLIC'; self.ra.save()
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.path).status_code, 200)
        response = self.client.get(self.detail)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['element_type'], {'id': self.custom.pk, 'name': self.custom.name})
        self.assertEqual(set(response.json()), {'id', 'name', 'description_markdown', 'element_type'})
        self.assertEqual(self.write(self.path, self.data).status_code, 403)
        self.assertEqual(self.write(self.detail, {'name': 'x'}, 'patch').status_code, 403)
        # Public reading does not make this owner's custom types selectable by outsiders.
        self.assertNotIn(self.custom.pk, [item['id'] for item in self.client.get(f'{TYPES}?reference_architecture_id={self.ra.pk}').json()])

    def test_private_outsider_cannot_read_or_write(self):
        self.client.force_login(self.other)
        for path in [self.path, self.detail]:
            self.assertEqual(self.client.get(path).status_code, 404)
        self.assertEqual(self.write(self.path, self.data).status_code, 404)
        self.assertEqual(self.write(self.detail, {'name': 'x'}, 'patch').status_code, 404)

    def test_anonymous_access_blocked(self):
        self.client.logout()
        for path in [self.path, self.detail, TYPES]:
            self.assertEqual(self.client.get(path).status_code, 403)
        self.assertEqual(self.write(self.path, self.data).status_code, 403)
        self.assertEqual(self.write(TYPES, {'name': 'Evento'}).status_code, 403)
        self.assertEqual(self.write(self.detail, {'name': 'x'}, 'patch').status_code, 403)

    def test_mutations_require_csrf(self):
        for path, data, method in [(self.path, self.data, 'post'), (self.detail, {'name': 'x'}, 'patch'), (TYPES, {'name': 'Evento'}, 'post')]:
            self.assertEqual(self.write(path, data, method, csrf=False).status_code, 403)
            self.assertEqual(getattr(self.client, method)(path, data, format='json', HTTP_X_CSRFTOKEN='invalid').status_code, 403)
        self.assertEqual(self.version.elements.count(), 1)

    def test_versions_are_isolated_and_not_copied(self):
        old = RAElement.objects.values().get(pk=self.element.pk)
        response = self.write(f'/api/reference-architectures/{self.ra.pk}/versions/', {'version': '2.0', 'description_markdown': 'Nova'})
        self.assertEqual(response.status_code, 201)
        new_path = f"/api/reference-architectures/{self.ra.pk}/versions/{response.json()['id']}/elements/"
        self.assertEqual(self.client.get(new_path).json(), [])
        created = self.write(new_path, {**self.data, 'name': 'API'})
        self.assertEqual(created.status_code, 201)
        self.assertEqual(self.write(f"{new_path}{created.json()['id']}/", {'description_markdown': 'Alteração só na 2.0'}, 'patch').status_code, 200)
        self.assertEqual(RAElement.objects.values().get(pk=self.element.pk), old)
        self.assertEqual([item['id'] for item in self.client.get(self.path).json()], [self.element.pk])
        mismatched = f'{new_path}{self.element.pk}/'
        self.assertEqual(self.client.get(mismatched).status_code, 404)
        self.assertEqual(self.write(mismatched, {'name': 'x'}, 'patch').status_code, 404)

    def test_mismatched_architecture_ids(self):
        other_ra = create_reference_architecture(user=self.owner, name='Outra', visibility='PRIVATE', initial_version={'version': '1', 'description_markdown': 'x'})
        wrong_version = f'/api/reference-architectures/{other_ra.pk}/versions/{self.version.pk}/elements/'
        valid_version_wrong_element = f'/api/reference-architectures/{other_ra.pk}/versions/{other_ra.versions.get().pk}/elements/{self.element.pk}/'
        self.assertEqual(self.write(wrong_version, self.data).status_code, 404)
        for path in [wrong_version + f'{self.element.pk}/', valid_version_wrong_element]:
            self.assertEqual(self.client.get(path).status_code, 404)
            self.assertEqual(self.write(path, {'name': 'x'}, 'patch').status_code, 404)

    def test_element_validation(self):
        for changes in [{'name': ''}, {'name': ' '}, {'description_markdown': ''}, {'element_type_id': None}]:
            self.assertEqual(self.write(self.path, {**self.data, **changes}).status_code, 400)
            self.assertEqual(self.write(self.detail, changes, 'patch').status_code, 400)

    def test_no_deletion_or_global_type_edit(self):
        self.assertEqual(self.write(self.detail, {}, 'delete').status_code, 405)
        self.assertEqual(self.write(TYPES, {'name': 'Changed'}, 'patch').status_code, 405)

    def test_list_loads_types_without_per_element_queries(self):
        for index in range(5):
            RAElement.objects.create(ra_version=self.version, element_type=self.custom, name=f'Element {index}', description_markdown='x')
        with self.assertNumQueries(1):
            from .serializers import ElementSerializer
            result = ElementSerializer(self.version.elements.select_related('element_type'), many=True).data
        self.assertEqual(len(result), 6)

    def test_contextual_types_span_versions_but_not_other_architectures(self):
        second = RAVersion.objects.create(reference_architecture=self.ra, version='2', description_markdown='x')
        other_ra = create_reference_architecture(user=self.editor, name='Outra', visibility='PRIVATE', initial_version={'version': '1', 'description_markdown': 'x'})
        self.client.force_login(self.editor)
        second_path = f'/api/reference-architectures/{self.ra.pk}/versions/{second.pk}/elements/'
        other_path = f'/api/reference-architectures/{other_ra.pk}/versions/{other_ra.versions.get().pk}/elements/'
        self.assertEqual(self.write(second_path, {**self.data, 'element_type_id': self.custom.pk}).status_code, 201)
        self.assertEqual(self.write(other_path, {**self.data, 'element_type_id': self.custom.pk}).status_code, 400)
