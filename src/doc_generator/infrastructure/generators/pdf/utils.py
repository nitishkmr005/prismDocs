"""
PDF generation utilities migrated from data/build_transformer_pdf.py.

This module contains reusable functions for PDF generation using ReportLab,
including markdown parsing, styling, and flowable creation.
"""

from __future__ import annotations

import hashlib
import html
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Iterator

from loguru import logger
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    Image,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)

from ....utils.markdown_utils import strip_frontmatter  # noqa: F401
from ...settings import get_settings

# Corporate-ready color palette - Modern, professional styling
_BASE_PALETTE = {
    "ink": "#1a1a2e",         # Deep navy for text
    "muted": "#4a5568",       # Sophisticated gray
    "paper": "#fafafa",       # Clean white background
    "panel": "#f7fafc",       # Light panel
    "accent": "#2563eb",      # Professional blue
    "accent_light": "#3b82f6", # Lighter blue for highlights
    "teal": "#0d9488",        # Modern teal
    "line": "#e2e8f0",        # Subtle dividers
    "code": "#f1f5f9",        # Code background
    "table": "#f8fafc",       # Table background
    "success": "#10b981",     # Green for positive
    "warning": "#f59e0b",     # Amber for warnings
    "mermaid_bg": "#eef2ff",  # Light blue for diagrams
}


def _load_palette() -> dict:
    """
    Load the PDF palette from settings with safe defaults.
    Invoked by: src/doc_generator/infrastructure/generators/pdf/utils.py
    """
    pdf_palette = get_settings().pdf.palette
    overrides = {
        "ink": pdf_palette.ink,
        "muted": pdf_palette.muted,
        "paper": pdf_palette.paper,
        "panel": pdf_palette.panel,
        "accent": pdf_palette.accent,
        "teal": pdf_palette.teal,
        "line": pdf_palette.line,
        "code": pdf_palette.code,
        "table": pdf_palette.table,
    }
    merged = {**_BASE_PALETTE, **overrides}
    return {key: colors.HexColor(value) for key, value in merged.items()}


PALETTE = _load_palette()


def inline_md(text: str) -> str:
    """
    Convert inline markdown formatting to HTML for ReportLab.

    Supports:
    - `code` → <font face='Courier'>code</font>
    - **bold** → <b>bold</b>
    - *italic* → <i>italic</i>

    Args:
        text: Text with inline markdown formatting

    Returns:
        Text with HTML formatting for ReportLab
    Invoked by: src/doc_generator/infrastructure/generators/pdf/utils.py, src/doc_generator/infrastructure/pdf_utils.py
    """
    safe = html.escape(text)
    safe = re.sub(r"`([^`]+)`", r"<font face='Courier'>\1</font>", safe)
    safe = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", safe)
    safe = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", safe)
    return safe


def parse_table(table_lines: list[str]) -> list[list[str]]:
    """
    Parse markdown table into 2D list.

    Args:
        table_lines: Lines of markdown table

    Returns:
        2D list of table cells (skips separator rows)
    Invoked by: src/doc_generator/infrastructure/generators/pdf/utils.py, src/doc_generator/infrastructure/pdf_utils.py
    """
    rows = []
    for line in table_lines:
        parts = [cell.strip() for cell in line.strip().strip("|").split("|")]
        # Skip separator rows (e.g., |---|---|)
        if all(re.match(r"^:?-{2,}:?$", cell) for cell in parts):
            continue
        rows.append(parts)
    return rows


