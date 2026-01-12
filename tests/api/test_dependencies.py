"""Tests for API dependencies."""

import pytest
from fastapi import HTTPException

from doc_generator.infrastructure.api.dependencies import (
    extract_api_keys,
    get_api_key_for_provider,
    APIKeys,
)
from doc_generator.infrastructure.api.models.requests import Provider


class TestExtractAPIKeys:
    """Test API key extraction from headers."""

    def test_extract_google_key(self):
        """
        Invoked by: (no references found)
        """
        keys = extract_api_keys(
            x_google_key="AIza123",
            x_openai_key=None,
            x_anthropic_key=None,
        )
        assert keys.google == "AIza123"
        assert keys.openai is None
        assert keys.anthropic is None

    def test_extract_all_keys(self):
        """
        Invoked by: (no references found)
        """
        keys = extract_api_keys(
            x_google_key="AIza123",
            x_openai_key="sk-abc",
            x_anthropic_key="sk-ant-xyz",
        )
        assert keys.google == "AIza123"
        assert keys.openai == "sk-abc"
        assert keys.anthropic == "sk-ant-xyz"

    def test_extract_no_keys(self):
        """
        Invoked by: (no references found)
        """
        keys = extract_api_keys(
            x_google_key=None,
            x_openai_key=None,
            x_anthropic_key=None,
        )
        assert keys.google is None


class TestGetAPIKeyForProvider:
    """Test getting API key for specific provider."""

    def test_get_google_key(self):
        """
        Invoked by: (no references found)
        """
        keys = APIKeys(google="AIza123", openai=None, anthropic=None)
        key = get_api_key_for_provider(Provider.GOOGLE, keys)
        assert key == "AIza123"

    def test_missing_key_raises(self):
        """
        Invoked by: (no references found)
        """
        keys = APIKeys(google=None, openai="sk-abc", anthropic=None)
        with pytest.raises(HTTPException) as exc_info:
            get_api_key_for_provider(Provider.GOOGLE, keys)
        assert exc_info.value.status_code == 401
        assert "X-Google-Key" in exc_info.value.detail
