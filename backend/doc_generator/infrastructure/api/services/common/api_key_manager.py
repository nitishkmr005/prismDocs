"""Centralized API key configuration.

This module provides a single source of truth for configuring LLM provider API keys,
eliminating the duplicated `_configure_api_key` methods scattered across services.
"""

import os
from typing import Literal

from loguru import logger


# Supported provider names
ProviderName = Literal["gemini", "google", "openai", "anthropic"]


# Mapping of provider names to environment variable names
_PROVIDER_ENV_VAR_MAP: dict[str, list[str]] = {
    "gemini": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
    "google": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
    "openai": ["OPENAI_API_KEY"],
    "anthropic": ["ANTHROPIC_API_KEY"],
}


def configure_api_key(provider: str, api_key: str) -> None:
    """Configure API key in environment for the specified provider.

    This function sets the appropriate environment variables for the given
    LLM provider, ensuring the API key is available for subsequent API calls.

    Args:
        provider: Provider name (gemini, google, openai, anthropic)
        api_key: The API key value to set

    Example:
        >>> configure_api_key("gemini", "your-api-key")
        >>> # Now GEMINI_API_KEY and GOOGLE_API_KEY are set
    """
    env_vars = _PROVIDER_ENV_VAR_MAP.get(provider.lower(), [])

    if not env_vars:
        logger.warning(f"Unknown provider '{provider}', API key not configured")
        return

    for env_var in env_vars:
        os.environ[env_var] = api_key

    logger.debug(f"Configured API key for provider: {provider}")


class APIKeyManager:
    """Context manager for safely setting and restoring API keys.

    Useful for scenarios where you want to temporarily set an API key
    and restore the previous state after the operation.

    Example:
        >>> with APIKeyManager("gemini", "temp-api-key"):
        ...     # API key is set here
        ...     make_api_call()
        >>> # Original state restored
    """

    def __init__(self, provider: str, api_key: str):
        """Initialize the API key manager.

        Args:
            provider: Provider name (gemini, google, openai, anthropic)
            api_key: The API key to set temporarily
        """
        self.provider = provider.lower()
        self.api_key = api_key
        self._original_values: dict[str, str | None] = {}

    def __enter__(self) -> "APIKeyManager":
        """Set the API key and save original values."""
        env_vars = _PROVIDER_ENV_VAR_MAP.get(self.provider, [])

        # Save original values
        for env_var in env_vars:
            self._original_values[env_var] = os.environ.get(env_var)

        # Set new values
        configure_api_key(self.provider, self.api_key)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Restore original API key values."""
        for env_var, original_value in self._original_values.items():
            if original_value is None:
                os.environ.pop(env_var, None)
            else:
                os.environ[env_var] = original_value


def normalize_provider_name(provider: str) -> str:
    """Normalize provider name to standard format.

    Converts 'google' to 'gemini' for consistency.

    Args:
        provider: Raw provider name

    Returns:
        Normalized provider name
    """
    provider_lower = provider.lower()
    if provider_lower == "google":
        return "gemini"
    return provider_lower
