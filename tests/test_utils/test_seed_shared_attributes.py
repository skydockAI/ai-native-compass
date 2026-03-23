"""Tests for seed_default_shared_attributes (DI-006, REQ-034)."""

from app.models.shared_attribute import SharedAttributeDefinition
from app.utils.seed import seed_default_shared_attributes


class TestSeedDefaultSharedAttributes:

    def test_seeds_four_defaults_on_first_run(self, db):
        seed_default_shared_attributes()
        attrs = SharedAttributeDefinition.query.filter_by(is_default=True).all()
        names = {a.name for a in attrs}
        assert names == {'Name', 'Team', 'URL', 'Description'}

    def test_all_seeded_attrs_are_active(self, db):
        seed_default_shared_attributes()
        attrs = SharedAttributeDefinition.query.filter_by(is_default=True).all()
        assert all(a.is_active for a in attrs)

    def test_idempotent_on_second_run(self, db):
        seed_default_shared_attributes()
        seed_default_shared_attributes()
        count = SharedAttributeDefinition.query.filter_by(is_default=True).count()
        assert count == 4

    def test_does_not_overwrite_existing(self, db):
        # Pre-create Name with is_active=False to simulate manual change
        db.session.add(SharedAttributeDefinition(name='Name', is_default=True, is_active=False))
        db.session.commit()

        seed_default_shared_attributes()

        name_attr = SharedAttributeDefinition.query.filter_by(name='Name').first()
        # Seed should skip existing — not overwrite is_active
        assert name_attr.is_active is False
