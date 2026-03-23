"""Tests for shared attribute service business logic (DI-006, REQ-034–036)."""

import pytest

from app.models.shared_attribute import SharedAttributeDefinition
from app.services import shared_attribute_service
from app.services.shared_attribute_service import SharedAttributeServiceError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _seed_defaults(db):
    """Seed four default shared attributes directly in DB."""
    for name in ['Name', 'Team', 'URL', 'Description']:
        db.session.add(SharedAttributeDefinition(name=name, is_default=True, is_active=True))
    db.session.commit()


# ---------------------------------------------------------------------------
# get_attributes
# ---------------------------------------------------------------------------

class TestGetAttributes:

    def test_returns_active_only_by_default(self, db):
        _seed_defaults(db)
        attr = shared_attribute_service.create_attribute('Custom')
        shared_attribute_service.deactivate_attribute(attr.id)

        results = shared_attribute_service.get_attributes()
        names = [a.name for a in results]
        assert 'Custom' not in names
        assert 'Name' in names

    def test_includes_inactive_when_requested(self, db):
        _seed_defaults(db)
        attr = shared_attribute_service.create_attribute('Custom')
        shared_attribute_service.deactivate_attribute(attr.id)

        results = shared_attribute_service.get_attributes(include_inactive=True)
        names = [a.name for a in results]
        assert 'Custom' in names

    def test_defaults_appear_first(self, db):
        _seed_defaults(db)
        shared_attribute_service.create_attribute('Zzz Custom')
        results = shared_attribute_service.get_attributes()
        # First four should be defaults (is_default=True ordered first)
        defaults = [a for a in results if a.is_default]
        customs = [a for a in results if not a.is_default]
        assert len(defaults) == 4
        assert len(customs) >= 1
        # All defaults appear before any custom
        default_indices = [results.index(a) for a in defaults]
        custom_indices = [results.index(a) for a in customs]
        assert max(default_indices) < min(custom_indices)


# ---------------------------------------------------------------------------
# create_attribute
# ---------------------------------------------------------------------------

class TestCreateAttribute:

    def test_create_custom_attribute_success(self, db):
        attr = shared_attribute_service.create_attribute('GitHub URL')
        assert attr.id is not None
        assert attr.name == 'GitHub URL'
        assert attr.is_default is False
        assert attr.is_active is True

    def test_strips_whitespace(self, db):
        attr = shared_attribute_service.create_attribute('  Padded  ')
        assert attr.name == 'Padded'

    def test_empty_name_rejected(self, db):
        with pytest.raises(SharedAttributeServiceError, match='required'):
            shared_attribute_service.create_attribute('')

    def test_whitespace_name_rejected(self, db):
        with pytest.raises(SharedAttributeServiceError, match='required'):
            shared_attribute_service.create_attribute('   ')

    def test_duplicate_name_rejected(self, db):
        shared_attribute_service.create_attribute('Alpha')
        with pytest.raises(SharedAttributeServiceError, match='already exists'):
            shared_attribute_service.create_attribute('Alpha')

    def test_duplicate_name_case_insensitive(self, db):
        shared_attribute_service.create_attribute('Alpha')
        with pytest.raises(SharedAttributeServiceError, match='already exists'):
            shared_attribute_service.create_attribute('ALPHA')


# ---------------------------------------------------------------------------
# update_attribute
# ---------------------------------------------------------------------------

class TestUpdateAttribute:

    def test_rename_custom_attribute(self, db):
        attr = shared_attribute_service.create_attribute('Old Name')
        updated = shared_attribute_service.update_attribute(attr.id, 'New Name')
        assert updated.name == 'New Name'

    def test_rename_default_attribute_rejected(self, db):
        _seed_defaults(db)
        default = SharedAttributeDefinition.query.filter_by(name='Name').first()
        with pytest.raises(SharedAttributeServiceError, match='cannot be renamed'):
            shared_attribute_service.update_attribute(default.id, 'Renamed')

    def test_rename_to_existing_name_rejected(self, db):
        a1 = shared_attribute_service.create_attribute('Alpha')
        shared_attribute_service.create_attribute('Beta')
        with pytest.raises(SharedAttributeServiceError, match='already exists'):
            shared_attribute_service.update_attribute(a1.id, 'Beta')

    def test_not_found_raises(self, db):
        with pytest.raises(SharedAttributeServiceError, match='not found'):
            shared_attribute_service.update_attribute(9999, 'Whatever')


# ---------------------------------------------------------------------------
# deactivate_attribute
# ---------------------------------------------------------------------------

class TestDeactivateAttribute:

    def test_deactivate_custom_attribute(self, db):
        attr = shared_attribute_service.create_attribute('Custom')
        deactivated = shared_attribute_service.deactivate_attribute(attr.id)
        assert deactivated.is_active is False

    def test_deactivate_default_rejected(self, db):
        _seed_defaults(db)
        default = SharedAttributeDefinition.query.filter_by(name='Team').first()
        with pytest.raises(SharedAttributeServiceError, match='cannot be deactivated'):
            shared_attribute_service.deactivate_attribute(default.id)

    def test_deactivate_already_inactive_rejected(self, db):
        attr = shared_attribute_service.create_attribute('Custom')
        shared_attribute_service.deactivate_attribute(attr.id)
        with pytest.raises(SharedAttributeServiceError, match='already inactive'):
            shared_attribute_service.deactivate_attribute(attr.id)

    def test_not_found_raises(self, db):
        with pytest.raises(SharedAttributeServiceError, match='not found'):
            shared_attribute_service.deactivate_attribute(9999)


# ---------------------------------------------------------------------------
# reactivate_attribute
# ---------------------------------------------------------------------------

class TestReactivateAttribute:

    def test_reactivate_inactive_custom_attribute(self, db):
        attr = shared_attribute_service.create_attribute('Custom')
        shared_attribute_service.deactivate_attribute(attr.id)
        reactivated = shared_attribute_service.reactivate_attribute(attr.id)
        assert reactivated.is_active is True

    def test_reactivate_already_active_rejected(self, db):
        attr = shared_attribute_service.create_attribute('Custom')
        with pytest.raises(SharedAttributeServiceError, match='already active'):
            shared_attribute_service.reactivate_attribute(attr.id)

    def test_not_found_raises(self, db):
        with pytest.raises(SharedAttributeServiceError, match='not found'):
            shared_attribute_service.reactivate_attribute(9999)