def parse_markdown_lines(text: str) -> Iterator[tuple[str, any]]:
    """
    Parse markdown text into structured elements.

    Yields tuples of (element_type, content):
    - ("h1", "Heading text")
    - ("h2", "Subheading")
    - ("para", "Paragraph text")
    - ("code", "code content")
    - ("mermaid", "mermaid diagram code")
    - ("table", [[row1], [row2]])
    - ("bullets", ["item1", "item2"])
    - ("image", ("alt text", "url"))
    - ("quote", "quoted text")
    - ("spacer", "")
    - ("visual_marker", {"type": "architecture", "title": "...", "description": "..."})

    Args:
        text: Markdown text to parse

    Yields:
        Tuples of (element_type, content)
    Invoked by: (no references found)
    """
    lines = text.splitlines()
    in_code = False
    code_lang = ""
    code_lines = []
    table_lines = []
    bullets = []

    def flush_table():
        """
        Invoked by: src/doc_generator/infrastructure/generators/pdf/utils.py, src/doc_generator/infrastructure/pdf_utils.py
        """
        nonlocal table_lines
        if table_lines:
            yield ("table", parse_table(table_lines))
            table_lines = []

    def flush_bullets():
        """
        Invoked by: src/doc_generator/infrastructure/generators/pdf/utils.py, src/doc_generator/infrastructure/pdf_utils.py
        """
        nonlocal bullets
        if bullets:
            yield ("bullets", bullets)
            bullets = []

    for line in lines:
        # Code blocks
        if line.strip().startswith("```"):
            if in_code:
                content = "\n".join(code_lines)
                kind = "mermaid" if code_lang == "mermaid" else "code"
                yield (kind, content)
                code_lines = []
                code_lang = ""
                in_code = False
            else:
                in_code = True
                code_lang = line.strip().lstrip("```").strip().lower()
            continue

        if in_code:
            code_lines.append(line)
            continue

        # Tables
        if line.strip().startswith("|") and "|" in line:
            table_lines.append(line)
            continue

        if table_lines:
            yield from flush_table()

        # Bullet lists
        list_match = re.match(r"^[-*]\s+(.*)$", line)
        if list_match:
            bullets.append(list_match.group(1))
            continue

        if bullets:
            yield from flush_bullets()

        # Empty lines
        if not line.strip():
            yield ("spacer", "")
            continue

        # Visual markers: [VISUAL:type:title:description]
        visual_match = re.match(r'^\[VISUAL:(\w+):([^:]+):([^\]]+)\]$', line.strip())
        if visual_match:
            yield ("visual_marker", {
                "type": visual_match.group(1).lower(),
                "title": visual_match.group(2).strip(),
                "description": visual_match.group(3).strip()
            })
            continue

        # Headings
        heading_match = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading_match:
            level = len(heading_match.group(1))
            yield (f"h{level}", heading_match.group(2))
            continue

        # Images
        image_match = re.match(r"^!\[(.*?)\]\((.*?)\)", line)
        if image_match:
            alt = image_match.group(1) or "Figure"
            url = image_match.group(2)
            yield ("image", (alt, url))
            continue

        # Quotes
        quote_match = re.match(r"^>\s?(.*)$", line)
        if quote_match:
            yield ("quote", quote_match.group(1))
            continue

        # Regular paragraph
        yield ("para", line)

    # Flush remaining content
    if code_lines:
        kind = "mermaid" if code_lang == "mermaid" else "code"
        yield (kind, "\n".join(code_lines))
    if table_lines:
        yield from flush_table()
    if bullets:
        yield from flush_bullets()


def extract_headings(text: str) -> list[tuple[int, str]]:
    """
    Extract headings from markdown text for table of contents.

    Args:
        text: Markdown text to parse

    Returns:
        List of (level, heading_text) tuples
    Invoked by: (no references found)
    """
    headings = []
    for line in text.splitlines():
        heading_match = re.match(r"^(#{1,3})\s+(.*)$", line)
        if heading_match:
            level = len(heading_match.group(1))
            headings.append((level, heading_match.group(2)))
    return headings


def make_table_of_contents(headings: list[tuple[int, str]], styles: dict) -> list:
    """
    Create table of contents flowables.

    Args:
        headings: List of (level, heading_text) tuples
        styles: ReportLab styles dictionary

    Returns:
        List of flowables for the TOC
    Invoked by: (no references found)
    """
    if not headings:
        return []

    flowables = []
    flowables.append(Paragraph("Contents", styles["TOCHeading"]))
    flowables.append(Spacer(1, 8))

    for level, heading in headings:
        indent = (level - 1) * 20
        style = ParagraphStyle(
            name=f"TOCLevel{level}",
            parent=styles["TOCEntry"],
            leftIndent=indent,
            fontName="Helvetica-Bold" if level == 1 else "Helvetica",
            fontSize=12 if level == 1 else 11,
        )
        flowables.append(Paragraph(f"• {inline_md(heading)}", style))

    flowables.append(Spacer(1, 24))
    return flowables


