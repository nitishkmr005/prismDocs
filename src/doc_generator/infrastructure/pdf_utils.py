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

from cairosvg import svg2png
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

from ..utils.markdown_utils import strip_frontmatter  # noqa: F401

# Color palette (migrated from build_transformer_pdf.py lines 33-43)
PALETTE = {
    "ink": colors.HexColor("#1C1C1C"),
    "muted": colors.HexColor("#4A4A4A"),
    "paper": colors.HexColor("#F6F1E7"),
    "panel": colors.HexColor("#FFFDF8"),
    "accent": colors.HexColor("#D76B38"),
    "teal": colors.HexColor("#1E5D5A"),
    "line": colors.HexColor("#E2D7C9"),
    "code": colors.HexColor("#F2EEE7"),
    "table": colors.HexColor("#F8F4ED"),
}


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
    """
    lines = text.splitlines()
    in_code = False
    code_lang = ""
    code_lines = []
    table_lines = []
    bullets = []

    def flush_table():
        nonlocal table_lines
        if table_lines:
            yield ("table", parse_table(table_lines))
            table_lines = []

    def flush_bullets():
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


def rasterize_svg(svg_path: Path, image_cache: Path) -> Path | None:
    """
    Convert SVG to PNG for embedding in PDF.

    Args:
        svg_path: Path to SVG file
        image_cache: Directory for cached images

    Returns:
        Path to generated PNG file, or None if conversion failed
    """
    try:
        image_cache.mkdir(parents=True, exist_ok=True)
        output_path = image_cache / (svg_path.stem + ".png")

        if not output_path.exists():
            # Validate SVG before conversion to avoid XML parsing errors
            if not svg_path.exists():
                logger.warning(f"SVG file not found: {svg_path}")
                return None
                
            # Read and validate SVG content
            try:
                svg_content = svg_path.read_text(encoding="utf-8")
                if not svg_content.strip() or "<svg" not in svg_content.lower():
                    logger.warning(f"Invalid SVG content in: {svg_path.name}")
                    return None
            except Exception as e:
                logger.warning(f"Could not read SVG file {svg_path.name}: {e}")
                return None
            
            svg2png(url=str(svg_path), write_to=str(output_path), output_width=1600)
            logger.info(f"Rasterized SVG: {svg_path.name} → {output_path.name}")

        return output_path
    except Exception as e:
        logger.error(f"Failed to rasterize SVG {svg_path.name}: {e}")
        return None


def make_image_flowable(
    alt: str,
    image_path: Path,
    styles: dict,
    max_width: float = 6.9 * inch,
    max_height: float = 4.4 * inch
) -> list:
    """
    Create image flowable with caption.

    Args:
        alt: Alt text / caption
        image_path: Path to image file
        styles: ReportLab styles dictionary
        max_width: Maximum image width
        max_height: Maximum image height

    Returns:
        List of flowables (Image + caption + spacer)
    """
    if not image_path.exists():
        logger.warning(f"Image not found: {image_path}")
        return [Paragraph(f"Image placeholder: {inline_md(alt)}", styles["ImageCaption"])]

    img = ImageReader(str(image_path))
    width_px, height_px = img.getSize()
    scale = min(max_width / width_px, max_height / height_px)
    render_w = width_px * scale
    render_h = height_px * scale

    flow = [Image(str(image_path), width=render_w, height=render_h)]
    flow.append(Paragraph(inline_md(alt), styles["ImageCaption"]))
    flow.append(Spacer(1, 6))

    return flow


def make_code_block(code: str, styles: dict) -> Table:
    """
    Create formatted code block.

    Args:
        code: Code content
        styles: ReportLab styles dictionary

    Returns:
        Table flowable with code block styling
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


