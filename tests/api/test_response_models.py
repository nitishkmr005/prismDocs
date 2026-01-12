"""Tests for API response models."""

from doc_generator.infrastructure.api.models.responses import (
    CacheHitEvent,
    CompleteEvent,
    CompletionMetadata,
    ErrorEvent,
    GenerationStatus,
    HealthResponse,
    ProgressEvent,
    UploadResponse,
)


class TestProgressEvent:
    def test_basic_progress(self):
        """
        Invoked by: (no references found)
        """
        event = ProgressEvent(
            status=GenerationStatus.PARSING,
            progress=25,
            message="Parsing sources...",
        )
        assert event.status == GenerationStatus.PARSING
        assert event.progress == 25
        assert event.message == "Parsing sources..."

    def test_progress_defaults(self):
        """
        Invoked by: (no references found)
        """
        event = ProgressEvent(
            status=GenerationStatus.TRANSFORMING,
            progress=50,
        )
        assert event.message == ""


class TestCompleteEvent:
    def test_complete_event(self):
        """
        Invoked by: (no references found)
        """
        event = CompleteEvent(
            download_url="https://storage.example.com/doc.pdf",
            expires_in=3600,
            metadata=CompletionMetadata(
                title="Test Document",
                pages=12,
                images_generated=5,
            ),
        )
        assert event.status == GenerationStatus.COMPLETE
        assert event.progress == 100
        assert event.metadata.pages == 12


class TestCacheHitEvent:
    def test_cache_hit_event(self):
        """
        Invoked by: (no references found)
        """
        event = CacheHitEvent(
            download_url="https://storage.example.com/cached.pdf",
            cached_at="2024-01-15T10:30:00Z",
        )
        assert event.status == GenerationStatus.CACHE_HIT
        assert event.progress == 100
        assert event.download_url == "https://storage.example.com/cached.pdf"
        assert event.expires_in == 3600


class TestErrorEvent:
    def test_error_event(self):
        """
        Invoked by: (no references found)
        """
        event = ErrorEvent(
            error="Invalid API key",
            code="AUTH_ERROR",
        )
        assert event.status == GenerationStatus.ERROR
        assert event.error == "Invalid API key"


class TestUploadResponse:
    def test_upload_response(self):
        """
        Invoked by: (no references found)
        """
        response = UploadResponse(
            file_id="f_abc123",
            filename="report.pdf",
            size=245000,
            mime_type="application/pdf",
        )
        assert response.file_id == "f_abc123"
        assert response.expires_in == 3600


class TestHealthResponse:
    def test_health_response(self):
        """
        Invoked by: (no references found)
        """
        response = HealthResponse(version="0.1.0")
        assert response.status == "healthy"
        assert response.version == "0.1.0"
