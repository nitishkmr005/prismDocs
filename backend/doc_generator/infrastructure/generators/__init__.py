"""Output generators for PDF, PPTX, Markdown, PDF from PPTX, and FAQ."""

from ...domain.content_types import OutputFormat
from ...domain.exceptions import UnsupportedFormatError
from .faq import FAQGenerator
from .markdown import MarkdownGenerator
from .pdf import PDFGenerator
from .pdf_from_pptx import PDFFromPPTXGenerator
from .pptx import PPTXGenerator


def get_generator(output_format: str):
    """
    Get appropriate generator for output format.

    Args:
        output_format: Output format (pdf, pptx, markdown, pdf_from_pptx, faq)

    Returns:
        Generator instance

    Raises:
        UnsupportedFormatError: If format is not supported
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

    if format_lower in ["faq", OutputFormat.FAQ]:
        return FAQGenerator()

    raise UnsupportedFormatError(f"Unsupported output format: {output_format}")


__all__ = [
    "FAQGenerator",
    "MarkdownGenerator",
    "PDFGenerator",
    "PDFFromPPTXGenerator",
    "PPTXGenerator",
    "get_generator",
]
