"""Tests for upload route."""

import pytest
from fastapi.testclient import TestClient
from io import BytesIO

from doc_generator.infrastructure.api.main import app


@pytest.fixture
def client():
    """
    Create test client.
    Invoked by: src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/generate_images.py, src/doc_generator/infrastructure/image/claude_svg.py, src/doc_generator/infrastructure/image/gemini.py, src/doc_generator/infrastructure/llm/service.py, src/doc_generator/infrastructure/observability/opik.py, tests/api/test_generate_route.py, tests/api/test_health_route.py, tests/api/test_upload_route.py
    """
    return TestClient(app)


class TestUploadRoute:
    """Test file upload endpoint."""

    def test_upload_pdf(self, client):
        """
        Invoked by: (no references found)
        """
        content = b"%PDF-1.4 fake pdf content"
        files = {"file": ("report.pdf", BytesIO(content), "application/pdf")}
        response = client.post("/api/upload", files=files)
        assert response.status_code == 200
        data = response.json()
        assert data["file_id"].startswith("f_")
        assert data["filename"] == "report.pdf"
        assert data["mime_type"] == "application/pdf"
        assert data["size"] == len(content)

    def test_upload_text(self, client):
        """
        Invoked by: (no references found)
        """
        content = b"Plain text content"
        files = {"file": ("notes.txt", BytesIO(content), "text/plain")}
        response = client.post("/api/upload", files=files)
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "notes.txt"

    def test_upload_no_file(self, client):
        """
        Invoked by: (no references found)
        """
        response = client.post("/api/upload")
        assert response.status_code == 422  # Validation error