def make_section_divider(styles: dict) -> list:
    """
    Create a blog-style section divider.

    Args:
        styles: ReportLab styles dictionary

    Returns:
        List of flowables for the section divider
    Invoked by: (no references found)
    """
    divider = Table(
        [[""]],
        colWidths=[2 * inch]
    )
    divider.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, -1), 2, PALETTE["accent"]),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return [Spacer(1, 16), divider, Spacer(1, 16)]


def make_banner(text: str, styles: dict) -> Table:
    """
    Create a colored banner for section headings.

    Args:
        text: Section heading text
        styles: ReportLab styles dictionary

    Returns:
        Table flowable with banner styling
    Invoked by: (no references found)
    """
    banner = Table(
        [[Paragraph(inline_md(text), styles["SectionBanner"])]],
        colWidths=[6.9 * inch]
    )
    banner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PALETTE["accent"]),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return banner


# Global figure counter for image numbering
_figure_counter = 0


def reset_figure_counter():
    """
    Reset the global figure counter for a new document.
    Invoked by: (no references found)
    """
    global _figure_counter
    _figure_counter = 0


def make_image_flowable(
    alt: str,
    image_path: Path,
    styles: dict,
    max_width: float = 6.9 * inch,
    max_height: float = 4.4 * inch,
    add_figure_number: bool = True
) -> list:
    """
    Create image flowable with professional caption.

    Args:
        alt: Alt text / caption
        image_path: Path to image file
        styles: ReportLab styles dictionary
        max_width: Maximum image width
        max_height: Maximum image height
        add_figure_number: Whether to add "Figure X:" prefix

    Returns:
        List of flowables (Image + caption + spacer)
    Invoked by: (no references found)
    """
    global _figure_counter

    if not image_path.exists():
        logger.warning(f"Image not found: {image_path}")
        return [Paragraph(f"Image placeholder: {inline_md(alt)}", styles["ImageCaption"])]

    img = ImageReader(str(image_path))
    width_px, height_px = img.getSize()
    scale = min(max_width / width_px, max_height / height_px)
    render_w = width_px * scale
    render_h = height_px * scale

    flow = [Image(str(image_path), width=render_w, height=render_h)]

    # Generate professional caption with figure number
    if add_figure_number:
        _figure_counter += 1
        # Create a more descriptive caption
        caption_text = f"<b>Figure {_figure_counter}:</b> {inline_md(alt)}"
    else:
        caption_text = inline_md(alt)

    flow.append(Paragraph(caption_text, styles["ImageCaption"]))
    flow.append(Spacer(1, 10))

    return flow


