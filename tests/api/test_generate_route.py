"""Tests for generate route."""

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


class TestGenerateRoute:
    """Test document generation endpoint."""

    def test_generate_requires_api_key(self, client):
        """
        Test that generate endpoint requires API key.
        Invoked by: (no references found)
        """
        response = client.post(
            "/api/generate",
            json={
                "output_format": "pdf",
                "sources": {
                    "primary": [{"type": "text", "content": "Test content"}]
                },
            },
        )
        # Should fail without API key
        assert response.status_code == 401

    def test_generate_with_google_key(self, client):
        """
        Test generate with Google API key returns SSE stream.
        Invoked by: (no references found)
        """
        response = client.post(
            "/api/generate",
            headers={"X-Google-Key": "test-google-key"},
            json={
                "output_format": "pdf",
                "sources": {
                    "primary": [{"type": "text", "content": "Test content"}]
                },
            },
        )
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

    def test_generate_pptx_format(self, client):
        """
        Test generate with PPTX format.
        Invoked by: (no references found)
        """
        response = client.post(
            "/api/generate",
            headers={"X-Google-Key": "test-google-key"},
            json={
                "output_format": "pptx",
                "sources": {
                    "primary": [{"type": "text", "content": "Test presentation content"}]
                },
                "preferences": {
                    "slides": 5,
                },
            },
        )
        assert response.status_code == 200

    def test_generate_with_openai_provider(self, client):
        """
        Test generate with OpenAI provider.
        Invoked by: (no references found)
        """
        response = client.post(
            "/api/generate",
            headers={"X-OpenAI-Key": "test-openai-key"},
            json={
                "output_format": "pdf",
                "sources": {
                    "primary": [{"type": "text", "content": "Test content"}]
                },
                "provider": "openai",
            },
        )
        assert response.status_code == 200

    def test_generate_missing_provider_key(self, client):
        """
        Test generate fails when provider key is missing.
        Invoked by: (no references found)
        """
        response = client.post(
            "/api/generate",
            headers={"X-Google-Key": "test-google-key"},
            json={
                "output_format": "pdf",
                "sources": {
                    "primary": [{"type": "text", "content": "Test content"}]
                },
                "provider": "openai",  # Requesting OpenAI but only Google key provided
            },
        )
        assert response.status_code == 401

    def test_generate_with_cache_reuse(self, client):
        """
        Test generate with cache reuse enabled.
        Invoked by: (no references found)
        """
        response = client.post(
            "/api/generate",
            headers={"X-Google-Key": "test-google-key"},
            json={
                "output_format": "pdf",
                "sources": {
                    "primary": [{"type": "text", "content": "Cache test content"}]
                },
                "cache": {
                    "reuse": True,
                },
            },
        )
        assert response.status_code == 200

    def test_generate_with_multiple_sources(self, client):
        """
        Test generate with multiple source types.
        Invoked by: (no references found)
        """
        response = client.post(
            "/api/generate",
            headers={"X-Google-Key": "test-google-key"},
            json={
                "output_format": "pdf",
                "sources": {
                    "primary": [
                        {"type": "text", "content": "Primary content"},
                    ],
                    "supporting": [
                        {"type": "text", "content": "Supporting content"},
                    ],
                    "reference": [
                        {"type": "url", "url": "https://example.com"},
                    ],
                },
            },
        )
        assert response.status_code == 200
