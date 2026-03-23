"""Tests for template management routes (TS-006)."""

import pytest

from app.models.template import ArtifactType, ArtifactValueType
from app.services import template_service


@pytest.fixture
def template(db):
    """Create and persist a sample template."""
    return template_service.create_template(name='Test Template', description='A test template')


@pytest.fixture
def archived_template(db):
    """Create and persist an archived template."""
    t = template_service.create_template(name='Old Template')
    template_service.archive_template(t.id)
    return t


@pytest.fixture
def template_with_artifact(db, template):
    """Add a document artifact to the sample template."""
    template_service.add_artifact(
        template_id=template.id,
        artifact_type=ArtifactType.document,
        name='Architecture Doc',
    )
    return template


@pytest.fixture
def list_artifact(db, template):
    """Add an Other:list artifact to the sample template."""
    return template_service.add_artifact(
        template_id=template.id,
        artifact_type=ArtifactType.other,
        name='Priority',
        value_type=ArtifactValueType.list,
    )


class TestTemplateListRoute:

    # TC-006-001
    def test_authenticated_user_can_list_templates(self, auth_client, template):
        resp = auth_client.get('/templates/')
        assert resp.status_code == 200
        assert b'Test Template' in resp.data

    # TC-006-014
    def test_unauthenticated_redirects_to_login(self, client):
        resp = client.get('/templates/')
        assert resp.status_code == 302
        assert '/login' in resp.headers['Location']

    # TC-006-002
    def test_show_archived_filter(self, admin_client, archived_template):
        resp = admin_client.get('/templates/?archived=1')
        assert resp.status_code == 200
        assert b'Old Template' in resp.data

    def test_active_view_excludes_archived(self, admin_client, archived_template):
        resp = admin_client.get('/templates/')
        assert resp.status_code == 200
        assert b'Old Template' not in resp.data


class TestTemplateDetailRoute:

    # TC-006-029
    def test_authenticated_user_can_view_detail(self, auth_client, template_with_artifact):
        resp = auth_client.get(f'/templates/{template_with_artifact.id}')
        assert resp.status_code == 200
        assert b'Test Template' in resp.data
        assert b'Architecture Doc' in resp.data

    def test_nonexistent_template_redirects(self, admin_client):
        resp = admin_client.get('/templates/99999', follow_redirects=True)
        assert resp.status_code == 200
        assert b'not found' in resp.data.lower()


