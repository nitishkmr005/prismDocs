"""
Configuration module for document generator.

Contains settings used across the application.
Prompts have been moved to domain layer.

Usage:
    from doc_generator.config import settings, get_settings
    from doc_generator.domain.prompts import CONTENT_SYSTEM_PROMPT
"""

# Settings re-export
from .settings import (
    Settings,
    get_settings,
    settings,
)

__all__ = [
    # Settings
    "Settings",
    "get_settings",
    "settings",
]
