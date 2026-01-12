"""Tests for API request models."""

import pytest
from pydantic import ValidationError

from doc_generator.infrastructure.api.models.requests import (
    OutputFormat,
    Provider,
    Audience,
    ImageStyle,
    FileSource,
    UrlSource,
    TextSource,
    SourceCategories,
    Preferences,
    CacheOptions,
    GenerateRequest,
)


class TestSourceTypes:
    def test_file_source_valid(self):
        """
        Invoked by: (no references found)
        """
        source = FileSource(file_id="f_abc123")
        assert source.type == "file"
        assert source.file_id == "f_abc123"

    def test_url_source_valid(self):
        """
        Invoked by: (no references found)
        """
        source = UrlSource(url="https://example.com/article")
        assert source.type == "url"
        assert source.url == "https://example.com/article"

    def test_text_source_valid(self):
        """
        Invoked by: (no references found)
        """
        source = TextSource(content="Some pasted content")
        assert source.type == "text"
        assert source.content == "Some pasted content"


class TestSourceCategories:
    def test_empty_categories(self):
        """
        Invoked by: (no references found)
        """
        categories = SourceCategories()
        assert categories.primary == []
        assert categories.supporting == []
        assert categories.other == {}

    def test_mixed_sources(self):
        """
        Invoked by: (no references found)
        """
        categories = SourceCategories(
            primary=[
                FileSource(file_id="f_1"),
                UrlSource(url="https://example.com"),
            ],
            supporting=[
                TextSource(content="Notes here"),
            ],
            other={
                "custom": [FileSource(file_id="f_2")],
            },
        )
        assert len(categories.primary) == 2
        assert len(categories.supporting) == 1
        assert "custom" in categories.other


class TestPreferences:
    def test_defaults(self):
        """
        Invoked by: (no references found)
        """
        prefs = Preferences()
        assert prefs.audience == Audience.TECHNICAL
        assert prefs.image_style == ImageStyle.AUTO
        assert prefs.temperature == 0.4
        assert prefs.max_tokens == 8000
        assert prefs.max_slides == 10
        assert prefs.max_summary_points == 5

    def test_temperature_bounds(self):
        """
        Invoked by: (no references found)
        """
        with pytest.raises(ValidationError):
            Preferences(temperature=1.5)
        with pytest.raises(ValidationError):
            Preferences(temperature=-0.1)

    def test_max_tokens_bounds(self):
        """
        Invoked by: (no references found)
        """
        with pytest.raises(ValidationError):
            Preferences(max_tokens=50)
        with pytest.raises(ValidationError):
            Preferences(max_tokens=50000)


class TestGenerateRequest:
    def test_minimal_request(self):
        """
        Invoked by: (no references found)
        """
        request = GenerateRequest(
            output_format=OutputFormat.PDF,
            sources=SourceCategories(
                primary=[TextSource(content="Test content")]
            ),
        )
        assert request.provider == Provider.GOOGLE
        assert request.model == "gemini-3-pro-preview"
        assert request.image_model == "gemini-3-pro-image-preview"
        assert request.cache.reuse is True

    def test_full_request(self):
        """
        Invoked by: (no references found)
        """
        request = GenerateRequest(
            output_format=OutputFormat.PPTX,
            sources=SourceCategories(
                primary=[FileSource(file_id="f_1")],
                supporting=[UrlSource(url="https://example.com")],
            ),
            provider=Provider.OPENAI,
            model="gpt-4o",
            image_model="dall-e-3",
            preferences=Preferences(
                audience=Audience.EXECUTIVE,
                image_style=ImageStyle.CORPORATE,
                temperature=0.7,
                max_slides=15,
            ),
            cache=CacheOptions(reuse=False),
        )
        assert request.provider == Provider.OPENAI
        assert request.preferences.audience == Audience.EXECUTIVE