class TestTemplateCreateRoute:

    # TC-006-004
    def test_viewer_cannot_access_create_form(self, auth_client):
        resp = auth_client.get('/templates/new')
        assert resp.status_code == 403

    def test_editor_cannot_access_create_form(self, editor_client):
        resp = editor_client.get('/templates/new')
        assert resp.status_code == 403

    # TC-006-003
    def test_admin_can_view_create_form(self, admin_client):
        resp = admin_client.get('/templates/new')
        assert resp.status_code == 200
        assert b'New Template' in resp.data

    def test_admin_can_create_template(self, admin_client):
        resp = admin_client.post('/templates/new', data={
            'name': 'Admin Created',
            'description': 'Desc',
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'Template created successfully' in resp.data

    def test_duplicate_name_shows_error(self, admin_client, template):
        resp = admin_client.post('/templates/new', data={
            'name': 'Test Template',
            'description': '',
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'already exists' in resp.data


class TestTemplateEditRoute:

    # TC-006-006
    def test_viewer_cannot_access_edit_form(self, auth_client, template):
        resp = auth_client.get(f'/templates/{template.id}/edit')
        assert resp.status_code == 403

    # TC-006-005
    def test_admin_can_edit_template(self, admin_client, template):
        resp = admin_client.post(f'/templates/{template.id}/edit', data={
            'name': 'Renamed Template',
            'description': 'Updated',
            'version': str(template.version),
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'Template updated successfully' in resp.data


class TestTemplateArchiveRoute:

    # TC-006-011
    def test_viewer_cannot_archive(self, auth_client, template):
        resp = auth_client.post(f'/templates/{template.id}/archive')
        assert resp.status_code == 403

    def test_editor_cannot_archive(self, editor_client, template):
        resp = editor_client.post(f'/templates/{template.id}/archive')
        assert resp.status_code == 403

    # TC-006-009 (via route)
    def test_admin_can_archive_template(self, admin_client, template):
        resp = admin_client.post(f'/templates/{template.id}/archive', follow_redirects=True)
        assert resp.status_code == 200
        assert b'archived successfully' in resp.data

    # TC-006-012 (via route)
    def test_admin_can_reactivate_template(self, admin_client, archived_template):
        resp = admin_client.post(
            f'/templates/{archived_template.id}/reactivate', follow_redirects=True
        )
        assert resp.status_code == 200
        assert b'reactivated successfully' in resp.data


class TestArtifactRoutes:

    def test_admin_can_view_add_artifact_form(self, admin_client, template):
        """GET /templates/<id>/artifacts/new renders without error (regression for Jinja2 bug)."""
        resp = admin_client.get(f'/templates/{template.id}/artifacts/new')
        assert resp.status_code == 200
        assert b'Add Artifact' in resp.data

    def test_admin_can_view_edit_artifact_form(self, admin_client, template_with_artifact):
        """GET /templates/<id>/artifacts/<aid>/edit renders without error (regression)."""
        artifact = template_with_artifact.artifacts[0]
        resp = admin_client.get(
            f'/templates/{template_with_artifact.id}/artifacts/{artifact.id}/edit'
        )
        assert resp.status_code == 200
        assert b'Edit Artifact' in resp.data

    # TC-006-022
    def test_viewer_cannot_add_artifact(self, auth_client, template):
        resp = auth_client.post(f'/templates/{template.id}/artifacts/new', data={
            'type': 'document',
            'name': 'Doc',
            'display_order': '0',
        })
        assert resp.status_code == 403

    # TC-006-015
    def test_admin_can_add_document_artifact(self, admin_client, template):
        resp = admin_client.post(f'/templates/{template.id}/artifacts/new', data={
            'type': 'document',
            'name': 'My Doc',
            'description': '',
            'value_type': '',
            'display_order': '0',
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'Artifact added successfully' in resp.data

    # TC-006-019
    def test_admin_can_add_other_list_artifact(self, admin_client, template):
        resp = admin_client.post(f'/templates/{template.id}/artifacts/new', data={
            'type': 'other',
            'name': 'Priority',
            'description': '',
            'value_type': 'list',
            'is_required': 'false',
            'display_order': '0',
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'Artifact added successfully' in resp.data

    # TC-006-024 (via route)
    def test_admin_can_remove_artifact(self, admin_client, template_with_artifact):
        artifact = template_with_artifact.artifacts[0]
        resp = admin_client.post(
            f'/templates/{template_with_artifact.id}/artifacts/{artifact.id}/remove',
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b'Artifact removed successfully' in resp.data


class TestListOptionRoutes:

    # TC-006-025 (via route)
    def test_admin_can_add_list_option(self, admin_client, template, list_artifact):
        resp = admin_client.post(
            f'/templates/{template.id}/artifacts/{list_artifact.id}/options/new',
            data={'value': 'High', 'display_order': '0'},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b'List option added successfully' in resp.data

    # TC-006-027 (via route)
    def test_admin_can_deactivate_list_option(self, admin_client, template, list_artifact):
        opt = template_service.add_list_option(artifact_id=list_artifact.id, value='Medium')
        resp = admin_client.post(
            f'/templates/{template.id}/artifacts/{list_artifact.id}/options/{opt.id}/deactivate',
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b'deactivated' in resp.data

    # TC-006-028 (via route)
    def test_admin_can_delete_list_option(self, admin_client, template, list_artifact):
        opt = template_service.add_list_option(artifact_id=list_artifact.id, value='Low')
        resp = admin_client.post(
            f'/templates/{template.id}/artifacts/{list_artifact.id}/options/{opt.id}/delete',
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b'deleted' in resp.data

    def test_viewer_cannot_add_list_option(self, auth_client, template, list_artifact):
        resp = auth_client.post(
            f'/templates/{template.id}/artifacts/{list_artifact.id}/options/new',
            data={'value': 'X', 'display_order': '0'},
        )
        assert resp.status_code == 403
