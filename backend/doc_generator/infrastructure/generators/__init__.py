"""Output generators for PDF and PPTX."""

from ...domain.content_types import OutputFormat
from ...domain.exceptions import UnsupportedFormatError
from .pdf import PDFGenerator
from .pptx import PPTXGenerator


def get_generator(output_format: str):
    """
    Get appropriate generator for output format.

    Args:
        output_format: Output format (pdf, pptx)

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

    raise UnsupportedFormatError(f"Unsupported output format: {output_format}")


__all__ = ["PDFGenerator", "PPTXGenerator", "get_generator"]
