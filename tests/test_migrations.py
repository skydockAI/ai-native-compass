"""Tests for migration infrastructure (TC-001-010)."""

import os


def test_migrations_directory_exists():
    """TC-001-010: Alembic migration infrastructure exists."""
    migrations_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'migrations')
    assert os.path.isdir(migrations_dir)
    assert os.path.isdir(os.path.join(migrations_dir, 'versions'))


def test_alembic_config_exists():
    """TC-001-010: Alembic configuration exists."""
    migrations_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'migrations')
    assert os.path.isfile(os.path.join(migrations_dir, 'alembic.ini'))


def test_database_connection(db):
    """TC-001-003: Database connection works."""
    result = db.session.execute(db.text('SELECT 1')).scalar()
    assert result == 1
