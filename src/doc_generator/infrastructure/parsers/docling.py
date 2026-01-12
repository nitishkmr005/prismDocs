"""
Docling adapter for advanced document parsing.

Provides wrapper around Docling library for PDF, DOCX, PPTX, and image parsing
with OCR support.
"""

from pathlib import Path
from typing import Tuple

from loguru import logger

try:
    from docling.document_converter import DocumentConverter
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    logger.warning("Docling not available - advanced document parsing disabled")

from ...domain.exceptions import ParseError


def convert_document_to_markdown(file_path: Path) -> Tuple[str, dict]:
    """
    Convert document to markdown using Docling.

    Supports: PDF, DOCX, PPTX, XLSX, images with advanced OCR,
    table extraction, and layout analysis.

    Args:
        file_path: Path to input document

    Returns:
        Tuple of (markdown_content, metadata)

    Raises:
        ParseError: If conversion fails
        ImportError: If Docling is not installed
    Invoked by: src/doc_generator/application/parsers/unified_parser.py
    """
    if not DOCLING_AVAILABLE:
        raise ImportError(
            "Docling is not installed. Install with: pip install docling"
        )

    if not file_path.exists():
        raise ParseError(f"File not found: {file_path}")

    try:
        logger.info(f"Converting document with Docling: {file_path.name}")

        converter = DocumentConverter()
        result = converter.convert(str(file_path))

        # Export to markdown
        markdown_content = result.document.export_to_markdown()

        # Extract metadata
        metadata = {
            "title": getattr(result.document, "title", file_path.stem),
            "pages": getattr(result.document, "num_pages", None),
            "source_file": str(file_path),
            "parser": "docling",
        }

        # Add any additional metadata from result
        if hasattr(result, "metadata"):
            metadata.update(result.metadata)

        logger.info(
            f"Docling conversion successful: {len(markdown_content)} chars, "
            f"{metadata.get('pages', 'N/A')} pages"
        )

        return markdown_content, metadata

    except Exception as e:
        logger.error(f"Docling conversion failed for {file_path}: {e}")
        raise ParseError(f"Failed to convert document with Docling: {e}")


def is_docling_available() -> bool:
    """
    Check if Docling is available.

    Returns:
        True if Docling is installed, False otherwise
    Invoked by: src/doc_generator/application/parsers/unified_parser.py
    """
    return DOCLING_AVAILABLE
