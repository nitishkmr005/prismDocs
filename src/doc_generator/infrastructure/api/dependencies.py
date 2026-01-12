"""FastAPI dependencies for API routes."""

from dataclasses import dataclass
from typing import Optional

from fastapi import Header, HTTPException

from .schemas.requests import Provider


@dataclass
class APIKeys:
    """Container for API keys from headers."""

    google: Optional[str] = None
    openai: Optional[str] = None
    anthropic: Optional[str] = None


def extract_api_keys(
    x_google_key: Optional[str] = Header(None, alias="X-Google-Key"),
    x_openai_key: Optional[str] = Header(None, alias="X-OpenAI-Key"),
    x_anthropic_key: Optional[str] = Header(None, alias="X-Anthropic-Key"),
) -> APIKeys:
    """Extract API keys from request headers.

    Args:
        x_google_key: Google/Gemini API key
        x_openai_key: OpenAI API key
        x_anthropic_key: Anthropic/Claude API key

    Returns:
        APIKeys container with extracted keys
    Invoked by: src/doc_generator/infrastructure/api/routes/generate.py, tests/api/test_dependencies.py
    """
    return APIKeys(
        google=x_google_key,
        openai=x_openai_key,
        anthropic=x_anthropic_key,
    )


def get_api_key_for_provider(provider: Provider, keys: APIKeys) -> str:
    """Get API key for the specified provider.

    Args:
        provider: The LLM provider
        keys: Extracted API keys

    Returns:
        The API key for the provider

    Raises:
        HTTPException: If the required API key is missing
    Invoked by: src/doc_generator/infrastructure/api/routes/generate.py, tests/api/test_dependencies.py
    """
    key_map = {
        Provider.GEMINI: (keys.google, "X-Google-Key"),
        Provider.GOOGLE: (keys.google, "X-Google-Key"),
        Provider.OPENAI: (keys.openai, "X-OpenAI-Key"),
        Provider.ANTHROPIC: (keys.anthropic, "X-Anthropic-Key"),
    }

    key, header_name = key_map[provider]

    if not key:
        raise HTTPException(
            status_code=401,
            detail=f"Missing required header: {header_name}",
        )

    return key
