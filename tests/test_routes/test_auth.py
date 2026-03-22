"""Tests for authentication routes (TS-003 — TC-003-001 to TC-003-009)."""

from app.models.user import User, UserRole


def test_login_page_loads(client):
    """TC-003-001: GET /login returns 200 with sign-in form."""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Sign In' in response.data


def test_login_success_redirects_to_dashboard(client, db, test_user):
    """TC-003-002: Valid credentials redirect to dashboard."""
    response = client.post(
        '/login',
        data={'email': 'testuser@example.com', 'password': 'password123'},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b'Dashboard' in response.data


def test_login_wrong_password(client, db, test_user):
    """TC-003-003: Wrong password shows generic error without revealing which field."""
    response = client.post(
        '/login',
        data={'email': 'testuser@example.com', 'password': 'wrongpassword'},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b'Invalid email or password' in response.data


def test_login_unknown_email(client, db):
    """TC-003-004: Unknown email shows same generic error."""
    response = client.post(
        '/login',
        data={'email': 'nobody@example.com', 'password': 'password123'},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b'Invalid email or password' in response.data


def test_login_inactive_user_rejected(client, db):
    """TC-003-005: Inactive user cannot log in."""
    user = User(email='inactive@example.com', full_name='Inactive', role=UserRole.VIEWER)
    user.set_password('password123')
    user.is_active = False
    db.session.add(user)
    db.session.commit()

    response = client.post(
        '/login',
        data={'email': 'inactive@example.com', 'password': 'password123'},
        follow_redirects=True,
    )
    assert b'Invalid email or password' in response.data


def test_login_archived_user_rejected(client, db):
    """TC-003-006: Archived user cannot log in."""
    user = User(email='archived@example.com', full_name='Archived', role=UserRole.VIEWER)
    user.set_password('password123')
    user.is_archived = True
    db.session.add(user)
    db.session.commit()

    response = client.post(
        '/login',
        data={'email': 'archived@example.com', 'password': 'password123'},
        follow_redirects=True,
    )
    assert b'Invalid email or password' in response.data


def test_logout_redirects_to_login(auth_client):
    """TC-003-007: Logout clears session and redirects to login page."""
    response = auth_client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'Sign In' in response.data


def test_dashboard_requires_authentication(client):
    """TC-003-008: Unauthenticated request to / redirects to /login."""
    response = client.get('/')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_active_session_invalidated_when_user_archived(client, db, test_user):
    """TC-003-009: Session is invalidated immediately when user is archived."""
    # Log in
    client.post(
        '/login',
        data={'email': 'testuser@example.com', 'password': 'password123'},
    )

    # Archive the user directly in the DB
    test_user.is_archived = True
    db.session.commit()

    # Next request should redirect to login
    response = client.get('/', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_active_session_invalidated_when_user_deactivated(client, db, test_user):
    """TC-003-009 (variant): Session is invalidated when user is deactivated."""
    client.post(
        '/login',
        data={'email': 'testuser@example.com', 'password': 'password123'},
    )

    test_user.is_active = False
    db.session.commit()

    response = client.get('/', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_authenticated_user_redirected_away_from_login(auth_client):
    """Already authenticated users are redirected from /login to the dashboard."""
    response = auth_client.get('/login', follow_redirects=False)
    assert response.status_code == 302
    assert '/' in response.headers['Location']
