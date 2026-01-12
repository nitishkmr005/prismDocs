"""Tests for cache service."""

import pytest
from pathlib import Path

from doc_generator.infrastructure.api.services.cache import CacheService
from doc_generator.infrastructure.api.models.requests import (
    GenerateRequest,
    OutputFormat,
    SourceCategories,
    TextSource,
)


@pytest.fixture
def cache_service(tmp_path):
    """
    Create cache service with temp directory.
    Invoked by: src/doc_generator/infrastructure/api/routes/generate.py, tests/api/test_cache_service.py
    """
    return CacheService(cache_dir=tmp_path / "cache")


class TestCacheService:
    """Test cache service."""

    def test_generate_cache_key(self, cache_service):
        """
        Invoked by: (no references found)
        """
        request = GenerateRequest(
            output_format=OutputFormat.PDF,
            sources=SourceCategories(
                primary=[TextSource(content="Test content")]
            ),
        )
        key = cache_service.generate_cache_key(request)
        assert len(key) == 64  # SHA256 hex digest

    def test_same_request_same_key(self, cache_service):
        """
        Invoked by: (no references found)
        """
        request1 = GenerateRequest(
            output_format=OutputFormat.PDF,
            sources=SourceCategories(
                primary=[TextSource(content="Test content")]
            ),
        )
        request2 = GenerateRequest(
            output_format=OutputFormat.PDF,
            sources=SourceCategories(
                primary=[TextSource(content="Test content")]
            ),
        )
        assert cache_service.generate_cache_key(request1) == cache_service.generate_cache_key(request2)

    def test_different_content_different_key(self, cache_service):
        """
        Invoked by: (no references found)
        """
        request1 = GenerateRequest(
            output_format=OutputFormat.PDF,
            sources=SourceCategories(
                primary=[TextSource(content="Content A")]
            ),
        )
        request2 = GenerateRequest(
            output_format=OutputFormat.PDF,
            sources=SourceCategories(
                primary=[TextSource(content="Content B")]
            ),
        )
        assert cache_service.generate_cache_key(request1) != cache_service.generate_cache_key(request2)

    def test_cache_miss(self, cache_service):
        """
        Invoked by: (no references found)
        """
        request = GenerateRequest(
            output_format=OutputFormat.PDF,
            sources=SourceCategories(
                primary=[TextSource(content="Test")]
            ),
        )
        result = cache_service.get(request)
        assert result is None

    def test_cache_hit(self, cache_service):
        """
        Invoked by: (no references found)
        """
        request = GenerateRequest(
            output_format=OutputFormat.PDF,
            sources=SourceCategories(
                primary=[TextSource(content="Test")]
            ),
        )
        cache_service.set(
            request=request,
            output_path=Path("/output/doc.pdf"),
            metadata={"title": "Test Doc"},
        )
        result = cache_service.get(request)
        assert result is not None
        assert result["metadata"]["title"] == "Test Doc"
