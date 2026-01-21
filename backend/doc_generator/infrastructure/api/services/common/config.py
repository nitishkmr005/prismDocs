"""Generation service configuration constants.

This module centralizes configuration values that were previously
scattered as magic numbers throughout the codebase.
"""

from dataclasses import dataclass, field
from typing import ClassVar


@dataclass(frozen=True)
class LLMTokenLimits:
    """Token limits for different generation steps."""

    # Question generation (Idea Canvas)
    QUESTION_GENERATION: int = 2000

    # Report/document generation
    REPORT_GENERATION: int = 4000

    # Mind map generation (needs more for complex structures)
    MINDMAP_GENERATION: int = 8000

    # Podcast script generation (needs more for dialogue)
    PODCAST_SCRIPT_GENERATION: int = 12000


@dataclass(frozen=True)
class LLMTemperatures:
    """Temperature settings for different generation tasks.

    Lower values produce more focused/deterministic output.
    Higher values produce more creative/varied output.
    """

    # Structured output (JSON, code) - low temperature for consistency
    STRUCTURED: float = 0.4

    # Mind map generation - slightly higher for variety
    MINDMAP: float = 0.4

    # Standard generation tasks
    STANDARD: float = 0.6

    # Creative/conversational tasks
    CREATIVE: float = 0.7

    # Podcast dialogue - higher for natural variation
    DIALOGUE: float = 0.7


@dataclass(frozen=True)
class ContentLimits:
    """Content size limits to prevent exceeding model context windows."""

    # Maximum characters for content extraction
    MAX_EXTRACTED_CONTENT_CHARS: int = 50_000

    # Maximum characters for report preview
    MAX_REPORT_SNIPPET_CHARS: int = 1500

    # Maximum label length for tree nodes
    MAX_NODE_LABEL_LENGTH: int = 100

    # Maximum truncated text preview
    MAX_LABEL_PREVIEW_LENGTH: int = 120

    # Maximum idea description preview
    MAX_IDEA_PREVIEW_LENGTH: int = 150


@dataclass(frozen=True)
class SessionLimits:
    """Limits for interactive sessions like Idea Canvas."""

    # Hard cap on questions in Idea Canvas session
    MAX_QUESTIONS: int = 25


@dataclass(frozen=True)
class CacheSettings:
    """Cache configuration defaults."""

    # Default time-to-live for cache entries (24 hours)
    DEFAULT_TTL_SECONDS: int = 86400

    # Maximum cache file size in bytes
    MAX_CACHE_FILE_SIZE: int = 100 * 1024 * 1024  # 100 MB


@dataclass(frozen=True)
class ModelFallbacks:
    """Model fallback configurations for different providers."""

    # Gemini models in order of preference for fallback
    GEMINI_MODELS: tuple[str, ...] = (
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-3-flash-preview",
        "gemini-3-pro-preview",
    )

    # Default models per provider
    DEFAULT_GEMINI_MODEL: str = "gemini-2.5-flash"
    DEFAULT_OPENAI_MODEL: str = "gpt-4.1-mini"
    DEFAULT_ANTHROPIC_MODEL: str = "claude-3-sonnet-20240229"

    # Image generation models
    DEFAULT_IMAGE_MODEL: str = "gemini-3-pro-image-preview"


@dataclass
class GenerationConfig:
    """Complete configuration for generation services.

    Usage:
        config = GenerationConfig()
        max_tokens = config.tokens.MINDMAP_GENERATION
        temperature = config.temperatures.STRUCTURED
    """

    tokens: LLMTokenLimits = field(default_factory=LLMTokenLimits)
    temperatures: LLMTemperatures = field(default_factory=LLMTemperatures)
    content: ContentLimits = field(default_factory=ContentLimits)
    sessions: SessionLimits = field(default_factory=SessionLimits)
    cache: CacheSettings = field(default_factory=CacheSettings)
    models: ModelFallbacks = field(default_factory=ModelFallbacks)


# Singleton instance for easy access
_config: GenerationConfig | None = None


def get_generation_config() -> GenerationConfig:
    """Get the singleton generation config instance.

    Returns:
        GenerationConfig instance with all default settings
    """
    global _config
    if _config is None:
        _config = GenerationConfig()
    return _config


# Convenience exports for direct access
TOKENS = LLMTokenLimits()
TEMPERATURES = LLMTemperatures()
CONTENT_LIMITS = ContentLimits()
SESSION_LIMITS = SessionLimits()
CACHE_SETTINGS = CacheSettings()
MODEL_FALLBACKS = ModelFallbacks()
