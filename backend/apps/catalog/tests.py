from django.contrib.auth import get_user_model
from django.db.models.functions import Lower
from django.test import TestCase
from rest_framework.test import APIClient
from apps.reference_architectures import services as ra_services
from apps.reference_architectures.models import ReferenceArchitecture, ReferenceArchitectureMember, ArchitecturalElementType
from apps.checklists import services as checklist_services
from apps.checklists.models import Checklist
from apps.checklist_evaluations import services as evaluation_services
from apps.checklist_evaluations.models import Answer


class CatalogTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(email='owner@catalog.test', name='Autoria reservada')
        self.viewer = get_user_model().objects.create_user(email='viewer@catalog.test', name='Leitor')
        self.client = APIClient(enforce_csrf_checks=True)
        self.client.force_login(self.viewer)
        self.ra = self.architecture(self.owner, 'Sistemas Web', 'PUBLIC')
        self.own_ra = self.architecture(self.viewer, 'Sistemas próprios', 'PUBLIC')
        self.private_ra = self.architecture(self.owner, 'Sistemas privados', 'PRIVATE')
        self.own_private_ra = self.architecture(self.viewer, 'Privada do leitor', 'PRIVATE')
        self.checklist = self.instrument(self.owner, 'Arquitetura configurável', 'PUBLIC')
        self.own_checklist = self.instrument(self.viewer, 'Checklist própria', 'PUBLIC')
        self.private_checklist = self.instrument(self.owner, 'Arquitetura privada', 'PRIVATE')
        self.own_private_checklist = self.instrument(self.viewer, 'Privada do leitor', 'PRIVATE')

    def architecture(self, user, name, visibility):
        return ra_services.create_reference_architecture(user=user, name=name, visibility=visibility,
            initial_version={'version': '1', 'description_markdown': 'Conteúdo da versão'})

    def instrument(self, user, name, visibility):
        return checklist_services.create_checklist(user=user, name=name, visibility=visibility, origin='Fonte do instrumento', initial_version={'version': '1'})

    def catalog(self, kind='ra', **params):
        return self.client.get('/api/catalog/', {'type': kind, **params})

    def write(self, url, data, method='post'):
        token = self.client.get('/api/auth/csrf/').json()['csrfToken']
        return getattr(self.client, method)(url, data, format='json', HTTP_X_CSRFTOKEN=token)

    def test_authenticated_user_can_consult_both_types(self):
        for kind in ['ra', 'checklist']:
            response = self.catalog(kind)
            self.assertEqual(response.status_code, 200)
            self.assertIsInstance(response.data, list)

    def test_anonymous_is_blocked(self):
        self.client.logout()
        for kind in ['ra', 'checklist']:
            self.assertEqual(self.catalog(kind).status_code, 403)

    def test_ra_catalog_only_public_including_own(self):
        response = self.catalog()
        self.assertEqual({row['id'] for row in response.data}, {self.ra.pk, self.own_ra.pk})
        self.assertTrue(all(row['visibility'] == 'PUBLIC' for row in response.data))
        self.assertTrue(all(set(row) == {'id', 'name', 'visibility', 'version_count'} for row in response.data))

    def test_checklist_catalog_only_public_including_own(self):
        response = self.catalog('checklist')
        self.assertEqual({row['id'] for row in response.data}, {self.checklist.pk, self.own_checklist.pk})
        self.assertTrue(all(set(row) == {'id', 'name', 'origin', 'visibility', 'version_count'} for row in response.data))
        self.assertEqual(response.data[0]['origin'], 'Fonte do instrumento')

    def test_collaborator_private_ra_still_excluded_from_catalog(self):
        ReferenceArchitectureMember.objects.create(reference_architecture=self.private_ra, user=self.viewer, role='EDITOR')
        self.assertNotIn(self.private_ra.pk, [row['id'] for row in self.catalog().data])
        self.assertEqual(self.client.get(f'/api/reference-architectures/{self.private_ra.pk}/').status_code, 200)

    def test_partial_name_search_and_case_insensitivity(self):
        for kind, term, expected in [('ra', 'EMAS W', self.ra), ('checklist', 'TETURA CON', self.checklist)]:
            response = self.catalog(kind, q=term)
            self.assertEqual([row['id'] for row in response.data], [expected.pk])
            self.assertEqual(self.catalog(kind, q='  ' + term.lower() + '  ').data, response.data)

    def test_empty_and_missing_query_list_all_public(self):
        for kind in ['ra', 'checklist']:
            self.assertEqual(self.catalog(kind).data, self.catalog(kind, q='   ').data)

    def test_search_without_results_does_not_reveal_private_names(self):
        for kind in ['ra', 'checklist']:
            response = self.catalog(kind, q='privad')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data, [])

    def test_invalid_unknown_repeated_and_oversized_parameters(self):
        urls = ['/api/catalog/', '/api/catalog/?type=', '/api/catalog/?type=invalid',
                '/api/catalog/?type=ra&visibility=PRIVATE', '/api/catalog/?type=ra&type=checklist',
                '/api/catalog/?type=ra&q=a&q=b', '/api/catalog/?type=ra&q=' + 'x' * 256]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 400)
                self.assertTrue(response.data)

    def test_search_special_characters_are_literal(self):
        for kind in ['ra', 'checklist']:
            self.assertEqual(self.catalog(kind, q='%').data, [])
            self.assertEqual(self.catalog(kind, q='_').data, [])

    def test_ordering_and_version_counts(self):
        ra_services.create_version(architecture=self.ra, version='2', description_markdown='Outra versão')
        checklist_services.create_version(user=self.owner, checklist=self.checklist, version='2')
        self.architecture(self.owner, self.ra.name, 'PUBLIC')
        for kind, model, item in [('ra', ReferenceArchitecture, self.ra), ('checklist', Checklist, self.checklist)]:
            result = self.catalog(kind).data
            expected = list(model.objects.filter(visibility='PUBLIC').order_by(Lower('name'), 'name', 'id').values_list('pk', flat=True))
            self.assertEqual([row['id'] for row in result], expected)
            self.assertEqual(next(row['version_count'] for row in result if row['id'] == item.pk), 2)

    def test_metadata_query_does_not_fetch_versions_or_contents_per_artifact(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        from .views import CatalogView
        from rest_framework.test import APIRequestFactory, force_authenticate
        request = APIRequestFactory().get('/api/catalog/', {'type': 'ra'})
        force_authenticate(request, self.viewer)
        with CaptureQueriesContext(connection) as queries:
            response = CatalogView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(queries), 1)
        self.assertNotIn('description_markdown', queries[0]['sql'])

    def test_public_to_private_removes_catalog_and_direct_access(self):
        self.client.force_login(self.owner)
        for path, item, kind in [('reference-architectures', self.ra, 'ra'), ('checklists', self.checklist, 'checklist')]:
            self.assertEqual(self.write(f'/api/{path}/{item.pk}/', {'visibility': 'PRIVATE'}, 'patch').status_code, 200)
            self.client.force_login(self.viewer)
            self.assertNotIn(item.pk, [row['id'] for row in self.catalog(kind).data])
            self.assertEqual(self.client.get(f'/api/{path}/{item.pk}/').status_code, 404)
            self.client.force_login(self.owner)
            self.assertEqual(self.client.get(f'/api/{path}/{item.pk}/').status_code, 200)

    def test_private_direct_and_nested_access_remains_protected(self):
        for path, item, suffix in [('reference-architectures', self.private_ra, 'elements/'), ('checklists', self.private_checklist, 'questions/')]:
            root = f'/api/{path}/{item.pk}/'
            for url in [root, root + 'versions/', root + f'versions/{item.versions.get().pk}/', root + f'versions/{item.versions.get().pk}/' + suffix]:
                self.assertEqual(self.client.get(url).status_code, 404, url)
        self.assertEqual(self.client.get(f'/api/checklists/{self.own_private_checklist.pk}/').status_code, 200)
        self.assertEqual(self.client.get(f'/api/reference-architectures/{self.own_private_ra.pk}/').status_code, 200)

    def test_personal_lists_are_not_globalized(self):
        self.assertEqual({row['id'] for row in self.client.get('/api/reference-architectures/').data}, {self.own_ra.pk, self.own_private_ra.pk})
        self.assertEqual({row['id'] for row in self.client.get('/api/checklists/').data}, {self.own_checklist.pk, self.own_private_checklist.pk})

    def test_public_versions_reused_without_copying_or_editing_rights(self):
        ra_version = self.ra.versions.get()
        version = self.checklist.versions.get()
        role = checklist_services.save_stakeholder(user=self.owner, version=version, data={'name': 'Arquiteto'})
        section = checklist_services.save_section(user=self.owner, version=version, data={'name': 'Objetivos'})
        question = checklist_services.save_question(user=self.owner, version=version, data={
            'statement': 'Objetivos claros?', 'response_type': 'SINGLE_CHOICE', 'comment_mode': 'OPTIONAL',
            'section_id': section.pk, 'stakeholder_ids': [role.pk], 'options': [{'label': 'Configurável', 'order_index': 0}]})
        element_type = ArchitecturalElementType.objects.create(name='Tipo próprio', created_by_user=self.owner)
        element = ra_services.create_element(user=self.owner, version=ra_version,
            data={'name': 'Componente', 'element_type': element_type, 'description_markdown': 'Descrição'})
        counts = (ReferenceArchitecture.objects.count(), Checklist.objects.count())
        response = self.write('/api/checklist-evaluations/', {'ra_version_id': ra_version.pk, 'checklist_version_id': version.pk})
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['ra_version']['id'], ra_version.pk)
        self.assertEqual(response.data['checklist_version']['id'], version.pk)
        self.assertEqual((ReferenceArchitecture.objects.count(), Checklist.objects.count()), counts)
        self.assertFalse(self.ra.members.filter(user=self.viewer).exists())
        self.assertEqual(self.checklist.owner_user_id, self.owner.pk)
        rpath = f'/api/reference-architectures/{self.ra.pk}/versions/{ra_version.pk}/elements/'
        cpath = f'/api/checklists/{self.checklist.pk}/versions/{version.pk}/'
        self.assertEqual(self.client.get(rpath).data[0]['element_type']['name'], 'Tipo próprio')
        result = self.client.get(cpath + 'questions/').data[0]
        self.assertEqual(result['options'][0]['label'], 'Configurável')
        self.assertEqual(result['stakeholders'][0]['id'], role.pk)
        self.assertEqual(result['section']['id'], section.pk)
        for url, data, method in [
            (f'/api/reference-architectures/{self.ra.pk}/', {'name': 'Não editar'}, 'patch'),
            (rpath, {'name': 'Novo', 'element_type_id': element_type.pk, 'description_markdown': ''}, 'post'),
            (rpath + f'{element.pk}/', {'name': 'Não editar'}, 'patch'),
            (f'/api/checklists/{self.checklist.pk}/', {'name': 'Não editar'}, 'patch'),
            (cpath + 'questions/', {'statement': 'Não adicionar'}, 'post'),
            (cpath + f'questions/{question.pk}/', {'statement': 'Não editar'}, 'patch'),
        ]:
            self.assertEqual(self.write(url, data, method).status_code, 403, url)

    def test_stale_public_version_selection_is_revalidated(self):
        self.assertTrue(self.catalog().data)
        self.ra.visibility = 'PRIVATE'
        self.ra.save()
        response = self.write('/api/checklist-evaluations/', {'ra_version_id': self.ra.versions.get().pk,
            'checklist_version_id': self.checklist.versions.get().pk})
        self.assertEqual(response.status_code, 404)
        self.ra.visibility = 'PUBLIC'; self.ra.save()
        self.checklist.visibility = 'PRIVATE'; self.checklist.save()
        self.assertEqual(self.write('/api/checklist-evaluations/', {'ra_version_id': self.ra.versions.get().pk,
            'checklist_version_id': self.checklist.versions.get().pk}).status_code, 404)

    def test_no_evaluations_participants_answers_or_personal_data_exposed(self):
        version = self.checklist.versions.get()
        question = checklist_services.save_question(user=self.owner, version=version,
            data={'statement': 'Não incluir estrutura na listagem', 'response_type': 'TEXT', 'comment_mode': 'OPTIONAL'})
        evaluation = evaluation_services.create_evaluation(user=self.owner, ra_version_id=self.ra.versions.get().pk, checklist_version_id=version.pk)
        evaluation_services.save_participant(user=self.owner, evaluation=evaluation, email=self.owner.email, stakeholder_role_ids=[])
        evaluation_services.start_evaluation(user=self.owner, evaluation=evaluation)
        evaluation_services.save_answer(user=self.owner, evaluation_id=evaluation.pk, question_id=question.pk,
            data={'text_value': 'Resposta privada', 'comment': 'Comentário privado'})
        self.assertEqual(Answer.objects.count(), 1)
        for kind in ['ra', 'checklist']:
            data = self.catalog(kind).data
            for secret in [self.owner.email, self.owner.name, 'Resposta privada', 'Comentário privado', question.statement,
                           'participants', 'answers', 'owner_user', 'created_by_user', 'versions']:
                self.assertNotIn(secret, str(data))
        self.assertEqual(self.client.get(f'/api/checklist-evaluations/{evaluation.pk}/').status_code, 404)

    def test_catalog_has_no_write_operations(self):
        self.assertEqual(self.write('/api/catalog/?type=ra', {'name': 'Não criar'}).status_code, 405)
