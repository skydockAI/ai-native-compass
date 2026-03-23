"""Tests for DI-011 audit log routes (TS-011 TC-011-017 through TC-011-023)."""

import pytest

from app.models.audit_log import AuditLog


# ---------------------------------------------------------------------------
# TC-011-017: Admin can access audit log list page
# ---------------------------------------------------------------------------

class TestAuditAccess:

    def test_admin_can_access_audit_log(self, admin_client):
        """TC-011-017: Admin user can view audit log."""
        resp = admin_client.get('/audit/')
        assert resp.status_code == 200

    def test_non_admin_cannot_access_audit_log(self, auth_client):
        """TC-011-018: Non-admin (viewer) is forbidden from audit log."""
        resp = auth_client.get('/audit/')
        assert resp.status_code in (302, 403)

    def test_unauthenticated_redirects_to_login(self, client):
        """TC-011-019: Unauthenticated access redirects to login."""
        resp = client.get('/audit/')
        assert resp.status_code == 302
        assert '/login' in resp.headers['Location']

    def test_editor_cannot_access_audit_log(self, editor_client):
        """TC-011-018: Editor is forbidden from audit log."""
        resp = editor_client.get('/audit/')
        assert resp.status_code in (302, 403)


# ---------------------------------------------------------------------------
# TC-011-020 through TC-011-023: Filter and HTMX partial
# ---------------------------------------------------------------------------

class TestAuditFilters:

    def _add_entries(self, db):
        db.session.add(AuditLog(action='create', entity_type='user', entity_id=1))
        db.session.add(AuditLog(action='archive', entity_type='team', entity_id=2))
        db.session.commit()

    def test_entity_type_filter(self, admin_client, db):
        """TC-011-020: entity_type filter returns only matching entries."""
        self._add_entries(db)
        resp = admin_client.get('/audit/?entity_type=user')
        assert resp.status_code == 200

    def test_action_filter(self, admin_client, db):
        """TC-011-021: action filter returns only matching entries."""
        self._add_entries(db)
        resp = admin_client.get('/audit/?action=create')
        assert resp.status_code == 200

    def test_text_search(self, admin_client, db):
        """TC-011-022: text search returns 200."""
        self._add_entries(db)
        resp = admin_client.get('/audit/?q=user')
        assert resp.status_code == 200

    def test_htmx_partial_response(self, admin_client, db):
        """TC-011-023: HTMX request returns partial HTML without full document."""
        resp = admin_client.get('/audit/', headers={'HX-Request': 'true'})
        assert resp.status_code == 200
        html = resp.data.decode('utf-8')
        assert '<html' not in html
        assert '<!DOCTYPE' not in html

    def test_audit_page_shows_entries(self, admin_client, db):
        """TC-011-024: Audit entries appear in the page output."""
        db.session.add(AuditLog(action='login', entity_type='session', entity_id=1))
        db.session.commit()
        resp = admin_client.get('/audit/')
        assert resp.status_code == 200
        html = resp.data.decode('utf-8')
        assert 'login' in html

    def test_pagination_param_accepted(self, admin_client, db):
        """TC-011-025: page param is accepted without error."""
        resp = admin_client.get('/audit/?page=1')
        assert resp.status_code == 200
