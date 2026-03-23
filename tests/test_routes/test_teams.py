"""Tests for team management routes (TC-005-001 through TC-005-018)."""

import pytest

from app.services import team_service


@pytest.fixture
def team(db):
    """Create and persist a sample team."""
    return team_service.create_team(name='Test Team', description='A test team')


@pytest.fixture
def archived_team(db):
    """Create and persist an archived team."""
    t = team_service.create_team(name='Old Team')
    team_service.archive_team(t.id)
    return t


class TestTeamListRoute:
    """Team list page tests."""

    # TC-005-001
    def test_authenticated_user_can_list_teams(self, auth_client, team):
        resp = auth_client.get('/teams/')
        assert resp.status_code == 200
        assert b'Test Team' in resp.data

    # TC-005-018
    def test_unauthenticated_redirects_to_login(self, client):
        resp = client.get('/teams/')
        assert resp.status_code == 302
        assert '/login' in resp.headers['Location']

    # TC-005-002
    def test_show_archived_filter(self, admin_client, archived_team):
        resp = admin_client.get('/teams/?archived=1')
        assert resp.status_code == 200
        assert b'Old Team' in resp.data

    def test_active_view_excludes_archived(self, admin_client, archived_team):
        resp = admin_client.get('/teams/')
        assert resp.status_code == 200
        assert b'Old Team' not in resp.data


class TestTeamCreateRoute:
    """Team creation route tests."""

    # TC-005-005
    def test_viewer_cannot_access_create_form(self, auth_client):
        resp = auth_client.get('/teams/new')
        assert resp.status_code == 403

    # TC-005-003
    def test_admin_can_view_create_form(self, admin_client):
        resp = admin_client.get('/teams/new')
        assert resp.status_code == 200
        assert b'New Team' in resp.data

    # TC-005-004
    def test_editor_can_create_team(self, editor_client):
        resp = editor_client.post('/teams/new', data={
            'name': 'Editor Created',
            'description': 'Created by editor',
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'Team created successfully' in resp.data

    # TC-005-003
    def test_admin_can_create_team(self, admin_client):
        resp = admin_client.post('/teams/new', data={
            'name': 'Admin Created',
            'description': '',
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'Team created successfully' in resp.data

    def test_duplicate_name_shows_error(self, admin_client, team):
        resp = admin_client.post('/teams/new', data={
            'name': 'Test Team',
            'description': '',
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'already exists' in resp.data

    def test_empty_name_shows_error(self, admin_client):
        resp = admin_client.post('/teams/new', data={
            'name': '',
            'description': '',
        }, follow_redirects=True)
        assert resp.status_code == 200
        # WTForms DataRequired triggers validation error
        assert b'This field is required' in resp.data or b'required' in resp.data.lower()


class TestTeamEditRoute:
    """Team edit route tests."""

    # TC-005-008
    def test_viewer_cannot_access_edit_form(self, auth_client, team):
        resp = auth_client.get(f'/teams/{team.id}/edit')
        assert resp.status_code == 403

    # TC-005-006
    def test_admin_can_edit_team(self, admin_client, team):
        resp = admin_client.post(f'/teams/{team.id}/edit', data={
            'name': 'Renamed Team',
            'description': 'Updated description',
            'version': str(team.version),
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'Team updated successfully' in resp.data

    # TC-005-007
    def test_editor_can_edit_team(self, editor_client, team):
        resp = editor_client.post(f'/teams/{team.id}/edit', data={
            'name': 'Editor Renamed',
            'description': '',
            'version': str(team.version),
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'Team updated successfully' in resp.data

    def test_edit_nonexistent_team_redirects(self, admin_client):
        resp = admin_client.get('/teams/99999/edit', follow_redirects=True)
        assert resp.status_code == 200
        assert b'not found' in resp.data.lower()


class TestTeamArchiveRoute:
    """Team archive/reactivate route tests."""

    # TC-005-016
    def test_viewer_cannot_archive(self, auth_client, team):
        resp = auth_client.post(f'/teams/{team.id}/archive')
        assert resp.status_code == 403

    # TC-005-015
    def test_admin_can_archive_team(self, admin_client, team):
        resp = admin_client.post(f'/teams/{team.id}/archive', follow_redirects=True)
        assert resp.status_code == 200
        assert b'archived successfully' in resp.data

    # TC-005-014
    def test_admin_can_reactivate_team(self, admin_client, archived_team):
        resp = admin_client.post(f'/teams/{archived_team.id}/reactivate', follow_redirects=True)
        assert resp.status_code == 200
        assert b'reactivated successfully' in resp.data

    def test_editor_can_archive_team(self, editor_client, team):
        resp = editor_client.post(f'/teams/{team.id}/archive', follow_redirects=True)
        assert resp.status_code == 200
        assert b'archived successfully' in resp.data
