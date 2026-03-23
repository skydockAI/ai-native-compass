"""Tests for RBAC decorators (TC-004-001 through TC-004-004)."""


class TestRoleRequired:
    """@role_required decorator tests."""

    # TC-004-001
    def test_admin_can_access_admin_route(self, admin_client):
        resp = admin_client.get('/users/')
        assert resp.status_code == 200

    # TC-004-002
    def test_editor_denied_admin_route(self, editor_client):
        resp = editor_client.get('/users/')
        assert resp.status_code == 403

    # TC-004-003
    def test_viewer_denied_admin_route(self, auth_client):
        resp = auth_client.get('/users/')
        assert resp.status_code == 403

    # TC-004-004
    def test_unauthenticated_redirected_to_login(self, client, db):
        resp = client.get('/users/')
        assert resp.status_code == 302
        assert '/login' in resp.headers['Location']
