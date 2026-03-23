"""Tests for shared attribute management routes (DI-006, REQ-034–036)."""

import pytest

from app.models.shared_attribute import SharedAttributeDefinition
from app.services import shared_attribute_service


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def default_attrs(db):
    """Seed four default shared attributes."""
    for name in ['Name', 'Team', 'URL', 'Description']:
        db.session.add(SharedAttributeDefinition(name=name, is_default=True, is_active=True))
    db.session.commit()


@pytest.fixture
def custom_attr(db):
    """Create a custom shared attribute."""
    return shared_attribute_service.create_attribute('GitHub URL')


@pytest.fixture
def inactive_attr(db):
    """Create and deactivate a custom shared attribute."""
    attr = shared_attribute_service.create_attribute('Inactive Attr')
    shared_attribute_service.deactivate_attribute(attr.id)
    return attr


# ---------------------------------------------------------------------------
# Access control
# ---------------------------------------------------------------------------

class TestSharedAttributeAccessControl:

    def test_unauthenticated_redirects_to_login(self, client):
        resp = client.get('/shared-attributes/')
        assert resp.status_code == 302
        assert '/login' in resp.headers['Location']

    def test_non_admin_gets_403(self, auth_client, db):
        resp = auth_client.get('/shared-attributes/')
        assert resp.status_code == 403

    def test_editor_gets_403(self, editor_client, db):
        resp = editor_client.get('/shared-attributes/')
        assert resp.status_code == 403

    def test_admin_can_access_list(self, admin_client, db):
        resp = admin_client.get('/shared-attributes/')
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

class TestSharedAttributeList:

    def test_shows_default_attributes(self, admin_client, default_attrs):
        resp = admin_client.get('/shared-attributes/')
        assert resp.status_code == 200
        assert b'Name' in resp.data
        assert b'Team' in resp.data
        assert b'URL' in resp.data
        assert b'Description' in resp.data

    def test_shows_protected_badge_for_defaults(self, admin_client, default_attrs):
        resp = admin_client.get('/shared-attributes/')
        assert b'Protected' in resp.data

    def test_shows_custom_attribute(self, admin_client, custom_attr):
        resp = admin_client.get('/shared-attributes/')
        assert b'GitHub URL' in resp.data

    def test_inactive_hidden_by_default(self, admin_client, inactive_attr):
        resp = admin_client.get('/shared-attributes/')
        assert b'Inactive Attr' not in resp.data

    def test_show_inactive_filter(self, admin_client, inactive_attr):
        resp = admin_client.get('/shared-attributes/?inactive=1')
        assert b'Inactive Attr' in resp.data


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

class TestSharedAttributeCreate:

    def test_get_create_form(self, admin_client, db):
        resp = admin_client.get('/shared-attributes/new')
        assert resp.status_code == 200
        assert b'New Shared Attribute' in resp.data

    def test_create_success(self, admin_client, db):
        resp = admin_client.post(
            '/shared-attributes/new',
            data={'name': 'My Custom Attr', 'submit': 'Create Attribute'},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b'My Custom Attr' in resp.data
        assert b'created successfully' in resp.data

    def test_create_duplicate_shows_error(self, admin_client, custom_attr):
        resp = admin_client.post(
            '/shared-attributes/new',
            data={'name': 'GitHub URL', 'submit': 'Create Attribute'},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b'already exists' in resp.data

    def test_create_empty_name_shows_error(self, admin_client, db):
        resp = admin_client.post(
            '/shared-attributes/new',
            data={'name': '', 'submit': 'Create Attribute'},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        # WTForms validation should catch it
        assert b'New Shared Attribute' in resp.data

    def test_non_admin_create_gets_403(self, auth_client, db):
        resp = auth_client.post(
            '/shared-attributes/new',
            data={'name': 'Hack', 'submit': 'Create Attribute'},
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Edit
# ---------------------------------------------------------------------------

class TestSharedAttributeEdit:

    def test_get_edit_form(self, admin_client, custom_attr):
        resp = admin_client.get(f'/shared-attributes/{custom_attr.id}/edit')
        assert resp.status_code == 200
        assert b'GitHub URL' in resp.data

    def test_edit_success(self, admin_client, custom_attr):
        resp = admin_client.post(
            f'/shared-attributes/{custom_attr.id}/edit',
            data={'name': 'Renamed Attr', 'submit': 'Save Changes'},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b'updated successfully' in resp.data
        assert b'Renamed Attr' in resp.data

    def test_edit_default_attribute_redirects_with_error(self, admin_client, default_attrs):
        default = SharedAttributeDefinition.query.filter_by(name='Name').first()
        resp = admin_client.get(
            f'/shared-attributes/{default.id}/edit',
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b'cannot be renamed' in resp.data

    def test_edit_not_found_redirects(self, admin_client, db):
        resp = admin_client.get('/shared-attributes/9999/edit', follow_redirects=True)
        assert resp.status_code == 200
        assert b'not found' in resp.data

    def test_non_admin_edit_gets_403(self, auth_client, custom_attr):
        resp = auth_client.post(
            f'/shared-attributes/{custom_attr.id}/edit',
            data={'name': 'Hack', 'submit': 'Save Changes'},
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Deactivate
# ---------------------------------------------------------------------------

class TestSharedAttributeDeactivate:

    def test_deactivate_custom_attribute(self, admin_client, custom_attr):
        resp = admin_client.post(
            f'/shared-attributes/{custom_attr.id}/deactivate',
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b'deactivated' in resp.data

    def test_deactivate_default_shows_error(self, admin_client, default_attrs):
        default = SharedAttributeDefinition.query.filter_by(name='URL').first()
        resp = admin_client.post(
            f'/shared-attributes/{default.id}/deactivate',
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b'cannot be deactivated' in resp.data

    def test_non_admin_deactivate_gets_403(self, auth_client, custom_attr):
        resp = auth_client.post(f'/shared-attributes/{custom_attr.id}/deactivate')
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Reactivate
# ---------------------------------------------------------------------------

class TestSharedAttributeReactivate:

    def test_reactivate_inactive_attribute(self, admin_client, inactive_attr):
        resp = admin_client.post(
            f'/shared-attributes/{inactive_attr.id}/reactivate',
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b'reactivated' in resp.data

    def test_reactivate_active_shows_error(self, admin_client, custom_attr):
        resp = admin_client.post(
            f'/shared-attributes/{custom_attr.id}/reactivate',
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b'already active' in resp.data
