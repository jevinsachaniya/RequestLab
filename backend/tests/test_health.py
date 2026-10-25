"""Tests for root and health check endpoints."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Verify the root endpoint responds with status 200 and expected metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["docs"] == "/docs"
    assert data["health"] == "/api/v1/health"


def test_health_check_endpoint():
    """Verify the /api/v1/health endpoint responds with status 200 and healthy status."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "RequestLab"
    assert "version" in data
    assert "environment" in data


def test_swagger_documentation_accessible():
    """Verify that Swagger UI (/docs) and OpenAPI schema (/api/v1/openapi.json) are accessible."""
    docs_response = client.get("/docs")
    assert docs_response.status_code == 200
    assert "swagger-ui" in docs_response.text.lower()

    openapi_response = client.get("/api/v1/openapi.json")
    assert openapi_response.status_code == 200
    openapi_data = openapi_response.json()
    assert openapi_data["info"]["title"] == "RequestLab"
    assert "/api/v1/health" in openapi_data["paths"]


