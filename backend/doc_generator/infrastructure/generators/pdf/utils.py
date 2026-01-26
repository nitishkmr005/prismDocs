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

# Modern blog-style color palette - Vibrant and readable
_BASE_PALETTE = {
    "ink": "#1e293b",  # Slate-800 (softer than pure black)
    "muted": "#64748b",  # Slate-500 (modern gray)
    "paper": "#ffffff",  # Pure white
    "panel": "#f8fafc",  # Slate-50 (subtle background)
    "accent": "#6366f1",  # Indigo-500 (vibrant primary)
    "accent_light": "#818cf8",  # Indigo-400 (lighter variant)
    "accent_dark": "#4f46e5",  # Indigo-600 (darker variant)
    "teal": "#14b8a6",  # Teal-500 (secondary accent)
    "line": "#e2e8f0",  # Slate-200 (subtle dividers)
    "code": "#f1f5f9",  # Slate-100 (code background)
    "table": "#f8fafc",  # Slate-50 (table background)
    "success": "#22c55e",  # Green-500
    "warning": "#f59e0b",  # Amber-500
    "mermaid_bg": "#eef2ff",  # Indigo-50 for diagrams
    "cover_bar": "#6366f1",  # Cover page accent bar
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
CONTENT_WIDTH = 6.9 * inch


def inline_md(text: str) -> str:
    """
    Convert inline markdown formatting to HTML for ReportLab.

    Supports:
    - `code` → <font face='Courier'>code</font>
    - **bold** → <b>bold</b>
    - *italic* → <i>italic</i>
    - [text](url) → <link href="url">text</link> (clickable)

    Args:
        text: Text with inline markdown formatting

    Returns:
        Text with HTML formatting for ReportLab
    Invoked by: src/doc_generator/infrastructure/generators/pdf/utils.py, src/doc_generator/infrastructure/pdf_utils.py
    """
    # First, handle markdown links [text](url) -> clickable links
    # Use a placeholder to avoid conflicts with other formatting
    link_pattern = r"\[([^\]]+)\]\(([^\)]+)\)"
    links = []

    def replace_link(match):
        text_part = match.group(1)
        url = match.group(2)
        links.append((text_part, url))
        return f"__LINK_{len(links)-1}__"

    text = re.sub(link_pattern, replace_link, text)

    # Handle code blocks
    parts = re.split(r"(`[^`]+`)", text)
    rendered: list[str] = []
    for part in parts:
        if part.startswith("`") and part.endswith("`") and len(part) >= 2:
            # For inline code, escape HTML special chars like < and >
            code = part[1:-1]
            # Only escape < and > which could break XML/HTML parsing
            # Keep quotes as-is since ReportLab handles them fine
            code = code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            rendered.append(f"<font face='Courier'>{code}</font>")
            continue
        # For regular text, only escape < and > that could break tags
        # Keep quotes and apostrophes as-is for better readability
        safe = part.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        safe = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", safe)
        safe = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", safe)
        rendered.append(safe)

    result = "".join(rendered)

    # Restore links with proper ReportLab link tags
    for i, (link_text, url) in enumerate(links):
        placeholder = f"__LINK_{i}__"
        # Only escape < and > in URLs, keep quotes
        safe_url = url.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        safe_text = (
            link_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        )
        link_html = f'<link href="{safe_url}" color="blue"><u>{safe_text}</u></link>'
        result = result.replace(placeholder, link_html)

    return result


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

        # Bullet lists - but skip if it looks like code
        list_match = re.match(r"^[-*]\s+(.*)$", line)
        if list_match:
            bullet_content = list_match.group(1)
            # Check if the bullet content looks like code (common patterns)
            code_patterns = [
                r"^\w+\s*=\s*\w+.*\(.*\)",  # function calls: var = func(...)
                r"^(def|class|import|from|if|for|while|return|print|async|await)\s+",  # Python keywords
                r"^(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)\s+",  # SQL keywords
                r"^[\w_]+\(.*?\)",  # function calls: func(...)
                r"^(const|let|var|function|async)\s+",  # JavaScript keywords
                r"^\$\w+",  # shell variables
                r"^[a-z_]+\s*\(",  # function call at start
            ]
            is_likely_code = any(
                re.match(pattern, bullet_content, re.IGNORECASE)
                for pattern in code_patterns
            )

            if not is_likely_code:
                bullets.append(bullet_content)
                continue
            # If it looks like code, let it fall through to regular paragraph handling

        if bullets:
            yield from flush_bullets()

        # Empty lines
        if not line.strip():
            yield ("spacer", "")
            continue

        # Visual markers: [VISUAL:type:title:description]
        visual_match = re.match(r"^\[VISUAL:(\w+):([^:]+):([^\]]+)\]$", line.strip())
        if visual_match:
            yield (
                "visual_marker",
                {
                    "type": visual_match.group(1).lower(),
                    "title": visual_match.group(2).strip(),
                    "description": visual_match.group(3).strip(),
                },
            )
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


def _normalize_heading_for_comparison(heading: str) -> str:
    """
    Normalize a heading for comparison to detect duplicates.

    Removes:
    - Leading numbers and punctuation (e.g., "1." or "1)")
    - Extra whitespace
    - Case differences

    Examples:
        "Introduction" -> "introduction"
        "1. Introduction" -> "introduction"
        "Key Takeaways" -> "key takeaways"
        "6. Key Takeaways" -> "key takeaways"
    """
    # Remove leading number patterns like "1.", "1)", "1:", "1 "
    cleaned = re.sub(r"^\d+[\.:)\s]+\s*", "", heading.strip())
    # Normalize whitespace and case
    return re.sub(r"\s+", " ", cleaned).strip().lower()


def _deduplicate_headings(headings: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """
    Remove duplicate headings from the list, keeping the more specific version.

    For example, if both "Introduction" and "1. Introduction" exist,
    keep only "1. Introduction" (the numbered one).
    """
    if not headings:
        return []

    # Group headings by their normalized form
    normalized_groups: dict[str, list[tuple[int, str, int]]] = {}
    for idx, (level, heading) in enumerate(headings):
        normalized = _normalize_heading_for_comparison(heading)
        if normalized not in normalized_groups:
            normalized_groups[normalized] = []
        normalized_groups[normalized].append((level, heading, idx))

    # For each group, keep the best version (prefer numbered)
    result_with_indices = []
    for normalized, group in normalized_groups.items():
        if len(group) == 1:
            level, heading, idx = group[0]
            result_with_indices.append((idx, level, heading))
        else:
            # Multiple versions of the same heading
            # Prefer: numbered > unnumbered, keep first occurrence of preferred type
            numbered = [
                (lvl, h, i) for lvl, h, i in group if re.match(r"^\d+[\.:)\s]", h)
            ]
            if numbered:
                # Keep the first numbered version
                level, heading, idx = numbered[0]
                result_with_indices.append((idx, level, heading))
            else:
                # No numbered versions, keep the first one
                level, heading, idx = group[0]
                result_with_indices.append((idx, level, heading))

    # Sort by original index to maintain document order
    result_with_indices.sort(key=lambda x: x[0])
    return [(level, heading) for _, level, heading in result_with_indices]


def make_table_of_contents(
    headings: list[tuple[int, str]],
    styles: dict,
    markdown_content: str = "",
    toc_settings: dict = None,
) -> list:
    """
    Create table of contents flowables with optional page numbers and reading time.

    Args:
        headings: List of (level, heading_text) tuples
        styles: ReportLab styles dictionary
        markdown_content: Full markdown content for reading time calculation
        toc_settings: TOC settings dictionary with keys:
            - include_page_numbers: bool
            - max_depth: int (1-6)
            - show_reading_time: bool
            - words_per_minute: int

    Returns:
        List of flowables for the TOC
    Invoked by: (no references found)
    """
    if not headings:
        return []

    # Default settings
    if toc_settings is None:
        toc_settings = {
            "include_page_numbers": True,
            "max_depth": 3,
            "show_reading_time": True,
            "words_per_minute": 200,
        }

    # Filter headings by max depth
    max_depth = toc_settings.get("max_depth", 3)
    filtered_headings = [(lvl, txt) for lvl, txt in headings if lvl <= max_depth]

    # Deduplicate headings to avoid entries like "Introduction" and "1. Introduction"
    filtered_headings = _deduplicate_headings(filtered_headings)

    if not filtered_headings:
        return []

    flowables = []
    flowables.append(Paragraph("Contents", styles["TOCHeading"]))

    # Add reading time estimate if enabled
    if toc_settings.get("show_reading_time", True) and markdown_content:
        word_count = len(markdown_content.split())
        wpm = toc_settings.get("words_per_minute", 200)
        reading_time = max(1, round(word_count / wpm))
        time_text = f"<i>Estimated reading time: {reading_time} min</i>"
        flowables.append(Paragraph(time_text, styles["TOCEntry"]))

    flowables.append(Spacer(1, 8))

    for level, heading in filtered_headings:
        indent = (level - 1) * 20
        style = ParagraphStyle(
            name=f"TOCLevel{level}",
            parent=styles["TOCEntry"],
            leftIndent=indent,
            fontName="Helvetica-Bold" if level == 1 else "Helvetica",
            fontSize=12 if level == 1 else 11,
        )

        # Format the heading display text
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
    divider = Table([[""]], colWidths=[2 * inch])
    divider.setStyle(
        TableStyle(
            [
                ("LINEABOVE", (0, 0), (-1, -1), 2, PALETTE["accent"]),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
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
        [[Paragraph(inline_md(text), styles["SectionBanner"])]], colWidths=[6.9 * inch]
    )
    banner.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PALETTE["accent"]),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
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
    add_figure_number: bool = True,
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
        return [
            Paragraph(f"Image placeholder: {inline_md(alt)}", styles["ImageCaption"])
        ]

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


def make_code_block(
    code: str,
    styles: dict,
    max_height: float = 8.5 * inch,
    language: str = "python",
    code_settings: dict = None,
) -> list:
    """
    Create formatted code block with optional line numbers and syntax highlighting.

    Args:
        code: Code content
        styles: ReportLab styles dictionary
        max_height: Maximum height for code block
        language: Programming language for syntax highlighting
        code_settings: Code settings dictionary with keys:
            - show_line_numbers: bool
            - syntax_highlighting: bool
            - max_lines_per_page: int
            - font_size: int
            - line_number_color: str

    Returns:
        List of flowables with code block styling
    Invoked by: (no references found)
    """
    # Default settings
    if code_settings is None:
        code_settings = {
            "show_line_numbers": True,
            "syntax_highlighting": False,  # Requires pygments
            "max_lines_per_page": 50,
            "font_size": 9,
            "line_number_color": "#888888",
        }

    lines = code.splitlines() or [""]
    show_line_numbers = code_settings.get("show_line_numbers", True)

    # Heuristic language detection for better code headers when language tags are missing.
    detected_language = language or "code"
    if detected_language == "python":
        code_lower = code.lower()
        if re.search(r"\b(select|insert|update|delete|create table|alter table)\b", code_lower):
            detected_language = "sql"
        elif re.search(r"^\s*(sudo|apt|pip|npm|docker|kubectl|curl|export)\b", code_lower, re.M):
            detected_language = "bash"
        elif code.strip().startswith("{") and ":" in code:
            detected_language = "json"

    # Calculate line height
    leading = styles["CodeBlock"].leading or (styles["CodeBlock"].fontSize * 1.2)
    max_lines = code_settings.get("max_lines_per_page", 50)
    max_lines = min(max_lines, max(1, int((max_height - 12) // leading)))

    flow: list = []

    for i in range(0, len(lines), max_lines):
        chunk_lines = lines[i : i + max_lines]

        if show_line_numbers:
            # Add line numbers to each line
            numbered_lines = []
            for idx, line in enumerate(chunk_lines, start=i + 1):
                # Format: line number (right-aligned, 4 chars) + separator + code
                line_num = f"{idx:4d}"
                # Use ASCII separator to avoid font/encoding issues in PDFs.
                numbered_lines.append(f"{line_num} | {line}")

            chunk = "\n".join(numbered_lines)
        else:
            chunk = "\n".join(chunk_lines)

        block = Preformatted(chunk, styles["CodeBlock"])
        header_label = f"{detected_language.upper()} Code"
        if i > 0:
            header_label += " (continued)"
        header = Paragraph(header_label, styles.get("CodeHeader", styles["BodyText"]))

        table = Table([[header], [block]], colWidths=[6.9 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), PALETTE["panel"]),
                    ("BACKGROUND", (0, 1), (-1, -1), PALETTE["code"]),
                    ("BOX", (0, 0), (-1, -1), 0.8, PALETTE["line"]),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.6, PALETTE["line"]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, 0), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 3),
                    ("TOPPADDING", (0, 1), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
                ]
            )
        )
        flow.append(table)
        if i + max_lines < len(lines):
            flow.append(Spacer(1, 6))

    return flow


def render_mermaid(
    mermaid_text: str, image_cache: Path, mmdc_path: Path | None = None
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
                str(mmdc_path),
                "-i",
                str(temp_path),
                "-o",
                str(out_path),
                "-b",
                "transparent",
                "-w",
                "1600",
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


def render_mermaid_with_gemini(mermaid_text: str, image_cache: Path) -> Path | None:
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
    mermaid_text: str, styles: dict, image_cache: Path, mmdc_path: Path | None = None
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
            colWidths=[6.9 * inch],
        )
        header.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), PALETTE["accent"]),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        flow.append(header)

        # Show a preview of the mermaid code (truncated for display)
        preview_lines = mermaid_text.strip().split("\n")[:8]
        if len(mermaid_text.strip().split("\n")) > 8:
            preview_lines.append("...")
        preview_text = "\n".join(preview_lines)

        code_block = Preformatted(preview_text, styles["CodeBlock"])
        code_table = Table([[code_block]], colWidths=[6.9 * inch])
        code_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), PALETTE["mermaid_bg"]),
                    ("BOX", (0, 0), (-1, -1), 0.8, PALETTE["line"]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
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
    box = Table([[Paragraph(inline_md(text), styles["Quote"])]], colWidths=[6.9 * inch])
    box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F4FBF8")),
                ("BOX", (0, 0), (-1, -1), 1, PALETTE["line"]),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return box


def make_table(table_data: list[list[str]], styles: dict) -> Table:
    """
    Create formatted table from markdown table data with visual enhancements.

    Features:
    - Visual indicators (✓/✗) for boolean values
    - Color coding for performance metrics
    - Improved cell padding and alignment

    Args:
        table_data: 2D list of table cells
        styles: ReportLab styles dictionary

    Returns:
        Table flowable with styling
    Invoked by: (no references found)
    """
    if not table_data:
        return Table([[]])

    # Process cells with visual indicators
    def enhance_cell(cell_text: str) -> str:
        """Add visual indicators to cell content."""
        cell_lower = cell_text.lower().strip()

        # Boolean indicators
        if cell_lower in ["yes", "true", "✓", "pass", "passed"]:
            return f'<font color="green">✓</font> {cell_text}'
        elif cell_lower in ["no", "false", "✗", "fail", "failed"]:
            return f'<font color="red">✗</font> {cell_text}'

        # Performance indicators (percentages)
        if "%" in cell_text:
            try:
                value = float(cell_text.replace("%", "").strip())
                if value >= 90:
                    return f'<font color="green"><b>{cell_text}</b></font>'
                elif value >= 70:
                    return f'<font color="orange">{cell_text}</font>'
                elif value < 50:
                    return f'<font color="red">{cell_text}</font>'
            except ValueError:
                pass

        # Performance tiers
        if cell_lower in ["high", "excellent", "good"]:
            return f'<font color="green"><b>{cell_text}</b></font>'
        elif cell_lower in ["medium", "moderate", "fair"]:
            return f'<font color="orange">{cell_text}</font>'
        elif cell_lower in ["low", "poor", "bad"]:
            return f'<font color="red">{cell_text}</font>'

        return cell_text

    max_cols = max((len(row) for row in table_data), default=1)

    # Process table data with enhancements and normalize column count
    wrapped = []
    for row_idx, row in enumerate(table_data):
        normalized_row = list(row)
        if len(normalized_row) < max_cols:
            normalized_row.extend([""] * (max_cols - len(normalized_row)))
        wrapped_row = []
        for cell in normalized_row:
            # Skip enhancement for header row
            if row_idx == 0:
                wrapped_row.append(Paragraph(inline_md(cell), styles["TableCell"]))
            else:
                enhanced_cell = enhance_cell(cell)
                wrapped_row.append(
                    Paragraph(inline_md(enhanced_cell), styles["TableCell"])
                )
        wrapped.append(wrapped_row)

    col_width = CONTENT_WIDTH / max_cols if max_cols else CONTENT_WIDTH
    table = Table(
        wrapped,
        colWidths=[col_width] * max_cols,
        hAlign="LEFT",
        repeatRows=1,
    )

    # Build table style with alternating row colors
    table_style = [
        ("BACKGROUND", (0, 0), (-1, 0), PALETTE["teal"]),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, PALETTE["line"]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]

    # Add alternating row colors for better readability
    for row_idx in range(1, len(table_data)):
        if row_idx % 2 == 0:
            table_style.append(
                ("BACKGROUND", (0, row_idx), (-1, row_idx), PALETTE["table"])
            )

    table.setStyle(TableStyle(table_style))

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

    # Title styles - Large, impactful blog header
    styles.add(
        ParagraphStyle(
            name="TitleCover",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=42,
            leading=52,
            textColor=PALETTE["ink"],
            spaceAfter=20,
            spaceBefore=40,
            alignment=0,  # Left align for modern blog look
        )
    )

    styles.add(
        ParagraphStyle(
            name="SubtitleCover",
            parent=styles["BodyText"],
            fontName="Helvetica-Oblique",
            fontSize=16,
            leading=24,
            textColor=PALETTE["muted"],
            spaceAfter=32,
        )
    )

    styles.add(
        ParagraphStyle(
            name="CoverKicker",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=PALETTE["accent"],
            spaceAfter=8,
            textTransform="uppercase",
        )
    )

    styles.add(
        ParagraphStyle(
            name="CoverMeta",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=11,
            leading=18,
            textColor=PALETTE["muted"],
            spaceAfter=6,
        )
    )

    # Table of Contents styles
    styles.add(
        ParagraphStyle(
            name="TOCHeading",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=24,
            textColor=PALETTE["accent"],
            spaceBefore=24,
            spaceAfter=12,
        )
    )

    styles.add(
        ParagraphStyle(
            name="TOCEntry",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=11,
            leading=18,
            textColor=PALETTE["ink"],
            leftIndent=12,
            spaceAfter=4,
        )
    )

    # Section banner - Corporate section header
    styles.add(
        ParagraphStyle(
            name="SectionBanner",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=18,
            textColor=colors.white,
        )
    )

    # Heading styles - Clean hierarchy with accent colors
    styles.add(
        ParagraphStyle(
            name="Heading2Custom",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=26,
            leading=34,
            textColor=PALETTE["ink"],
            spaceBefore=28,
            spaceAfter=14,
        )
    )

    styles.add(
        ParagraphStyle(
            name="Heading3Custom",
            parent=styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=26,
            textColor=PALETTE["accent_dark"],
            spaceBefore=20,
            spaceAfter=10,
        )
    )

    # Body text - Comfortable blog-style reading
    styles.add(
        ParagraphStyle(
            name="BodyCustom",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=12,
            leading=19,
            textColor=PALETTE["ink"],
            spaceAfter=10,
            alignment=0,  # Left align for better readability
        )
    )

    # Lead paragraph - First paragraph with emphasis
    styles.add(
        ParagraphStyle(
            name="LeadParagraph",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=13,
            leading=22,
            textColor=PALETTE["ink"],
            spaceAfter=12,
            alignment=0,
        )
    )

    # Bullets - Clean corporate bullets
    styles.add(
        ParagraphStyle(
            name="BulletCustom",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=11,
            leading=17,
            leftIndent=22,
            bulletIndent=10,
            spaceAfter=4,
            textColor=PALETTE["ink"],
        )
    )

    # Code block - Professional code styling
    styles.add(
        ParagraphStyle(
            name="CodeBlock",
            parent=styles["BodyText"],
            fontName="Courier",
            fontSize=9,
            leading=13,
            leftIndent=8,
            rightIndent=8,
            spaceAfter=10,
            textColor=PALETTE["ink"],
        )
    )

    # Image caption - Professional centered caption
    styles.add(
        ParagraphStyle(
            name="ImageCaption",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=PALETTE["muted"],
            alignment=1,  # Center
            spaceAfter=14,
            spaceBefore=4,
        )
    )

    # Quote - Professional blockquote with accent
    styles.add(
        ParagraphStyle(
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
        )
    )

    # Table cell - Professional table styling
    styles.add(
        ParagraphStyle(
            name="TableCell",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=PALETTE["ink"],
            alignment=0,
            wordWrap="CJK",
        )
    )

    # Featured/Hero image style
    styles.add(
        ParagraphStyle(
            name="HeroCaption",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=16,
            textColor=PALETTE["accent"],
            alignment=1,  # Center
            spaceAfter=20,
        )
    )

    # Key Takeaways style
    styles.add(
        ParagraphStyle(
            name="KeyTakeaway",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=18,
            textColor=PALETTE["ink"],
            leftIndent=16,
            spaceAfter=8,
        )
    )

    # Code header - Small label above code blocks
    styles.add(
        ParagraphStyle(
            name="CodeHeader",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=PALETTE["accent_dark"],
            spaceAfter=2,
        )
    )

    return styles
