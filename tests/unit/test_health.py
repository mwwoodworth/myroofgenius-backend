"""
Unit Tests - Health Check
Fast, isolated tests for health endpoints
"""

import pytest

@pytest.mark.unit
def test_health_endpoint_structure(test_client):
    """Test health endpoint returns correct structure"""
    response = test_client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "version" in data
    assert data["status"] == "healthy"

@pytest.mark.unit
def test_health_endpoint_performance(test_client, timer):
    """Test health endpoint responds quickly"""
    timer.start()
    response = test_client.get("/health")
    timer.stop()

    assert response.status_code == 200
    assert timer.elapsed < 0.1  # Should respond in < 100ms

@pytest.mark.unit
@pytest.mark.ci
def test_health_database_status(test_client):
    """Test health endpoint shows database status"""
    response = test_client.get("/health")
    data = response.json()

    assert "database" in data
    # Database should be connected in test environment

@pytest.mark.unit
def test_health_timestamp(test_client):
    """Test health endpoint includes timestamp"""
    response = test_client.get("/health")
    data = response.json()

    assert "timestamp" in data
    assert isinstance(data["timestamp"], str)
