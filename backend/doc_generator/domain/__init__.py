"""
Domain layer for document generator.

This layer contains pure business logic with no external dependencies:
- models.py       - Domain entities (Document, Section, etc.)
- exceptions.py   - Domain-specific exceptions
- interfaces.py   - Abstract interfaces/protocols
- content_types.py - Enums and value objects
- prompts/        - LLM prompts (domain knowledge)
"""

from .models import WorkflowState
from .exceptions import (
    DocumentGeneratorError,
    GenerationError,
    ParseError,
    ValidationError,
    UnsupportedFormatError,
)
from .content_types import ImageType, ContentFormat, OutputFormat, Audience
from .interfaces import ContentParser, OutputGenerator

__all__ = [
    # Models
    "WorkflowState",
    # Exceptions
    "DocumentGeneratorError",
    "GenerationError",
    "ParseError",
    "ValidationError",
    "UnsupportedFormatError",
    # Content types
    "ImageType",
    "ContentFormat",
    "OutputFormat",
    "Audience",
    # Interfaces
    "ContentParser",
    "OutputGenerator",
]
