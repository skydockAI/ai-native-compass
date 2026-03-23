"""Tests for DI-011 audit service and model (TS-011 TC-011-001 through TC-011-016)."""

import pytest

from app.models.audit_log import AuditLog
from app.models.product import Product
from app.models.repository import Repository
from app.models.team import Team
from app.models.template import RepoTemplate
from app.models.user import User, UserRole
from app.services import audit_service, team_service, template_service, user_service


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def team(db):
    t = Team(name='Audit Test Team')
    db.session.add(t)
    db.session.commit()
    return t


@pytest.fixture
def template(db):
    t = RepoTemplate(name='Audit Test Template')
    db.session.add(t)
    db.session.commit()
    return t


# ---------------------------------------------------------------------------
# TC-011-001: AuditLog stores all required fields
# ---------------------------------------------------------------------------

class TestAuditLogModel:

    def test_audit_log_stores_all_fields(self, db):
        """TC-011-001: AuditLog persists all required fields."""
        u = User(email='a@test.com', full_name='A', role=UserRole.VIEWER)
        u.set_password('password1')
        db.session.add(u)
        db.session.commit()

        entry = AuditLog(
            action='create',
            entity_type='user',
            entity_id=u.id,
            before_value=None,
            after_value={'email': 'a@test.com'},
            user_id=u.id,
        )
        db.session.add(entry)
        db.session.commit()

        fetched = db.session.get(AuditLog, entry.id)
        assert fetched.action == 'create'
        assert fetched.entity_type == 'user'
        assert fetched.entity_id == u.id
        assert fetched.after_value == {'email': 'a@test.com'}
        assert fetched.before_value is None
        assert fetched.user_id == u.id
        assert fetched.timestamp is not None

    def test_audit_log_allows_null_user_id(self, db):
        """TC-011-002: AuditLog allows null user_id for system-generated events."""
        entry = AuditLog(
            action='create',
            entity_type='team',
            entity_id=1,
            user_id=None,
        )
        db.session.add(entry)
        db.session.commit()

        fetched = db.session.get(AuditLog, entry.id)
        assert fetched.user_id is None


# ---------------------------------------------------------------------------
# TC-011-003 & TC-011-004: to_audit_dict on models
# ---------------------------------------------------------------------------

class TestToAuditDict:

    def test_user_to_audit_dict(self, db):
        u = User(email='x@test.com', full_name='X', role=UserRole.EDITOR)
        u.set_password('password1')
        db.session.add(u)
        db.session.commit()
        d = u.to_audit_dict()
        assert d['email'] == 'x@test.com'
        assert d['role'] == 'editor'
        assert d['is_archived'] is False

    def test_team_to_audit_dict(self, db, team):
        d = team.to_audit_dict()
        assert d['name'] == 'Audit Test Team'
        assert d['is_archived'] is False

    def test_product_to_audit_dict(self, db):
        p = Product(name='Audit Prod')
        db.session.add(p)
        db.session.commit()
        d = p.to_audit_dict()
        assert d['name'] == 'Audit Prod'

    def test_template_to_audit_dict(self, db, template):
        d = template.to_audit_dict()
        assert d['name'] == 'Audit Test Template'
        assert d['is_archived'] is False

    def test_repository_to_audit_dict(self, db, team, template):
        from app.services import repository_service
        repo = repository_service.create_repository(
            name='AuditRepo',
            url='https://audit.test/repo',
            team_id=team.id,
            template_id=template.id,
        )
        d = repo.to_audit_dict()
        assert d['name'] == 'AuditRepo'
        assert d['url'] == 'https://audit.test/repo'
        assert d['team_id'] == team.id


# ---------------------------------------------------------------------------
# TC-011-005 through TC-011-015: audit_service.log() called from services
# ---------------------------------------------------------------------------