def make_code_block(code: str, styles: dict) -> Table:
    """
    Create formatted code block.

    Args:
        code: Code content
        styles: ReportLab styles dictionary

    Returns:
        Table flowable with code block styling
    Invoked by: (no references found)
    """
    block = Preformatted(code, styles["CodeBlock"])
    table = Table([[block]], colWidths=[6.9 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PALETTE["code"]),
        ("BOX", (0, 0), (-1, -1), 0.8, PALETTE["line"]),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def render_mermaid(
    mermaid_text: str,
    image_cache: Path,
    mmdc_path: Path | None = None
) -> Path | None:
    """
    Render mermaid diagram to PNG.

    Args:
        mermaid_text: Mermaid diagram code
        image_cache: Directory for cached images
        mmdc_path: Path to mermaid CLI (optional)

    Returns:
        Path to generated PNG or None if rendering failed
    Invoked by: src/doc_generator/infrastructure/generators/pdf/utils.py, src/doc_generator/infrastructure/pdf_utils.py
    """
    if mmdc_path is None:
        mmdc_path = Path("node_modules/.bin/mmdc")

    if not mmdc_path.exists():
        logger.warning("Mermaid CLI not found, skipping diagram rendering")
        return None

    image_cache.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(mermaid_text.encode("utf-8")).hexdigest()[:12]
    out_path = image_cache / f"mermaid-{digest}.png"

    if out_path.exists():
        return out_path

    with tempfile.NamedTemporaryFile(suffix=".mmd", delete=False) as temp_file:
        temp_file.write(mermaid_text.encode("utf-8"))
        temp_path = Path(temp_file.name)

    try:
        subprocess.run(
            [
                str(mmdc_path), "-i", str(temp_path), "-o", str(out_path),
                "-b", "transparent", "-w", "1600"
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        logger.info(f"Rendered mermaid diagram: {out_path.name}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Mermaid rendering failed: {e.stderr}")
        return None
    finally:
        temp_path.unlink(missing_ok=True)

    return out_path if out_path.exists() else None


def render_mermaid_with_gemini(
    mermaid_text: str,
    image_cache: Path
) -> Path | None:
    """
    Generate a diagram image from mermaid code using Gemini.

    Args:
        mermaid_text: Mermaid diagram code
        image_cache: Directory for cached images

    Returns:
        Path to generated PNG or None if generation failed
    Invoked by: src/doc_generator/infrastructure/generators/pdf/utils.py, src/doc_generator/infrastructure/pdf_utils.py
    """
    try:
        from .gemini_image_generator import get_gemini_generator
    except ImportError:
        logger.warning("Gemini generator not available")
        return None

    image_cache.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(mermaid_text.encode("utf-8")).hexdigest()[:12]
    out_path = image_cache / f"mermaid-gemini-{digest}.png"

    if out_path.exists():
        return out_path

    generator = get_gemini_generator()
    if not generator.is_available():
        logger.warning("Gemini not available for mermaid rendering")
        return None

    result = generator.generate_diagram_from_mermaid(mermaid_text, out_path)
    return result


def make_mermaid_flowable(
    mermaid_text: str,
    styles: dict,
    image_cache: Path,
    mmdc_path: Path | None = None
) -> list:
    """
    Create mermaid diagram flowable.

    First tries mmdc CLI, then falls back to Gemini image generation.

    Args:
        mermaid_text: Mermaid diagram code
        styles: ReportLab styles dictionary
        image_cache: Directory for cached images
        mmdc_path: Path to mermaid CLI (optional)

    Returns:
        List of flowables (Image + spacer or styled code block)
    Invoked by: (no references found)
    """
    logger.info("Mermaid rendering disabled, skipping diagram flowable")
    return []
    # Try mmdc first
    rendered = render_mermaid(mermaid_text, image_cache, mmdc_path)

    # If mmdc fails, try Gemini
    if not rendered:
        logger.info("Trying Gemini for mermaid diagram generation")
        rendered = render_mermaid_with_gemini(mermaid_text, image_cache)

    if not rendered:
        # Show mermaid code in a styled diagram box instead of generic placeholder
        flow = []

        # Header for the diagram box
        header = Table(
            [[Paragraph("<b>Diagram</b>", styles["ImageCaption"])]],
            colWidths=[6.9 * inch]
        )
        header.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), PALETTE["accent"]),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        flow.append(header)

        # Show a preview of the mermaid code (truncated for display)
        preview_lines = mermaid_text.strip().split('\n')[:8]
        if len(mermaid_text.strip().split('\n')) > 8:
            preview_lines.append("...")
        preview_text = '\n'.join(preview_lines)

        code_block = Preformatted(preview_text, styles["CodeBlock"])
        code_table = Table([[code_block]], colWidths=[6.9 * inch])
        code_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), PALETTE["mermaid_bg"]),
            ("BOX", (0, 0), (-1, -1), 0.8, PALETTE["line"]),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        flow.append(code_table)
        flow.append(Spacer(1, 12))

        return flow

    img = ImageReader(str(rendered))
    width_px, height_px = img.getSize()
    max_width = 6.9 * inch
    max_height = 4.4 * inch
    scale = min(max_width / width_px, max_height / height_px)
    render_w = width_px * scale
    render_h = height_px * scale

    flow = [Image(str(rendered), width=render_w, height=render_h)]
    flow.append(Spacer(1, 6))

    return flow


def make_quote(text: str, styles: dict) -> Table:
    """
    Create styled quote block.

    Args:
        text: Quote text
        styles: ReportLab styles dictionary

    Returns:
        Table flowable with quote styling
    Invoked by: (no references found)
    """
    box = Table(
        [[Paragraph(inline_md(text), styles["Quote"])]],
        colWidths=[6.9 * inch]
    )
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F4FBF8")),
        ("BOX", (0, 0), (-1, -1), 1, PALETTE["line"]),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return box


def make_table(table_data: list[list[str]], styles: dict) -> Table:
    """
    Create formatted table from markdown table data.

    Args:
        table_data: 2D list of table cells
        styles: ReportLab styles dictionary

    Returns:
        Table flowable with styling
    Invoked by: (no references found)
    """
    if not table_data:
        return Table([[]])

    wrapped = [
        [Paragraph(inline_md(cell), styles["TableCell"]) for cell in row]
        for row in table_data
    ]
    table = Table(wrapped, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PALETTE["teal"]),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, PALETTE["line"]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    return table


