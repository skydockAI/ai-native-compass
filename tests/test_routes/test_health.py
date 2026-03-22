"""Tests for health check endpoint (TC-001-002)."""


def test_health_check_returns_200(client):
    """TC-001-002: Health check endpoint returns 200."""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
