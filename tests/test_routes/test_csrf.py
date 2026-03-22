"""Tests for CSRF protection (TC-001-007)."""

from app import create_app


def test_csrf_protection_active():
    """TC-001-007: CSRF protection is active in non-test config."""
    app = create_app('development')
    assert app.config['WTF_CSRF_ENABLED'] is True
    assert 'csrf' in app.extensions
