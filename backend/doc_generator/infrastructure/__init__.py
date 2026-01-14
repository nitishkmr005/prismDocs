"""
Infrastructure layer for document generator.

This layer contains external dependencies and adapters:
- api/        - FastAPI HTTP layer (routes, schemas, dependencies)
- llm/        - LLM providers (Gemini, OpenAI, Claude)
- generators/ - Output generators (PDF, PPTX)
- parsers/    - Content parsers (Docling, Markitdown)
- image/      - Image generation (Gemini, SVG)
- storage/    - File storage operations
- logging/    - Logging configuration
"""

# Re-export commonly used items for backward compatibility
from .settings import get_settings, Settings
from .logging import setup_logging

# LLM services
from .llm import LLMService, LLMContentGenerator

# Image generators
from .image import (
    GeminiImageGenerator,
    encode_image_base64,
)

# Parsers
from . import parsers

__all__ = [
    # Settings
    "get_settings",
    "Settings",
    "setup_logging",
    # LLM
    "LLMService",
    "LLMContentGenerator",
    # Image
    "GeminiImageGenerator",
    "encode_image_base64",
    # Parsers
    "parsers",
]