def make_mermaid_flowable(
    mermaid_text: str,
    styles: dict,
    image_cache: Path,
    mmdc_path: Path | None = None
) -> list:
    """
    Create mermaid diagram flowable.

    Args:
        mermaid_text: Mermaid diagram code
        styles: ReportLab styles dictionary
        image_cache: Directory for cached images
        mmdc_path: Path to mermaid CLI (optional)

    Returns:
        List of flowables (Image + spacer or placeholder)
    """
    rendered = render_mermaid(mermaid_text, image_cache, mmdc_path)

    if not rendered:
        return [
            Paragraph("Mermaid diagram (rendering not available)", styles["ImageCaption"]),
            Spacer(1, 6)
        ]

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

    Blog-like styling with larger typography, more whitespace,
    and improved readability.

    Returns:
        Dictionary of custom ParagraphStyle objects
    """
    styles = getSampleStyleSheet()

    # Title styles - Blog-like hero header
    styles.add(ParagraphStyle(
        name="TitleCover",
        parent=styles["Title"],
        fontName="Times-Bold",
        fontSize=36,
        leading=44,
        textColor=PALETTE["ink"],
        spaceAfter=12,
        spaceBefore=24,
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

    # Table of Contents styles
    styles.add(ParagraphStyle(
        name="TOCHeading",
        parent=styles["Heading1"],
        fontName="Times-Bold",
        fontSize=20,
        leading=28,
        textColor=PALETTE["teal"],
        spaceBefore=24,
        spaceAfter=16,
    ))

    styles.add(ParagraphStyle(
        name="TOCEntry",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=12,
        leading=20,
        textColor=PALETTE["ink"],
        leftIndent=12,
        spaceAfter=6,
    ))

    # Section banner - Blog-style section divider
    styles.add(ParagraphStyle(
        name="SectionBanner",
        parent=styles["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
    ))

    # Heading styles - Blog-like larger headings with more space
    styles.add(ParagraphStyle(
        name="Heading2Custom",
        parent=styles["Heading2"],
        fontName="Times-Bold",
        fontSize=24,
        leading=32,
        textColor=PALETTE["ink"],
        spaceBefore=24,
        spaceAfter=12,
    ))

    styles.add(ParagraphStyle(
        name="Heading3Custom",
        parent=styles["Heading3"],
        fontName="Times-Bold",
        fontSize=18,
        leading=24,
        textColor=PALETTE["ink"],
        spaceBefore=16,
        spaceAfter=8,
    ))

    # Body text - Blog-like readable body
    styles.add(ParagraphStyle(
        name="BodyCustom",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=12,
        leading=20,
        textColor=PALETTE["muted"],
        spaceAfter=12,
    ))

    # Bullets - Larger for readability
    styles.add(ParagraphStyle(
        name="BulletCustom",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=12,
        leading=20,
        leftIndent=20,
        bulletIndent=8,
        spaceAfter=8,
        textColor=PALETTE["muted"],
    ))

    # Code block - Blog-style with better readability
    styles.add(ParagraphStyle(
        name="CodeBlock",
        parent=styles["BodyText"],
        fontName="Courier",
        fontSize=10,
        leading=14,
        leftIndent=8,
        rightIndent=8,
        spaceAfter=12,
        textColor=PALETTE["ink"],
    ))

    # Image caption - Blog-style centered caption
    styles.add(ParagraphStyle(
        name="ImageCaption",
        parent=styles["BodyText"],
        fontName="Helvetica-Oblique",
        fontSize=11,
        leading=16,
        textColor=PALETTE["muted"],
        alignment=1,  # Center
        spaceAfter=16,
    ))

    # Quote - Blog-style blockquote
    styles.add(ParagraphStyle(
        name="Quote",
        parent=styles["BodyText"],
        fontName="Times-Italic",
        fontSize=14,
        leading=22,
        textColor=PALETTE["ink"],
        leftIndent=20,
        rightIndent=20,
    ))

    # Table cell - Blog-style readable tables
    styles.add(ParagraphStyle(
        name="TableCell",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=11,
        leading=16,
        textColor=PALETTE["ink"],
    ))

    # Featured/Hero image style
    styles.add(ParagraphStyle(
        name="HeroCaption",
        parent=styles["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=18,
        textColor=PALETTE["accent"],
        alignment=1,  # Center
        spaceAfter=24,
    ))

    return styles
