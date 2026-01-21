"""Common utilities shared across API services.

This module provides shared functionality for:
- API key configuration across providers
- Content extraction from multiple source types
- JSON parsing with robust error handling
- LLM calls with automatic model fallback
- Singleton pattern implementation
- Centralized configuration constants
"""

from .api_key_manager import configure_api_key, APIKeyManager, normalize_provider_name
from .content_extractor import BaseContentExtractor
from .json_utils import extract_json_from_text, safe_json_parse, clean_markdown_json
from .llm_caller import LLMCaller
from .singleton import SingletonMeta, get_or_create_singleton
from .config import (
    GenerationConfig,
    get_generation_config,
    TOKENS,
    TEMPERATURES,
    CONTENT_LIMITS,
    SESSION_LIMITS,
    CACHE_SETTINGS,
    MODEL_FALLBACKS,
)

__all__ = [
    # API key management
    "configure_api_key",
    "APIKeyManager",
    "normalize_provider_name",
    # Content extraction
    "BaseContentExtractor",
    # JSON utilities
    "extract_json_from_text",
    "safe_json_parse",
    "clean_markdown_json",
    # LLM utilities
    "LLMCaller",
    # Singleton utilities
    "SingletonMeta",
    "get_or_create_singleton",
    # Configuration
    "GenerationConfig",
    "get_generation_config",
    "TOKENS",
    "TEMPERATURES",
    "CONTENT_LIMITS",
    "SESSION_LIMITS",
    "CACHE_SETTINGS",
    "MODEL_FALLBACKS",
]
