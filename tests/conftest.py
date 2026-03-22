import pytest

from app import create_app
from app.extensions import db as _db


@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    app = create_app('testing')
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture(scope='function')
def db(app):
    """Create a fresh database session for each test."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.rollback()
        _db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture(scope='function')
def test_user(db):
    """Create and persist a basic viewer user for authentication tests."""
    from app.models.user import User, UserRole

    user = User(
        email='testuser@example.com',
        full_name='Test User',
        role=UserRole.VIEWER,
    )
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture(scope='function')
def auth_client(client, db, test_user):  # noqa: ARG001 — fixtures used for side-effects
    """Return a test client that is logged in as *test_user*."""
    client.post(
        '/login',
        data={'email': 'testuser@example.com', 'password': 'password123'},
        follow_redirects=False,
    )
    return client
