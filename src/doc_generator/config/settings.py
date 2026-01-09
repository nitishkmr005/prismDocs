"""
Settings re-export for config module convenience.

The actual settings implementation is in infrastructure/settings.py.
This module provides a convenience import path:

    from doc_generator.config import settings, get_settings

For backwards compatibility, settings can also be imported from:
    from doc_generator.infrastructure.settings import settings, get_settings
"""

# Re-export from infrastructure for convenience
from ..infrastructure.settings import (
    Settings,
    get_settings,
    settings,
    # Sub-settings classes
    GeneratorSettings,
    LlmSettings,
    LoggingSettings,
    PdfSettings,
    PdfPaletteSettings,
    PdfMarginSettings,
    PptxSettings,
    PptxThemeSettings,
    ParserSettings,
    DoclingSettings,
    WebParserSettings,
    SvgSettings,
    ImageGenerationSettings,
)

__all__ = [
    "Settings",
    "get_settings",
    "settings",
    "GeneratorSettings",
    "LlmSettings",
    "LoggingSettings",
    "PdfSettings",
    "PdfPaletteSettings",
    "PdfMarginSettings",
    "PptxSettings",
    "PptxThemeSettings",
    "ParserSettings",
    "DoclingSettings",
    "WebParserSettings",
    "SvgSettings",
    "ImageGenerationSettings",
]