class TestAuditServiceLog:

    def test_log_creates_entry(self, db):
        """audit_service.log() persists an AuditLog row."""
        entry = audit_service.log('create', 'team', 99, after={'name': 'T'})
        assert db.session.get(AuditLog, entry.id) is not None
        assert entry.action == 'create'
        assert entry.entity_type == 'team'

    def test_user_create_logs_audit(self, db):
        """TC-011-005: create_user() logs a create event."""
        before_count = AuditLog.query.count()
        user_service.create_user('new@test.com', 'New User', 'password1', 'viewer')
        after_count = AuditLog.query.count()
        assert after_count == before_count + 1
        entry = AuditLog.query.filter_by(entity_type='user', action='create').first()
        assert entry is not None
        assert entry.before_value is None
        assert entry.after_value['email'] == 'new@test.com'

    def test_user_update_logs_audit(self, db):
        """TC-011-006: update_user() logs an update event."""
        user = user_service.create_user('upd@test.com', 'Upd', 'password1', 'viewer')
        before_count = AuditLog.query.count()
        user_service.update_user(user.id, 'upd@test.com', 'Updated Name', 'viewer', user.version)
        entries = AuditLog.query.filter_by(entity_type='user', action='update').all()
        assert len(entries) >= 1

    def test_user_role_change_logs_role_change(self, db):
        """TC-011-007: update_user() with different role logs role_change event."""
        user = user_service.create_user('role@test.com', 'Role', 'password1', 'viewer')
        AuditLog.query.delete()
        db.session.commit()
        user_service.update_user(user.id, 'role@test.com', 'Role', 'editor', user.version)
        entry = AuditLog.query.filter_by(entity_type='user', action='role_change').first()
        assert entry is not None
        assert entry.before_value['role'] == 'viewer'
        assert entry.after_value['role'] == 'editor'

    def test_user_archive_logs_audit(self, db):
        """TC-011-008: archive_user() logs an archive event."""
        user = user_service.create_user('arch@test.com', 'Arch', 'password1', 'viewer')
        AuditLog.query.delete()
        db.session.commit()
        user_service.archive_user(user.id)
        entry = AuditLog.query.filter_by(entity_type='user', action='archive').first()
        assert entry is not None
        assert entry.before_value['is_archived'] is False
        assert entry.after_value['is_archived'] is True

    def test_team_create_logs_audit(self, db):
        """TC-011-009: create_team() logs a create event."""
        before = AuditLog.query.count()
        team_service.create_team('LoggedTeam')
        assert AuditLog.query.count() == before + 1
        assert AuditLog.query.filter_by(entity_type='team', action='create').first() is not None

    def test_team_update_logs_audit(self, db):
        """TC-011-010: update_team() logs an update event."""
        t = team_service.create_team('TeamToUpdate')
        AuditLog.query.delete()
        db.session.commit()
        team_service.update_team(t.id, 'UpdatedTeam', None, t.version)
        assert AuditLog.query.filter_by(entity_type='team', action='update').first() is not None

    def test_team_archive_logs_audit(self, db):
        """TC-011-011: archive_team() logs an archive event."""
        t = team_service.create_team('TeamToArchive')
        AuditLog.query.delete()
        db.session.commit()
        team_service.archive_team(t.id)
        assert AuditLog.query.filter_by(entity_type='team', action='archive').first() is not None

    def test_template_artifact_change_logs_template_change(self, db):
        """TC-011-015: add_artifact() logs a template_change event."""
        from app.models.template import ArtifactType
        t = template_service.create_template('ChangeTemplate')
        AuditLog.query.delete()
        db.session.commit()
        template_service.add_artifact(t.id, ArtifactType.document, 'New Doc')
        entry = AuditLog.query.filter_by(entity_type='template', action='template_change').first()
        assert entry is not None
        assert entry.after_value['artifact_action'] == 'add'

    def test_audit_log_entries_not_deletable(self, db):
        """TC-011-016: AuditLog model has no delete/archive methods."""
        assert not hasattr(AuditLog, 'archive')
        assert not hasattr(AuditLog, 'soft_delete')
        assert not hasattr(AuditLog, 'is_archived')


# ---------------------------------------------------------------------------
# get_audit_logs filtering
# ---------------------------------------------------------------------------

class TestGetAuditLogs:

    def _add_entry(self, db, action, entity_type, entity_id=1, user_id=None):
        e = AuditLog(action=action, entity_type=entity_type, entity_id=entity_id, user_id=user_id)
        db.session.add(e)
        db.session.commit()
        return e

    def test_filter_by_entity_type(self, db):
        self._add_entry(db, 'create', 'user')
        self._add_entry(db, 'create', 'team')
        pagination = audit_service.get_audit_logs(entity_type='user')
        assert all(e.entity_type == 'user' for e in pagination.items)

    def test_filter_by_action(self, db):
        self._add_entry(db, 'create', 'user')
        self._add_entry(db, 'archive', 'user')
        pagination = audit_service.get_audit_logs(action='create')
        assert all(e.action == 'create' for e in pagination.items)

    def test_returns_newest_first(self, db):
        """TC-011-024: entries ordered newest first."""
        e1 = self._add_entry(db, 'create', 'user', entity_id=1)
        e2 = self._add_entry(db, 'update', 'user', entity_id=2)
        pagination = audit_service.get_audit_logs()
        ids = [e.id for e in pagination.items]
        assert ids.index(e2.id) < ids.index(e1.id)

    def test_pagination(self, db):
        """TC-011-025: pagination returns correct page."""
        for i in range(60):
            e = AuditLog(action='create', entity_type='team', entity_id=i + 1)
            db.session.add(e)
        db.session.commit()
        p1 = audit_service.get_audit_logs(page=1, per_page=50)
        p2 = audit_service.get_audit_logs(page=2, per_page=50)
        assert len(p1.items) == 50
        assert len(p2.items) == 10
        assert p1.total == 60
