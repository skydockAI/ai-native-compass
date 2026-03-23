"""Tests for DI-010 dashboard and filtering routes (TS-010 TC-010-001 through TC-010-019)."""

import pytest

from app.models.product import Product
from app.models.repository import Repository
from app.models.team import Team
from app.models.template import RepoTemplate
from app.models.user import User, UserRole
from app.services import repository_service


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def team(db):
    t = Team(name='DI010 Team')
    db.session.add(t)
    db.session.commit()
    return t


@pytest.fixture
def template(db):
    t = RepoTemplate(name='DI010 Template')
    db.session.add(t)
    db.session.commit()
    return t


@pytest.fixture
def repo(db, team, template):
    return repository_service.create_repository(
        name='DI010 Repo',
        url='https://example.com/di010',
        team_id=team.id,
        template_id=template.id,
    )


# ---------------------------------------------------------------------------
# TC-010-001 & TC-010-002: Dashboard landing page
# ---------------------------------------------------------------------------

class TestDashboard:

    def test_dashboard_returns_200_for_authenticated(self, auth_client):
        """TC-010-002: Dashboard returns 200 for authenticated users."""
        resp = auth_client.get('/')
        assert resp.status_code == 200

    def test_dashboard_contains_stat_card_labels(self, auth_client, db):
        """TC-010-003: Dashboard page contains summary card labels."""
        resp = auth_client.get('/')
        html = resp.data.decode('utf-8')
        assert 'Products' in html
        assert 'Repositories' in html
        assert 'Templates' in html
        assert 'Teams' in html

    def test_dashboard_shows_users_card_for_admin(self, admin_client, db):
        """TC-010-003: Admin sees Users card on dashboard."""
        resp = admin_client.get('/')
        html = resp.data.decode('utf-8')
        assert 'Users' in html

    def test_dashboard_unauthenticated_redirects(self, client):
        """TC-010-001: Unauthenticated access to dashboard redirects to login."""
        resp = client.get('/')
        assert resp.status_code == 302
        assert '/login' in resp.headers['Location']


# ---------------------------------------------------------------------------
# TC-010-010: Repository list route with filter query params
# ---------------------------------------------------------------------------

class TestRepositoryListFilter:

    def test_repository_list_returns_200(self, auth_client):
        """TC-010-010: Repository list returns 200."""
        resp = auth_client.get('/repositories/')
        assert resp.status_code == 200

    def test_repository_list_with_team_filter(self, auth_client, db, team, template, repo):
        """TC-010-010: Repository list accepts team_id filter param."""
        resp = auth_client.get(f'/repositories/?team_id={team.id}')
        assert resp.status_code == 200
        html = resp.data.decode('utf-8')
        assert repo.name in html

    def test_repository_list_with_template_filter(self, auth_client, db, team, template, repo):
        """TC-010-010: Repository list accepts template_id filter param."""
        resp = auth_client.get(f'/repositories/?template_id={template.id}')
        assert resp.status_code == 200

    def test_repository_list_with_combined_filters(self, auth_client, db, team, template, repo):
        """TC-010-019: Repository list accepts combined filter params."""
        resp = auth_client.get(f'/repositories/?team_id={team.id}&template_id={template.id}')
        assert resp.status_code == 200

    def test_repository_list_htmx_partial(self, auth_client, db):
        """TC-010-011: Repository list returns partial HTML for HTMX requests."""
        resp = auth_client.get('/repositories/', headers={'HX-Request': 'true'})
        assert resp.status_code == 200
        html = resp.data.decode('utf-8')
        # Partial should NOT contain full HTML wrapper
        assert '<html' not in html
        assert '<!DOCTYPE' not in html

    def test_repository_list_archived_filter(self, auth_client, db, team, template):
        """TC-010-010: Repository list accepts archived=1 param."""
        archived = repository_service.create_repository(
            name='Archived Filter Test',
            url='https://example.com/archived-test',
            team_id=team.id,
            template_id=template.id,
        )
        repository_service.archive_repository(archived.id)

        resp = auth_client.get('/repositories/?archived=1')
        assert resp.status_code == 200
        html = resp.data.decode('utf-8')
        assert 'Archived Filter Test' in html


# ---------------------------------------------------------------------------
# TC-010-014 & TC-010-015: Users list filter
# ---------------------------------------------------------------------------

class TestUsersListFilter:

    def test_users_list_returns_200_for_admin(self, admin_client):
        """TC-010-014: Users list returns 200 for admin."""
        resp = admin_client.get('/users/')
        assert resp.status_code == 200

    def test_users_list_with_role_filter(self, admin_client):
        """TC-010-014: Users list accepts role filter param."""
        resp = admin_client.get('/users/?role=admin')
        assert resp.status_code == 200

    def test_users_list_htmx_partial(self, admin_client):
        """TC-010-015: Users list returns partial HTML for HTMX requests."""
        resp = admin_client.get('/users/', headers={'HX-Request': 'true'})
        assert resp.status_code == 200
        html = resp.data.decode('utf-8')
        assert '<html' not in html
        assert '<!DOCTYPE' not in html

    def test_users_list_role_filter_editor(self, admin_client):
        """TC-010-014: Users list accepts role=editor param."""
        resp = admin_client.get('/users/?role=editor')
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# TC-010-016: Products list HTMX partial
# ---------------------------------------------------------------------------

class TestProductsListFilter:

    def test_products_list_returns_200(self, auth_client):
        """TC-010-016: Products list returns 200."""
        resp = auth_client.get('/products/')
        assert resp.status_code == 200

    def test_products_list_htmx_partial(self, auth_client):
        """TC-010-016: Products list returns partial HTML for HTMX requests."""
        resp = auth_client.get('/products/', headers={'HX-Request': 'true'})
        assert resp.status_code == 200
        html = resp.data.decode('utf-8')
        assert '<html' not in html

    def test_products_list_archived_filter(self, auth_client):
        """TC-010-016: Products list accepts archived=1 param."""
        resp = auth_client.get('/products/?archived=1')
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# TC-010-017: Teams list HTMX partial
# ---------------------------------------------------------------------------

class TestTeamsListFilter:

    def test_teams_list_returns_200(self, auth_client):
        """TC-010-017: Teams list returns 200."""
        resp = auth_client.get('/teams/')
        assert resp.status_code == 200

    def test_teams_list_htmx_partial(self, auth_client):
        """TC-010-017: Teams list returns partial HTML for HTMX requests."""
        resp = auth_client.get('/teams/', headers={'HX-Request': 'true'})
        assert resp.status_code == 200
        html = resp.data.decode('utf-8')
        assert '<html' not in html

    def test_teams_list_archived_filter(self, auth_client):
        """TC-010-017: Teams list accepts archived=1 param."""
        resp = auth_client.get('/teams/?archived=1')
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# TC-010-018: Templates list HTMX partial
# ---------------------------------------------------------------------------

class TestTemplatesListFilter:

    def test_templates_list_returns_200(self, auth_client):
        """TC-010-018: Templates list returns 200."""
        resp = auth_client.get('/templates/')
        assert resp.status_code == 200

    def test_templates_list_htmx_partial(self, auth_client):
        """TC-010-018: Templates list returns partial HTML for HTMX requests."""
        resp = auth_client.get('/templates/', headers={'HX-Request': 'true'})
        assert resp.status_code == 200
        html = resp.data.decode('utf-8')
        assert '<html' not in html

    def test_templates_list_archived_filter(self, auth_client):
        """TC-010-018: Templates list accepts archived=1 param."""
        resp = auth_client.get('/templates/?archived=1')
        assert resp.status_code == 200