def create_custom_styles() -> dict:
    """
    Create custom ReportLab styles for PDF generation.

    Corporate-ready styling with professional typography, balanced whitespace,
    and excellent readability for executive presentations.

    Returns:
        Dictionary of custom ParagraphStyle objects
    Invoked by: (no references found)
    """
    styles = getSampleStyleSheet()

    # Title styles - Professional corporate header
    styles.add(ParagraphStyle(
        name="TitleCover",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=32,
        leading=40,
        textColor=PALETTE["ink"],
        spaceAfter=16,
        spaceBefore=32,
        alignment=0,  # Left align for corporate look
    ))

    styles.add(ParagraphStyle(
        name="SubtitleCover",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=14,
        leading=20,
        textColor=PALETTE["muted"],
        spaceAfter=24,
    ))

    styles.add(ParagraphStyle(
        name="CoverKicker",
        parent=styles["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=PALETTE["accent"],
        spaceAfter=6,
    ))

    styles.add(ParagraphStyle(
        name="CoverMeta",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=11,
        leading=16,
        textColor=PALETTE["muted"],
        spaceAfter=4,
    ))

    # Table of Contents styles
    styles.add(ParagraphStyle(
        name="TOCHeading",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=24,
        textColor=PALETTE["accent"],
        spaceBefore=24,
        spaceAfter=12,
    ))

    styles.add(ParagraphStyle(
        name="TOCEntry",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=11,
        leading=18,
        textColor=PALETTE["ink"],
        leftIndent=12,
        spaceAfter=4,
    ))

    # Section banner - Corporate section header
    styles.add(ParagraphStyle(
        name="SectionBanner",
        parent=styles["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=18,
        textColor=colors.white,
    ))

    # Heading styles - Clean corporate headings
    styles.add(ParagraphStyle(
        name="Heading2Custom",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=28,
        textColor=PALETTE["ink"],
        spaceBefore=24,
        spaceAfter=12,
    ))

    styles.add(ParagraphStyle(
        name="Heading3Custom",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=22,
        textColor=PALETTE["accent"],
        spaceBefore=18,
        spaceAfter=8,
    ))

    # Body text - Professional readable body
    styles.add(ParagraphStyle(
        name="BodyCustom",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=11,
        leading=18,
        textColor=PALETTE["muted"],
        spaceAfter=10,
        alignment=4,  # Justify for professional look
    ))

    # Bullets - Clean corporate bullets
    styles.add(ParagraphStyle(
        name="BulletCustom",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=11,
        leading=18,
        leftIndent=24,
        bulletIndent=12,
        spaceAfter=6,
        textColor=PALETTE["muted"],
    ))

    # Code block - Professional code styling
    styles.add(ParagraphStyle(
        name="CodeBlock",
        parent=styles["BodyText"],
        fontName="Courier",
        fontSize=9,
        leading=13,
        leftIndent=8,
        rightIndent=8,
        spaceAfter=10,
        textColor=PALETTE["ink"],
    ))

    # Image caption - Professional centered caption
    styles.add(ParagraphStyle(
        name="ImageCaption",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=PALETTE["muted"],
        alignment=1,  # Center
        spaceAfter=14,
        spaceBefore=4,
    ))

    # Quote - Professional blockquote with accent
    styles.add(ParagraphStyle(
        name="Quote",
        parent=styles["BodyText"],
        fontName="Helvetica-Oblique",
        fontSize=12,
        leading=20,
        textColor=PALETTE["ink"],
        leftIndent=24,
        rightIndent=24,
        borderColor=PALETTE["accent"],
        borderPadding=8,
    ))

    # Table cell - Professional table styling
    styles.add(ParagraphStyle(
        name="TableCell",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=PALETTE["ink"],
    ))

    # Featured/Hero image style
    styles.add(ParagraphStyle(
        name="HeroCaption",
        parent=styles["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=16,
        textColor=PALETTE["accent"],
        alignment=1,  # Center
        spaceAfter=20,
    ))

    # Key Takeaways style
    styles.add(ParagraphStyle(
        name="KeyTakeaway",
        parent=styles["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=18,
        textColor=PALETTE["ink"],
        leftIndent=16,
        spaceAfter=8,
    ))

    return styles
