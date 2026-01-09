"""
Content type enumerations for document generator.

Defines supported input and output formats.
"""

from enum import Enum


class ContentFormat(str, Enum):
    """Supported input content formats."""

    PDF = "pdf"
    MARKDOWN = "md"
    TEXT = "txt"
    URL = "url"
    DOCX = "docx"
    PPTX = "pptx"
    HTML = "html"


class OutputFormat(str, Enum):
    """Supported output formats."""

    PDF = "pdf"
    PPTX = "pptx"


class ImageType(str, Enum):
    """Supported image generation types."""

    INFOGRAPHIC = "infographic"  # Gemini - explains concepts visually
    DECORATIVE = "decorative"    # Gemini - thematic header image
    DIAGRAM = "diagram"          # SVG - architecture, flowcharts
    CHART = "chart"              # SVG - data comparisons
    MERMAID = "mermaid"          # Mermaid - sequence diagrams, flows
    NONE = "none"                # Skip image for this section
