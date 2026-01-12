"""Tests for generation service."""

import pytest

from doc_generator.infrastructure.api.services.generation import GenerationService
from doc_generator.infrastructure.api.models.requests import (
    GenerateRequest,
    OutputFormat,
    SourceCategories,
    TextSource,
)
from doc_generator.infrastructure.api.models.responses import GenerationStatus


class TestGenerationService:
    """Test generation service."""

    @pytest.fixture
    def service(self, tmp_path):
        """
        Create generation service.
        Invoked by: tests/api/test_generation_service.py
        """
        return GenerationService(output_dir=tmp_path)

    @pytest.mark.asyncio
    async def test_progress_callback(self, service):
        """
        Test that progress events are yielded.
        Invoked by: (no references found)
        """
        events = []

        request = GenerateRequest(
            output_format=OutputFormat.PDF,
            sources=SourceCategories(
                primary=[TextSource(content="Test content for PDF generation")]
            ),
        )
        async for event in service.generate(
            request=request,
            api_key="test-key",
        ):
            events.append(event)
            # Stop after first few events for test
            if len(events) >= 2:
                break

        assert len(events) >= 1
        assert events[0].status == GenerationStatus.PARSING
