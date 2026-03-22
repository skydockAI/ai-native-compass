"""Tests for dashboard route (TC-001-009)."""


def test_dashboard_returns_200(auth_client):
    """TC-001-009: Dashboard route returns 200 for authenticated users."""
    response = auth_client.get('/')
    assert response.status_code == 200


def test_dashboard_renders_html(auth_client):
    """TC-001-008: Base template renders with expected elements."""
    response = auth_client.get('/')
    html = response.data.decode('utf-8')

    # Bootstrap 5 CSS is loaded
    assert 'bootstrap' in html

    # HTMX is loaded
    assert 'htmx.org' in html

    # Sidebar navigation links are present
    assert 'Dashboard' in html
    assert 'Products' in html
    assert 'Repositories' in html
    assert 'Templates' in html
    assert 'Teams' in html
    assert 'Users' in html
    assert 'Audit Log' in html

    # Navbar is present
    assert 'AI Native Compass' in html
