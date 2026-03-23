"""Tests for DI-010 service layer filters (TS-010 TC-010-006 through TC-010-013)."""

import pytest

from app.models.product import Product
from app.models.repository import Repository, product_repository
from app.models.team import Team
from app.models.template import RepoTemplate
from app.models.user import User, UserRole
from app.services import repository_service, user_service


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def team_a(db):
    t = Team(name='Team Alpha')
    db.session.add(t)
    db.session.commit()
    return t


@pytest.fixture
def team_b(db):
    t = Team(name='Team Beta')
    db.session.add(t)
    db.session.commit()
    return t


@pytest.fixture
def template_a(db):
    t = RepoTemplate(name='Template Alpha')
    db.session.add(t)
    db.session.commit()
    return t


@pytest.fixture
def template_b(db):
    t = RepoTemplate(name='Template Beta')
    db.session.add(t)
    db.session.commit()
    return t


@pytest.fixture
def product_a(db):
    p = Product(name='Product Alpha')
    db.session.add(p)
    db.session.commit()
    return p


@pytest.fixture
def product_b(db):
    p = Product(name='Product Beta')
    db.session.add(p)
    db.session.commit()
    return p


def _make_repo(db, name, url, team, template):
    r = Repository(name=name, url=url, team_id=team.id, template_id=template.id)
    db.session.add(r)
    db.session.commit()
    return r


def _link_repo_to_product(db, repo, product):
    db.session.execute(
        product_repository.insert().values(product_id=product.id, repository_id=repo.id)
    )
    db.session.commit()


# ---------------------------------------------------------------------------
# TC-010-006: filter by team
# ---------------------------------------------------------------------------

class TestRepositoryFilterByTeam:

    def test_filter_by_team_returns_only_matching_repos(self, db, team_a, team_b, template_a):
        """TC-010-006: get_repositories(team_id) returns only repos for that team."""
        r1 = _make_repo(db, 'Repo Alpha', 'https://a.com/1', team_a, template_a)
        _make_repo(db, 'Repo Beta', 'https://b.com/1', team_b, template_a)

        result = repository_service.get_repositories(team_id=team_a.id)
        assert len(result) == 1
        assert result[0].id == r1.id

    def test_filter_by_team_returns_empty_when_no_match(self, db, team_a, team_b, template_a):
        """TC-010-006: get_repositories(team_id) returns empty list when no repos match."""
        _make_repo(db, 'Repo', 'https://a.com/1', team_b, template_a)
        result = repository_service.get_repositories(team_id=team_a.id)
        assert result == []


# ---------------------------------------------------------------------------
# TC-010-007: filter by template
# ---------------------------------------------------------------------------

class TestRepositoryFilterByTemplate:

    def test_filter_by_template_returns_only_matching_repos(self, db, team_a, template_a, template_b):
        """TC-010-007: get_repositories(template_id) returns only repos using that template."""
        r1 = _make_repo(db, 'Repo Alpha', 'https://a.com/1', team_a, template_a)
        _make_repo(db, 'Repo Beta', 'https://b.com/1', team_a, template_b)

        result = repository_service.get_repositories(template_id=template_a.id)
        assert len(result) == 1
        assert result[0].id == r1.id


# ---------------------------------------------------------------------------
# TC-010-008: filter by product
# ---------------------------------------------------------------------------

class TestRepositoryFilterByProduct:

    def test_filter_by_product_returns_only_linked_repos(self, db, team_a, template_a, product_a, product_b):
        """TC-010-008: get_repositories(product_id) returns only repos linked to that product."""
        r1 = _make_repo(db, 'Repo Alpha', 'https://a.com/1', team_a, template_a)
        r2 = _make_repo(db, 'Repo Beta', 'https://b.com/1', team_a, template_a)
        _link_repo_to_product(db, r1, product_a)
        _link_repo_to_product(db, r2, product_b)

        result = repository_service.get_repositories(product_id=product_a.id)
        assert len(result) == 1
        assert result[0].id == r1.id

    def test_filter_by_product_excludes_unlinked_repos(self, db, team_a, template_a, product_a):
        """TC-010-008: repos not linked to any product not returned when filtering by product."""
        _make_repo(db, 'Unlinked Repo', 'https://a.com/1', team_a, template_a)
        result = repository_service.get_repositories(product_id=product_a.id)
        assert result == []


