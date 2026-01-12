"""
Web article parser using MarkItDown.

Fetches and converts web pages to markdown.
"""

from pathlib import Path
from typing import Tuple

from loguru import logger

from ...domain.exceptions import ParseError
from ...infrastructure.parsers.markitdown import convert_url_to_markdown, is_markitdown_available
from ...infrastructure.settings import get_settings


class WebParser:
    """
    Parser for web articles and HTML content.

    Uses Microsoft's MarkItDown library to convert HTML to markdown.
    """

    def __init__(self):
        """
        Invoked by: (no references found)
        """
        if not is_markitdown_available():
            logger.warning(
                "MarkItDown not available - web parsing will have limited functionality"
            )

    def parse(self, input_path: str | Path) -> Tuple[str, dict]:
        """
        Fetch and parse web article.

        Args:
            input_path: URL to web page

        Returns:
            Tuple of (markdown_content, metadata)

        Raises:
            ParseError: If fetching or parsing fails
        Invoked by: .claude/skills/pptx/ooxml/scripts/pack.py, .claude/skills/pptx/ooxml/scripts/validation/base.py, .claude/skills/pptx/ooxml/scripts/validation/docx.py, .claude/skills/pptx/ooxml/scripts/validation/pptx.py, .claude/skills/pptx/ooxml/scripts/validation/redlining.py, scripts/generate_from_folder.py, src/doc_generator/application/nodes/parse_content.py, src/doc_generator/application/workflow/nodes/parse_content.py, src/doc_generator/infrastructure/api/services/generation.py
        """
        url = str(input_path)
        settings = get_settings().parsers.web

        logger.info(f"Fetching web article: {url}")

        try:
            content = convert_url_to_markdown(
                url,
                timeout=settings.timeout,
                user_agent=settings.user_agent,
            )

            # Extract title from content (first heading)
            title = self._extract_title_from_markdown(content)

            metadata = {
                "title": title,
                "url": url,
                "parser": "web",
            }

            logger.info(
                f"Web parsing completed: {len(content)} chars, "
                f"title='{title}'"
            )

            return content, metadata

        except Exception as e:
            logger.error(f"Web parsing failed for {url}: {e}")
            raise ParseError(f"Failed to parse web article: {e}")

    def _extract_title_from_markdown(self, content: str) -> str:
        """
        Extract title from markdown content (first H1 heading).

        Args:
            content: Markdown content

        Returns:
            Extracted title or default
        Invoked by: src/doc_generator/application/parsers/web_parser.py
        """
        import re

        # Look for first H1 heading
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)

        if match:
            return match.group(1).strip()

        return "Web Article"
