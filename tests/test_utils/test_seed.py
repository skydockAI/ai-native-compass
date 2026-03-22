"""Tests for admin seeding utility (TS-003 — TC-003-012 to TC-003-014, TC-003-017)."""

import os
from unittest.mock import patch

from app.models.user import User, UserRole
from app.utils.seed import seed_admins


def test_seed_creates_admin_user(db):
    """TC-003-012: seed_admins creates an admin user from ADMIN_SEEDS."""
    with patch.dict(os.environ, {'ADMIN_SEEDS': 'seedadmin@example.com:securepass123'}):
        seed_admins()

    user = User.query.filter_by(email='seedadmin@example.com').first()
    assert user is not None
    assert user.role == UserRole.ADMIN


def test_seed_sets_is_seeded_flag(db):
    """TC-003-017: Seeded users have is_seeded=True."""
    with patch.dict(os.environ, {'ADMIN_SEEDS': 'flagged@example.com:securepass123'}):
        seed_admins()

    user = User.query.filter_by(email='flagged@example.com').first()
    assert user is not None
    assert user.is_seeded is True


def test_seed_is_idempotent(db):
    """TC-003-013: Running seed_admins twice does not create duplicate users."""
    with patch.dict(os.environ, {'ADMIN_SEEDS': 'idem@example.com:securepass123'}):
        seed_admins()
        seed_admins()

    count = User.query.filter_by(email='idem@example.com').count()
    assert count == 1


def test_seed_skips_short_password(db):
    """TC-003-014: Entries with passwords shorter than 8 chars are skipped."""
    with patch.dict(os.environ, {'ADMIN_SEEDS': 'shortpw@example.com:short'}):
        seed_admins()

    user = User.query.filter_by(email='shortpw@example.com').first()
    assert user is None


def test_seed_no_env_var(db):
    """seed_admins does nothing when ADMIN_SEEDS is not set."""
    env = {k: v for k, v in os.environ.items() if k != 'ADMIN_SEEDS'}
    with patch.dict(os.environ, env, clear=True):
        seed_admins()  # Should not raise

    assert User.query.count() == 0


def test_seed_default_full_name_from_email(db):
    """Seeded user full_name defaults to the local part of the email address."""
    with patch.dict(os.environ, {'ADMIN_SEEDS': 'johndoe@example.com:securepass123'}):
        seed_admins()

    user = User.query.filter_by(email='johndoe@example.com').first()
    assert user is not None
    assert user.full_name == 'johndoe'


def test_seed_normalises_email(db):
    """Emails are stored in lowercase regardless of case in ADMIN_SEEDS."""
    with patch.dict(os.environ, {'ADMIN_SEEDS': 'UPPER@EXAMPLE.COM:securepass123'}):
        seed_admins()

    user = User.query.filter_by(email='upper@example.com').first()
    assert user is not None


def test_seed_multiple_admins(db):
    """Multiple comma-separated entries are all created."""
    with patch.dict(os.environ, {
        'ADMIN_SEEDS': 'multi1@example.com:securepass123,multi2@example.com:securepass456'
    }):
        seed_admins()

    assert User.query.filter_by(email='multi1@example.com').count() == 1
    assert User.query.filter_by(email='multi2@example.com').count() == 1
