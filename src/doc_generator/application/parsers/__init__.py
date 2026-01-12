"""
Parsers for different input formats.

Provides factory function to get appropriate parser for content format.
"""

from ...domain.content_types import ContentFormat
from ...domain.exceptions import UnsupportedFormatError
from .markdown_parser import MarkdownParser
from .unified_parser import UnifiedParser
from .web_parser import WebParser


def get_parser(content_format: str):
    """
    Get appropriate parser for content format.

    Args:
        content_format: Content format (pdf, md, txt, url, etc.)

    Returns:
        Parser instance

    Raises:
        UnsupportedFormatError: If format is not supported
    Invoked by: scripts/generate_from_folder.py, src/doc_generator/application/nodes/parse_content.py, src/doc_generator/application/workflow/nodes/parse_content.py, src/doc_generator/infrastructure/api/services/generation.py
    """
    format_lower = content_format.lower()

    # Markdown files
    if format_lower in ["md", "markdown", ContentFormat.MARKDOWN]:
        return MarkdownParser()

    # Web URLs
    if format_lower in ["url", "html", ContentFormat.URL, ContentFormat.HTML]:
        return WebParser()

    # Documents handled by Docling (PDF, DOCX, PPTX, images)
    if format_lower in ["pdf", "docx", "pptx", "xlsx", "png", "jpg", "jpeg", "tiff"]:
        return UnifiedParser()

    # Plain text (treat as markdown)
    if format_lower in ["txt", "text", ContentFormat.TEXT]:
        return MarkdownParser()

    raise UnsupportedFormatError(f"Unsupported content format: {content_format}")


__all__ = ["UnifiedParser", "MarkdownParser", "WebParser", "get_parser"]
