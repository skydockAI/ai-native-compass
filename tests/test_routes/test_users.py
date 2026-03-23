"""Tests for user management routes (TC-004-005 through TC-004-029)."""


class TestUserListRoute:
    """User list page tests."""

    # TC-004-005
    def test_admin_can_list_users(self, admin_client):
        resp = admin_client.get('/users/')
        assert resp.status_code == 200
        assert b'Users' in resp.data

    # TC-004-010
    def test_editor_denied_user_list(self, editor_client):
        resp = editor_client.get('/users/')
        assert resp.status_code == 403

    def test_viewer_denied_user_list(self, auth_client):
        resp = auth_client.get('/users/')
        assert resp.status_code == 403


class TestUserCreateRoute:
    """User creation route tests."""

    def test_admin_can_view_create_form(self, admin_client):
        resp = admin_client.get('/users/new')
        assert resp.status_code == 200
        assert b'New User' in resp.data

    # TC-004-006
    def test_admin_can_create_user(self, admin_client):
        resp = admin_client.post('/users/new', data={
            'email': 'created@example.com',
            'full_name': 'Created User',
            'password': 'password123',
            'confirm_password': 'password123',
            'role': 'editor',
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'User created successfully' in resp.data

    def test_editor_denied_create_user(self, editor_client):
        resp = editor_client.get('/users/new')
        assert resp.status_code == 403

    # TC-004-021
    def test_password_mismatch_rejected(self, admin_client):
        resp = admin_client.post('/users/new', data={
            'email': 'mismatch@example.com',
            'full_name': 'Mismatch User',
            'password': 'password123',
            'confirm_password': 'different456',
            'role': 'viewer',
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'Passwords must match' in resp.data


class TestUserEditRoute:
    """User edit route tests."""

    # TC-004-007
    def test_admin_can_edit_user(self, admin_client, test_user):
        resp = admin_client.post(f'/users/{test_user.id}/edit', data={
            'email': 'updated@example.com',
            'full_name': 'Updated Name',
            'role': 'editor',
            'version': str(test_user.version),
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'User updated successfully' in resp.data


class TestUserArchiveRoute:
    """Archive/reactivate route tests."""

    # TC-004-008
    def test_admin_can_archive_user(self, admin_client, test_user):
        resp = admin_client.post(
            f'/users/{test_user.id}/archive',
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b'User archived successfully' in resp.data

    # TC-004-009
    def test_admin_can_reactivate_user(self, admin_client, db, test_user):
        test_user.is_archived = True
        test_user.is_active = False
        db.session.commit()

        resp = admin_client.post(
            f'/users/{test_user.id}/reactivate',
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b'User reactivated successfully' in resp.data

    # TC-004-014
    def test_cannot_archive_seeded_admin(self, admin_client, seeded_admin):
        resp = admin_client.post(
            f'/users/{seeded_admin.id}/archive',
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b'cannot be archived' in resp.data


class TestChangePasswordRoute:
    """Self-service password change route tests."""

    # TC-004-018
    def test_user_can_change_password(self, auth_client):
        resp = auth_client.post('/users/change-password', data={
            'current_password': 'password123',
            'new_password': 'newpassword456',
            'confirm_password': 'newpassword456',
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'Password changed successfully' in resp.data

    # TC-004-019
    def test_wrong_current_password(self, auth_client):
        resp = auth_client.post('/users/change-password', data={
            'current_password': 'wrongpassword',
            'new_password': 'newpassword456',
            'confirm_password': 'newpassword456',
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'incorrect' in resp.data

    def test_change_password_form_loads(self, auth_client):
        resp = auth_client.get('/users/change-password')
        assert resp.status_code == 200
        assert b'Change Password' in resp.data


class TestResetPasswordRoute:
    """Admin password reset route tests."""

    # TC-004-022
    def test_admin_can_reset_password(self, admin_client, test_user):
        resp = admin_client.post(f'/users/{test_user.id}/reset-password', data={
            'new_password': 'resetpass123',
            'confirm_password': 'resetpass123',
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'Password reset successfully' in resp.data

    # TC-004-023
    def test_editor_denied_reset_password(self, editor_client, test_user):
        resp = editor_client.get(f'/users/{test_user.id}/reset-password')
        assert resp.status_code == 403


class TestSidebarVisibility:
    """Sidebar role-awareness tests."""

    # TC-004-027
    def test_admin_sees_admin_sidebar(self, admin_client):
        resp = admin_client.get('/')
        assert b'Users' in resp.data
        assert b'Audit Log' in resp.data

    # TC-004-028
    def test_editor_does_not_see_admin_sidebar(self, editor_client):
        resp = editor_client.get('/')
        assert b'person-gear' not in resp.data

    # TC-004-029
    def test_viewer_does_not_see_admin_sidebar(self, auth_client):
        resp = auth_client.get('/')
        assert b'person-gear' not in resp.data
