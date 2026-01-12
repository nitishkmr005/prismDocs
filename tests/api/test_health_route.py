"""Tests for health route."""

import pytest
from fastapi.testclient import TestClient

from doc_generator.infrastructure.api.main import app


@pytest.fixture
def client():
    """
    Create test client.
    Invoked by: src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/generate_images.py, src/doc_generator/infrastructure/image/claude_svg.py, src/doc_generator/infrastructure/image/gemini.py, src/doc_generator/infrastructure/llm/service.py, src/doc_generator/infrastructure/observability/opik.py, tests/api/test_generate_route.py, tests/api/test_health_route.py, tests/api/test_upload_route.py
    """
    return TestClient(app)


class TestHealthRoute:
    """Test health check endpoint."""

    def test_health_check(self, client):
        """
        Invoked by: (no references found)
        """
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
