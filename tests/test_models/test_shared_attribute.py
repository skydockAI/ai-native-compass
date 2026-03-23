"""Tests for SharedAttributeDefinition and RepositorySharedAttributeValue models (DI-006)."""

from app.models.shared_attribute import RepositorySharedAttributeValue, SharedAttributeDefinition


class TestSharedAttributeDefinitionModel:

    def test_create_default_attribute(self, db):
        attr = SharedAttributeDefinition(name='Name', is_default=True, is_active=True)
        db.session.add(attr)
        db.session.commit()
        assert attr.id is not None
        assert attr.name == 'Name'
        assert attr.is_default is True
        assert attr.is_active is True
        assert attr.created_at is not None
        assert attr.updated_at is not None

    def test_create_custom_attribute(self, db):
        attr = SharedAttributeDefinition(name='Custom Field', is_default=False, is_active=True)
        db.session.add(attr)
        db.session.commit()
        assert attr.id is not None
        assert attr.is_default is False

    def test_name_uniqueness_enforced(self, db):
        from sqlalchemy.exc import IntegrityError
        db.session.add(SharedAttributeDefinition(name='Unique', is_default=False))
        db.session.commit()
        db.session.add(SharedAttributeDefinition(name='Unique', is_default=False))
        try:
            db.session.commit()
            assert False, 'Expected IntegrityError'
        except IntegrityError:
            db.session.rollback()

    def test_repr(self, db):
        attr = SharedAttributeDefinition(name='Team', is_default=True)
        assert 'Team' in repr(attr)
        assert 'default=True' in repr(attr)


class TestRepositorySharedAttributeValueModel:

    def test_create_value(self, db):
        attr = SharedAttributeDefinition(name='URL', is_default=True)
        db.session.add(attr)
        db.session.commit()

        val = RepositorySharedAttributeValue(repository_id=1, attribute_id=attr.id, value='https://example.com')
        db.session.add(val)
        db.session.commit()
        assert val.id is not None
        assert val.value == 'https://example.com'

    def test_unique_constraint_per_repo_attr(self, db):
        from sqlalchemy.exc import IntegrityError
        attr = SharedAttributeDefinition(name='Description', is_default=True)
        db.session.add(attr)
        db.session.commit()

        db.session.add(RepositorySharedAttributeValue(repository_id=1, attribute_id=attr.id, value='First'))
        db.session.commit()

        db.session.add(RepositorySharedAttributeValue(repository_id=1, attribute_id=attr.id, value='Second'))
        try:
            db.session.commit()
            assert False, 'Expected IntegrityError'
        except IntegrityError:
            db.session.rollback()

    def test_relationship_to_attribute(self, db):
        attr = SharedAttributeDefinition(name='Name', is_default=True)
        db.session.add(attr)
        db.session.commit()

        val = RepositorySharedAttributeValue(repository_id=10, attribute_id=attr.id, value='My Repo')
        db.session.add(val)
        db.session.commit()

        assert val.attribute.name == 'Name'
