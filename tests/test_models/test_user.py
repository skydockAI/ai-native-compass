"""Tests for User model (TS-003 — TC-003-010, TC-003-011, TC-003-015, TC-003-016)."""

import pytest

from app.models.user import User, UserRole


def test_user_model_has_required_columns():
    """TC-003-016: User table exposes all required columns."""
    columns = {col.name for col in User.__table__.columns}
    assert 'email' in columns
    assert 'full_name' in columns
    assert 'password_hash' in columns
    assert 'role' in columns
    assert 'is_seeded' in columns
    # BaseModel fields
    assert 'id' in columns
    assert 'is_active' in columns
    assert 'is_archived' in columns
    assert 'created_at' in columns
    assert 'updated_at' in columns
    assert 'version' in columns


def test_set_password_hashes_value(db):
    """TC-003-010: Password is stored as a hash, not plain text."""
    user = User(email='hash@example.com', full_name='Hash Test', role=UserRole.VIEWER)
    user.set_password('mypassword')
    assert user.password_hash != 'mypassword'
    assert user.password_hash.startswith('pbkdf2') or user.password_hash.startswith('scrypt')


def test_check_password_correct(db):
    """TC-003-010: check_password returns True for the correct password."""
    user = User(email='check@example.com', full_name='Check Test', role=UserRole.VIEWER)
    user.set_password('correctpass')
    assert user.check_password('correctpass') is True


def test_check_password_wrong(db):
    """TC-003-010: check_password returns False for a wrong password."""
    user = User(email='wrong@example.com', full_name='Wrong Test', role=UserRole.VIEWER)
    user.set_password('correctpass')
    assert user.check_password('wrongpass') is False


def test_set_password_too_short_raises():
    """TC-003-011: set_password raises ValueError for passwords shorter than 8 chars."""
    user = User(email='short@example.com', full_name='Short Test', role=UserRole.VIEWER)
    with pytest.raises(ValueError, match='8 characters'):
        user.set_password('short')


def test_set_password_exactly_8_chars():
    """TC-003-011: set_password accepts exactly 8-character passwords."""
    user = User(email='exact@example.com', full_name='Exact Test', role=UserRole.VIEWER)
    user.set_password('12345678')  # Should not raise
    assert user.password_hash is not None


def test_normalize_email():
    """TC-003-015: normalize_email strips whitespace and lowercases."""
    assert User.normalize_email('  User@EXAMPLE.COM  ') == 'user@example.com'
    assert User.normalize_email('TEST@Test.Org') == 'test@test.org'


def test_email_case_insensitive_login(db):
    """TC-003-015: Login works regardless of email case used at creation."""
    from app.auth.local import authenticate_user

    user = User(email=User.normalize_email('Mixed@Example.Com'), full_name='Mixed', role=UserRole.VIEWER)
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()

    result = authenticate_user('mixed@example.com', 'password123')
    assert result is not None
    assert result.id == user.id


def test_user_defaults(db):
    """User is active and not archived by default."""
    user = User(email='defaults@example.com', full_name='Defaults', role=UserRole.VIEWER)
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()

    assert user.is_active is True
    assert user.is_archived is False
    assert user.is_seeded is False


def test_user_repr():
    """User __repr__ includes the email."""
    user = User(email='repr@example.com', full_name='Repr', role=UserRole.VIEWER)
    assert 'repr@example.com' in repr(user)
