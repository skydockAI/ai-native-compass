"""Tests for base model mixin (TC-001-004, TC-001-005, TC-001-006)."""

from app.extensions import db
from app.models import BaseModel


class SampleModel(BaseModel):
    """Concrete model for testing the abstract base mixin."""
    __tablename__ = 'test_sample'
    name = db.Column(db.String(100), nullable=False)


def test_base_model_has_required_fields():
    """TC-001-004: Base model mixin has required fields."""
    columns = {col.name for col in SampleModel.__table__.columns}
    assert 'id' in columns
    assert 'is_active' in columns
    assert 'is_archived' in columns
    assert 'created_at' in columns
    assert 'updated_at' in columns
    assert 'version' in columns


def test_base_model_field_types():
    """TC-001-004: Base model fields have correct types."""
    columns = {col.name: col for col in SampleModel.__table__.columns}
    assert columns['id'].primary_key
    assert str(columns['is_active'].type) == 'BOOLEAN'
    assert str(columns['is_archived'].type) == 'BOOLEAN'
    assert str(columns['version'].type) == 'INTEGER'


def test_soft_delete_defaults(db):
    """TC-001-005: Soft delete defaults are correct."""
    db.create_all()
    sample = SampleModel(name='test')
    db.session.add(sample)
    db.session.commit()

    assert sample.is_active is True
    assert sample.is_archived is False


def test_version_default(db):
    """TC-001-006: Optimistic locking version field defaults to 1."""
    db.create_all()
    sample = SampleModel(name='test')
    db.session.add(sample)
    db.session.commit()

    assert sample.version == 1


def test_timestamps_are_set(db):
    """TC-001-004: Timestamps are set on creation."""
    db.create_all()
    sample = SampleModel(name='test')
    db.session.add(sample)
    db.session.commit()

    assert sample.created_at is not None
    assert sample.updated_at is not None
