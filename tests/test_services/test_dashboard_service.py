"""Tests for dashboard service (TS-010 TC-010-004, TC-010-005, TC-010-020)."""

from app.models.product import Product
from app.models.repository import Repository
from app.models.team import Team
from app.models.template import RepoTemplate
from app.models.user import User, UserRole
from app.services import dashboard_service


# ---------------------------------------------------------------------------
# TC-010-005: counts return 0 when no active entities exist
# ---------------------------------------------------------------------------

class TestDashboardCountsEmpty:

    def test_all_counts_zero_when_empty(self, db):  # noqa: ARG001 — db fixture sets up test database
        """TC-010-005: All counts are 0 with no active entities."""
        counts = dashboard_service.get_dashboard_counts()
        assert counts['products'] == 0
        assert counts['repositories'] == 0
        assert counts['templates'] == 0
        assert counts['teams'] == 0
        assert counts['users'] == 0


# ---------------------------------------------------------------------------
# TC-010-004: counts exclude archived entities
# ---------------------------------------------------------------------------

class TestDashboardCountsExcludeArchived:

    def test_product_count_excludes_archived(self, db):
        """TC-010-004: Product count excludes archived products."""
        db.session.add(Product(name='Active Product A'))
        db.session.add(Product(name='Active Product B'))
        archived = Product(name='Archived Product', is_archived=True, is_active=False)
        db.session.add(archived)
        db.session.commit()

        counts = dashboard_service.get_dashboard_counts()
        assert counts['products'] == 2

    def test_team_count_excludes_archived(self, db):
        """TC-010-020: Team count excludes archived teams."""
        db.session.add(Team(name='Active Team'))
        db.session.add(Team(name='Archived Team', is_archived=True, is_active=False))
        db.session.commit()

        counts = dashboard_service.get_dashboard_counts()
        assert counts['teams'] == 1

    def test_user_count_excludes_archived(self, db):
        """TC-010-004: User count excludes archived users."""
        u1 = User(email='active@example.com', full_name='Active User', role=UserRole.VIEWER)
        u1.set_password('password1')
        u2 = User(email='archived@example.com', full_name='Archived User',
                  role=UserRole.VIEWER, is_archived=True, is_active=False)
        u2.set_password('password1')
        db.session.add_all([u1, u2])
        db.session.commit()

        counts = dashboard_service.get_dashboard_counts()
        assert counts['users'] == 1

    def test_returns_correct_counts_for_all_entities(self, db):
        """TC-010-004: All entity counts are correct and exclude archived."""
        # Create active entities
        db.session.add(Product(name='Prod 1'))
        db.session.add(Team(name='Team 1'))
        template = RepoTemplate(name='Tmpl 1')
        db.session.add(template)
        db.session.commit()

        team = Team.query.filter_by(name='Team 1').first()
        tmpl = RepoTemplate.query.filter_by(name='Tmpl 1').first()
        repo = Repository(name='Repo 1', url='https://example.com/1',
                         team_id=team.id, template_id=tmpl.id)
        db.session.add(repo)

        u = User(email='u@example.com', full_name='User One', role=UserRole.VIEWER)
        u.set_password('password1')
        db.session.add(u)
        db.session.commit()

        counts = dashboard_service.get_dashboard_counts()
        assert counts['products'] == 1
        assert counts['teams'] == 1
        assert counts['templates'] == 1
        assert counts['repositories'] == 1
        assert counts['users'] == 1
