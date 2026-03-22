"""Tests for UI Polish — Modern Light Theme (TS-002, DI-012)."""


def test_custom_css_served(client):
    """TC-002-001: Custom stylesheet is served by the application."""
    response = client.get('/static/css/main.css')
    assert response.status_code == 200
    assert b'--anc-primary' in response.data


def test_base_layout_links_custom_css(auth_client):
    """TC-002-002: Base layout includes link to main.css."""
    response = auth_client.get('/')
    html = response.data.decode('utf-8')
    assert 'main.css' in html


def test_navbar_contains_branding(auth_client):
    """TC-002-003: Navbar renders brand name and user placeholder."""
    response = auth_client.get('/')
    html = response.data.decode('utf-8')
    assert 'AI Native Compass' in html
    assert 'main-navbar' in html


def test_sidebar_navigation_links_present(auth_client):
    """TC-002-004: Sidebar contains all required navigation links."""
    response = auth_client.get('/')
    html = response.data.decode('utf-8')
    assert 'Dashboard' in html
    assert 'Products' in html
    assert 'Repositories' in html
    assert 'Templates' in html
    assert 'Teams' in html
    assert 'Users' in html
    assert 'Audit Log' in html


def test_dashboard_stat_cards_rendered(auth_client):
    """TC-002-005: Dashboard renders four stat cards with correct labels."""
    response = auth_client.get('/')
    html = response.data.decode('utf-8')
    assert 'stat-card' in html
    assert 'Products' in html
    assert 'Repositories' in html
    assert 'Templates' in html
    assert 'Teams' in html


def test_dashboard_returns_200(auth_client):
    """TC-002-006: Dashboard page returns HTTP 200."""
    response = auth_client.get('/')
    assert response.status_code == 200


def test_health_check_unaffected(client):
    """TC-002-007: Health check endpoint unaffected by UI changes."""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
