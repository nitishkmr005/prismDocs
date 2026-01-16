"""Output generators for PDF, PPTX, Markdown, and PDF from PPTX."""

from ...domain.content_types import OutputFormat
from ...domain.exceptions import UnsupportedFormatError
from .markdown import MarkdownGenerator
from .pdf import PDFGenerator
from .pdf_from_pptx import PDFFromPPTXGenerator
from .pptx import PPTXGenerator


def get_generator(output_format: str):
    """
    Get appropriate generator for output format.

    Args:
        output_format: Output format (pdf, pptx, markdown, pdf_from_pptx)

    Returns:
        Generator instance

    Raises:
        UnsupportedFormatError: If format is not supported
    Invoked by: scripts/generate_from_folder.py, src/doc_generator/application/nodes/generate_output.py, src/doc_generator/application/workflow/nodes/generate_output.py
    """
    format_lower = output_format.lower()

    if format_lower in ["pdf", OutputFormat.PDF]:
        return PDFGenerator()

    if format_lower in ["pptx", "ppt", OutputFormat.PPTX]:
        return PPTXGenerator()

    if format_lower in ["markdown", "md", OutputFormat.MARKDOWN]:
        return MarkdownGenerator()

    if format_lower in ["pdf_from_pptx", OutputFormat.PDF_FROM_PPTX]:
        return PDFFromPPTXGenerator()

    raise UnsupportedFormatError(f"Unsupported output format: {output_format}")


__all__ = [
    "MarkdownGenerator",
    "PDFGenerator",
    "PDFFromPPTXGenerator",
    "PPTXGenerator",
    "get_generator",
]
