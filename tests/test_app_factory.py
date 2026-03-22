"""Tests for Flask application factory (TC-001-001)."""

from app import create_app


def test_create_app_returns_flask_instance():
    """TC-001-001: App factory creates application successfully."""
    app = create_app('testing')
    assert app is not None
    assert app.testing is True


def test_create_app_loads_testing_config():
    """TC-001-001: App factory loads correct configuration."""
    app = create_app('testing')
    assert app.config['TESTING'] is True
    assert app.config['WTF_CSRF_ENABLED'] is False
    assert 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']


def test_create_app_development_config():
    """TC-001-001: App factory loads development configuration."""
    app = create_app('development')
    assert app.config['DEBUG'] is True


def test_create_app_extensions_initialized(app):
    """TC-001-001: Extensions are initialized."""
    assert 'sqlalchemy' in app.extensions
    assert 'migrate' in app.extensions
    assert 'csrf' in app.extensions