# ---------------------------------------------------------------------------
# TC-010-009: combined filters (team + template)
# ---------------------------------------------------------------------------

class TestRepositoryFilterCombined:

    def test_combined_team_and_template_filter(self, db, team_a, team_b, template_a, template_b):
        """TC-010-009: Combined team + template filter uses AND logic."""
        r_match = _make_repo(db, 'Match', 'https://a.com/1', team_a, template_a)
        _make_repo(db, 'Wrong Team', 'https://b.com/1', team_b, template_a)
        _make_repo(db, 'Wrong Template', 'https://c.com/1', team_a, template_b)

        result = repository_service.get_repositories(team_id=team_a.id, template_id=template_a.id)
        assert len(result) == 1
        assert result[0].id == r_match.id


# ---------------------------------------------------------------------------
# TC-010-012: user filter by role
# ---------------------------------------------------------------------------

class TestUserFilterByRole:

    def _make_user(self, db, email, role, archived=False):
        u = User(
            email=email,
            full_name=email.split('@')[0],
            role=UserRole(role),
            is_archived=archived,
            is_active=not archived,
        )
        u.set_password('password1')
        db.session.add(u)
        db.session.commit()
        return u

    def test_filter_by_admin_role(self, db):
        """TC-010-012: get_users(role='admin') returns only admin users."""
        self._make_user(db, 'admin@test.com', 'admin')
        self._make_user(db, 'editor@test.com', 'editor')
        self._make_user(db, 'viewer@test.com', 'viewer')

        result = user_service.get_users(role='admin')
        assert len(result) == 1
        assert result[0].role == UserRole.ADMIN

    def test_filter_by_editor_role(self, db):
        """TC-010-012: get_users(role='editor') returns only editor users."""
        self._make_user(db, 'admin@test.com', 'admin')
        self._make_user(db, 'editor@test.com', 'editor')

        result = user_service.get_users(role='editor')
        assert len(result) == 1
        assert result[0].role == UserRole.EDITOR

    def test_filter_by_invalid_role_returns_all(self, db):
        """Invalid role value is silently ignored, all users returned."""
        self._make_user(db, 'u1@test.com', 'admin')
        self._make_user(db, 'u2@test.com', 'viewer')

        result = user_service.get_users(role='superuser')
        assert len(result) == 2

    def test_filter_by_none_role_returns_all(self, db):
        """TC-010-012: role=None returns all users (no role filter)."""
        self._make_user(db, 'u1@test.com', 'admin')
        self._make_user(db, 'u2@test.com', 'viewer')

        result = user_service.get_users(role=None)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# TC-010-013: combined role + archived filter
# ---------------------------------------------------------------------------

class TestUserFilterCombined:

    def _make_user(self, db, email, role, archived=False):
        u = User(
            email=email,
            full_name=email.split('@')[0],
            role=UserRole(role),
            is_archived=archived,
            is_active=not archived,
        )
        u.set_password('password1')
        db.session.add(u)
        db.session.commit()
        return u

    def test_role_and_archived_filter_combined(self, db):
        """TC-010-013: Combined role + archived filter returns correct subset."""
        self._make_user(db, 'active_editor@test.com', 'editor', archived=False)
        self._make_user(db, 'archived_editor@test.com', 'editor', archived=True)
        self._make_user(db, 'active_viewer@test.com', 'viewer', archived=False)

        # Only active editors
        result = user_service.get_users(role='editor', include_archived=False)
        assert len(result) == 1
        assert result[0].email == 'active_editor@test.com'
