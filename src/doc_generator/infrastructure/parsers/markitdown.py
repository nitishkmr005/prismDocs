"""
MarkItDown adapter for document-to-markdown conversion.

Provides wrapper around Microsoft's MarkItDown library for converting
various document formats to Markdown.
"""

import inspect
from pathlib import Path

from loguru import logger

try:
    from markitdown import MarkItDown
    MARKITDOWN_AVAILABLE = True
except ImportError:
    MARKITDOWN_AVAILABLE = False
    logger.warning("MarkItDown not available - some conversion features disabled")

from ...domain.exceptions import ParseError


def _create_markitdown(timeout: int | None = None, user_agent: str | None = None) -> "MarkItDown":
    """
    Create a MarkItDown instance with optional request settings.
    Invoked by: src/doc_generator/infrastructure/parsers/markitdown.py
    """
    if not MARKITDOWN_AVAILABLE:
        raise ImportError(
            "MarkItDown is not installed. Install with: pip install markitdown[all]"
        )

    kwargs = {}
    try:
        signature = inspect.signature(MarkItDown)
        params = signature.parameters
        if timeout is not None:
            if "timeout" in params:
                kwargs["timeout"] = timeout
            elif "request_timeout" in params:
                kwargs["request_timeout"] = timeout
            elif "request_timeout_seconds" in params:
                kwargs["request_timeout_seconds"] = timeout
        if user_agent:
            if "user_agent" in params:
                kwargs["user_agent"] = user_agent
            elif "headers" in params:
                kwargs["headers"] = {"User-Agent": user_agent}
    except (TypeError, ValueError):
        kwargs = {}

    return MarkItDown(**kwargs)


def convert_to_markdown(file_path: Path) -> str:
    """
    Convert document to markdown using MarkItDown.

    Supports: HTML, PDF, DOCX, PPTX, XLSX, images, audio.

    Args:
        file_path: Path to input file

    Returns:
        Markdown content

    Raises:
        ParseError: If conversion fails
        ImportError: If MarkItDown is not installed
    Invoked by: (no references found)
    """
    if not file_path.exists():
        raise ParseError(f"File not found: {file_path}")

    try:
        logger.info(f"Converting with MarkItDown: {file_path.name}")

        md = _create_markitdown()
        result = md.convert(str(file_path))

        markdown_content = result.text_content

        logger.info(f"MarkItDown conversion successful: {len(markdown_content)} chars")

        return markdown_content

    except Exception as e:
        logger.error(f"MarkItDown conversion failed for {file_path}: {e}")
        raise ParseError(f"Failed to convert with MarkItDown: {e}")


def convert_url_to_markdown(
    url: str,
    timeout: int | None = None,
    user_agent: str | None = None,
) -> str:
    """
    Convert web page to markdown using MarkItDown.

    Args:
        url: URL to web page
        timeout: Optional request timeout (seconds)
        user_agent: Optional User-Agent header

    Returns:
        Markdown content

    Raises:
        ParseError: If conversion fails
        ImportError: If MarkItDown is not installed
    Invoked by: src/doc_generator/application/parsers/web_parser.py
    """
    try:
        logger.info(f"Fetching URL with MarkItDown: {url}")

        md = _create_markitdown(timeout=timeout, user_agent=user_agent)
        result = md.convert(url)

        markdown_content = result.text_content

        logger.info(f"URL conversion successful: {len(markdown_content)} chars")

        return markdown_content

    except Exception as e:
        logger.error(f"MarkItDown URL conversion failed for {url}: {e}")
        raise ParseError(f"Failed to convert URL with MarkItDown: {e}")


def is_markitdown_available() -> bool:
    """
    Check if MarkItDown is available.

    Returns:
        True if MarkItDown is installed, False otherwise
    Invoked by: src/doc_generator/application/parsers/web_parser.py
    """
    return MARKITDOWN_AVAILABLE
