"""
PDF generator using ReportLab.

Generates blog-style PDF documents from structured markdown content.
"""

from datetime import datetime
from pathlib import Path
import re

from loguru import logger
from reportlab.lib.pagesizes import A4, legal, letter
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ....domain.exceptions import GenerationError
from .utils import (
    create_custom_styles,
    extract_headings,
    inline_md,
    make_banner,
    make_code_block,
    make_image_flowable,
    make_mermaid_flowable,
    make_quote,
    make_section_divider,
    make_table,
    make_table_of_contents,
    parse_markdown_lines,
    reset_figure_counter,
)
from ...settings import get_settings
from ....utils.image_utils import resolve_image_path


class PDFGenerator:
    """
    PDF generator using ReportLab.

    Converts structured markdown content to blog-style PDF with:
    - Mermaid diagrams rendered as images
    - Professional typography and spacing
    """

    def __init__(self, image_cache: Path | None = None):
        """
        Initialize PDF generator.

        Args:
            image_cache: Directory for cached images (optional)
        Invoked by: (no references found)
        """
        self.settings = get_settings()
        # Use provided cache or default to output/temp for rasterized images
        self.image_cache = image_cache or Path(self.settings.generator.temp_dir)
        self.styles = create_custom_styles()

    def generate(self, content: dict, metadata: dict, output_dir: Path) -> Path:
        """
        Generate PDF from structured content.

        Args:
            content: Structured content dictionary with 'title' and 'markdown'
            metadata: Document metadata
            output_dir: Output directory

        Returns:
            Path to generated PDF

        Raises:
            GenerationError: If PDF generation fails
        Invoked by: scripts/generate_from_folder.py, src/doc_generator/application/nodes/generate_output.py, src/doc_generator/application/workflow/nodes/generate_output.py, src/doc_generator/infrastructure/api/routes/generate.py, tests/api/test_generation_service.py
        """
        try:
            # Ensure output directory exists
            output_dir.mkdir(parents=True, exist_ok=True)
            self.image_cache.mkdir(parents=True, exist_ok=True)

            # Reset figure counter for new document
            reset_figure_counter()

            # Get title for document content
            title = metadata.get("title", "document")

            # Check for custom filename for output file
            if "custom_filename" in metadata:
                filename = metadata["custom_filename"]
            else:
                filename = title.replace(" ", "_").replace("/", "_")

            output_path = output_dir / f"{filename}.pdf"

            logger.info(f"Generating PDF: {output_path.name}")

            # Get markdown content
            markdown_content = content.get("markdown", content.get("raw_content", ""))

            if not markdown_content:
                raise GenerationError("No content provided for PDF generation")

            section_images = content.get("section_images", {})

            # Create PDF
            self._create_pdf(
                output_path,
                title,
                markdown_content,
                metadata,
                section_images
            )

            logger.info(f"PDF generated successfully: {output_path}")

            return output_path

        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            raise GenerationError(f"Failed to generate PDF: {e}")

    def _create_pdf(
        self,
        output_path: Path,
        title: str,
        markdown_content: str,
        metadata: dict,
        section_images: dict = None
    ) -> None:
        """
        Create blog-like PDF document with inline media.

        Features:
        - Hero title section with larger typography
        - Table of contents for navigation
        - Section dividers for visual separation
        - Mermaid diagrams rendered as images
        - Gemini-generated images for sections (infographic/decorative)

        Args:
            output_path: Path to output PDF
            title: Document title
            markdown_content: Markdown content to convert
            metadata: Document metadata
            section_images: Dict mapping section_id -> image info (from Gemini)
        Invoked by: src/doc_generator/infrastructure/generators/pdf/generator.py
        """
        section_images = section_images or {}
        display_title = self._resolve_display_title(title, markdown_content)

        margin = self.settings.pdf.margin
        page_size_key = str(self.settings.pdf.page_size or "letter").lower()
        page_sizes = {
            "letter": letter,
            "a4": A4,
            "legal": legal,
        }
        pagesize = page_sizes.get(page_size_key, letter)

        # Create document with configured margins
        from .page_template import NumberedCanvas
        
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=pagesize,
            rightMargin=margin.right,
            leftMargin=margin.left,
            topMargin=margin.top,
            bottomMargin=margin.bottom,
            title=display_title,
            author=metadata.get("author", self.settings.pdf.metadata.default_author),
        )
        
        # Add PDF metadata if enabled
        if self.settings.pdf.metadata.auto_add_metadata:
            doc.author = metadata.get("author", self.settings.pdf.metadata.default_author)
            doc.creator = self.settings.pdf.metadata.default_creator
            doc.subject = metadata.get("subtitle", "")
            
            # Add keywords from metadata
            keywords = metadata.get("keywords", [])
            if isinstance(keywords, list):
                doc.keywords = ", ".join(keywords)
            elif isinstance(keywords, str):
                doc.keywords = keywords
        
        # Configure custom canvas for headers/footers
        def create_canvas(filename, **kwargs):
            canvas_obj = NumberedCanvas(filename, **kwargs)
            canvas_obj.doc_title = display_title
            canvas_obj.show_header = self.settings.pdf.header_footer.show_header
            canvas_obj.show_footer = self.settings.pdf.header_footer.show_footer
            canvas_obj.show_page_numbers = self.settings.pdf.header_footer.show_page_numbers
            canvas_obj.include_watermark = self.settings.pdf.header_footer.include_watermark
            canvas_obj.watermark_text = self.settings.pdf.header_footer.watermark_text
            canvas_obj.watermark_opacity = self.settings.pdf.header_footer.watermark_opacity
            return canvas_obj

        story = []

        # ===== COVER PAGE =====
        # Create a modern blog-style cover page
        
        # Accent bar at top (visual branding element)
        from reportlab.lib import colors as rl_colors
        accent_bar = Table(
            [[""]],
            colWidths=[6.9 * inch],
            rowHeights=[8]
        )
        accent_bar.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), rl_colors.HexColor("#6366f1")),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(accent_bar)
        story.append(Spacer(1, 48))
        
        # Kicker (content type label)
        cover_kicker = metadata.get("content_type", "Document").replace("_", " ").upper()
        story.append(Paragraph(inline_md(cover_kicker), self.styles["CoverKicker"]))
        story.append(Spacer(1, 8))
        
        # Main title - Large and impactful
        story.append(Paragraph(inline_md(display_title), self.styles["TitleCover"]))

        # Subtitle or URL
        subtitle = metadata.get("subtitle", "")
        if not subtitle and metadata.get("url"):
            # Create a cleaner subtitle from URL if available
            subtitle = "Generated from web content"
        if subtitle:
            story.append(Paragraph(inline_md(subtitle), self.styles["SubtitleCover"]))

        # Decorative divider line
        story.append(Spacer(1, 24))
        divider_line = Table(
            [[""]],
            colWidths=[3 * inch],
            rowHeights=[3]
        )
        divider_line.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), rl_colors.HexColor("#6366f1")),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(divider_line)
        story.append(Spacer(1, 24))
        
        # Metadata section with clean formatting
        cover_lines = self._build_cover_metadata(metadata)
        if cover_lines:
            for line in cover_lines:
                story.append(Paragraph(inline_md(line), self.styles["CoverMeta"]))
            story.append(Spacer(1, 16))

        story.append(Spacer(1, 32))
        story.append(PageBreak())

        # Add executive summary if available
        exec_summary = metadata.get("executive_summary", "")

        # Table of contents (blog-like navigation)
        headings = self._filter_cover_heading(
            extract_headings(markdown_content),
            display_title
        )
        if headings:
            # Convert settings to dict for TOC function
            toc_settings = {
                "include_page_numbers": self.settings.pdf.toc.include_page_numbers,
                "max_depth": self.settings.pdf.toc.max_depth,
                "show_reading_time": self.settings.pdf.toc.show_reading_time,
                "words_per_minute": self.settings.pdf.toc.words_per_minute
            }
            story.extend(make_table_of_contents(
                headings, 
                self.styles, 
                markdown_content,
                toc_settings
            ))
            story.append(PageBreak())

        if exec_summary:
            story.append(Spacer(1, 12))
            story.append(make_banner("Executive Summary", self.styles))
            story.append(Spacer(1, 8))
            # Parse summary as markdown (may have bullets)
            for kind, content_item in parse_markdown_lines(exec_summary):
                if kind == "bullets":
                    for item in content_item:
                        story.append(
                            Paragraph(inline_md(item), self.styles["BulletCustom"], bulletText="•")
                        )
                elif kind == "para" and content_item.strip():
                    story.append(Paragraph(inline_md(content_item), self.styles["BodyCustom"]))
            story.append(Spacer(1, 12))
            story.extend(make_section_divider(self.styles))

        # Track section id for section images (prefer explicit numbering)
        next_section_id = 1
        skipped_cover_h1 = False
        section_image_lookup = self._build_section_image_lookup(section_images)

        # Parse and add markdown content with inline media
        for kind, content_item in parse_markdown_lines(markdown_content):
            if kind == "spacer":
                story.append(Spacer(1, 12))

            elif kind == "h1":
                if not skipped_cover_h1 and self._normalize_title(content_item) == self._normalize_title(display_title):
                    skipped_cover_h1 = True
                    continue
                # Major section - add divider before
                story.extend(make_section_divider(self.styles))
                story.append(Paragraph(inline_md(content_item), self.styles["Heading2Custom"]))

            elif kind == "h2":
                section_id, next_section_id = self._resolve_section_id(content_item, next_section_id)
                story.append(Spacer(1, 16))
                story.append(make_banner(content_item, self.styles))
                story.append(Spacer(1, 12))

                # Check for Gemini-generated section image
                img_info = section_images.get(section_id) or section_image_lookup.get(
                    self._normalize_title(content_item)
                )
                if img_info:
                    img_path = Path(img_info.get("path", ""))
                    if img_path.exists():
                        story.extend(make_image_flowable(
                            img_info.get("section_title", content_item),
                            img_path,
                            self.styles
                        ))
                        description = (img_info.get("description") or "").strip()
                        if description:
                            story.append(Paragraph(inline_md(description), self.styles["BodyCustom"]))
                        story.append(Spacer(1, 12))
                        logger.debug(f"Embedded section image for: {content_item}")

            elif kind == "h3":
                story.append(Paragraph(inline_md(content_item), self.styles["Heading3Custom"]))

            elif kind.startswith("h"):
                story.append(Paragraph(inline_md(content_item), self.styles["Heading3Custom"]))

            elif kind == "visual_marker":
                marker_title = content_item.get("title", "diagram")
                logger.debug(f"Skipping visual marker (SVG disabled): {marker_title}")
                continue

            elif kind == "image":
                alt, url = content_item
                # Resolve image path (if local file)
                image_path = self._resolve_image_path(url)
                if image_path:
                    story.append(Spacer(1, 12))
                    story.extend(make_image_flowable(alt, image_path, self.styles))
                    story.append(Spacer(1, 12))
                else:
                    story.append(Paragraph(f"Image: {inline_md(alt)}", self.styles["ImageCaption"]))

            elif kind == "quote":
                story.append(Spacer(1, 8))
                story.append(make_quote(content_item, self.styles))
                story.append(Spacer(1, 12))

            elif kind == "bullets":
                for item in content_item:
                    story.append(
                        Paragraph(inline_md(item), self.styles["BulletCustom"], bulletText="•")
                    )
                story.append(Spacer(1, 8))

            elif kind == "mermaid":
                mermaid_flow = make_mermaid_flowable(content_item, self.styles, self.image_cache)
                if mermaid_flow:
                    story.append(Spacer(1, 12))
                    story.extend(mermaid_flow)
                    story.append(Spacer(1, 12))

            elif kind == "code":
                story.append(Spacer(1, 8))
                # Convert settings to dict for code block function
                code_settings = {
                    "show_line_numbers": self.settings.pdf.code.show_line_numbers,
                    "syntax_highlighting": self.settings.pdf.code.syntax_highlighting,
                    "max_lines_per_page": self.settings.pdf.code.max_lines_per_page,
                    "font_size": self.settings.pdf.code.font_size,
                    "line_number_color": self.settings.pdf.code.line_number_color
                }
                story.extend(make_code_block(
                    content_item, 
                    self.styles,
                    code_settings=code_settings
                ))
                story.append(Spacer(1, 8))

            elif kind == "table":
                story.append(Spacer(1, 8))
                story.append(make_table(content_item, self.styles))
                story.append(Spacer(1, 12))

            else:  # para
                if content_item.strip():
                    story.append(Paragraph(inline_md(content_item), self.styles["BodyCustom"]))

        # Build PDF with custom canvas
        element_count = len(story)
        doc.build(story, canvasmaker=create_canvas)
        logger.debug(f"PDF document built with {element_count} elements")

    def _resolve_section_id(self, title: str, next_id: int) -> tuple[int, int]:
        """
        Resolve section ID from numbered headings, falling back to sequential IDs.
        Invoked by: src/doc_generator/infrastructure/generators/pdf/generator.py, src/doc_generator/infrastructure/generators/pptx/generator.py
        """
        match = re.match(r"^(\d+)[\.:)\s]+\s*(.+)$", title)
        if match:
            section_id = int(match.group(1))
            next_id = max(next_id, section_id + 1)
            return section_id, next_id
        return next_id, next_id + 1

        logger.debug(f"PDF document built with {element_count} elements")

    def _strip_heading_number(self, title: str) -> str:
        """
        Remove numeric prefixes from headings when present.
        Invoked by: src/doc_generator/infrastructure/generators/pdf/generator.py
        """
        match = re.match(r"^\d+[\.:)\s]+\s*(.+)$", title or "")
        return match.group(1).strip() if match else (title or "").strip()

    def _build_section_image_lookup(self, section_images: dict) -> dict[str, dict]:
        """
        Build a lookup for section images by normalized title.
        Invoked by: src/doc_generator/infrastructure/generators/pdf/generator.py
        """
        lookup: dict[str, dict] = {}
        for img_info in section_images.values():
            raw_title = img_info.get("section_title", "")
            for variant in {raw_title, self._strip_heading_number(raw_title)}:
                key = self._normalize_title(variant)
                if key and key not in lookup:
                    lookup[key] = img_info
        return lookup

    def _resolve_image_path(self, url: str) -> Path | None:
        """
        Resolve image URL to local path.

        Args:
            url: Image URL or path

        Returns:
            Path to local image or None
        Invoked by: src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/generate_images.py, src/doc_generator/infrastructure/generators/pdf/generator.py, src/doc_generator/infrastructure/generators/pptx/generator.py
        """
        return resolve_image_path(url)

    def _resolve_display_title(self, metadata_title: str, markdown_content: str) -> str:
        """
        Invoked by: src/doc_generator/infrastructure/generators/pdf/generator.py, src/doc_generator/infrastructure/generators/pptx/generator.py
        """
        raw_title = (metadata_title or "").strip()
        markdown_title = self._extract_markdown_title(markdown_content)
        cleaned_meta = self._clean_title(raw_title)

        if markdown_title and (not raw_title or self._looks_like_placeholder(raw_title)):
            return markdown_title

        return cleaned_meta or markdown_title or "Document"

    def _extract_markdown_title(self, markdown_content: str) -> str:
        """
        Invoked by: src/doc_generator/infrastructure/generators/pdf/generator.py, src/doc_generator/infrastructure/generators/pptx/generator.py
        """
        match = re.search(r"^#\s+(.+)$", markdown_content, re.MULTILINE)
        return match.group(1).strip() if match else ""

    def _looks_like_placeholder(self, title: str) -> bool:
        """
        Invoked by: src/doc_generator/infrastructure/generators/pdf/generator.py, src/doc_generator/infrastructure/generators/pptx/generator.py
        """
        if "/" in title or "\\" in title:
            return True
        if re.search(r"\.(pdf|docx|pptx|md|txt)$", title, re.IGNORECASE):
            return True
        if "_" in title and " " not in title:
            return True
        return False

    def _clean_title(self, title: str) -> str:
        """
        Invoked by: src/doc_generator/infrastructure/generators/pdf/generator.py, src/doc_generator/infrastructure/generators/pptx/generator.py
        """
        if not title:
            return ""
        cleaned = title.strip()
        if "/" in cleaned or "\\" in cleaned:
            parts = [part for part in cleaned.split() if "/" not in part and "\\" not in part]
            cleaned = " ".join(parts) if parts else Path(cleaned).stem
        if re.search(r"\.(pdf|docx|pptx|md|txt)$", cleaned, re.IGNORECASE):
            cleaned = Path(cleaned).stem
        cleaned = cleaned.replace("_", " ").strip()
        return re.sub(r"\s+", " ", cleaned)

    def _build_cover_metadata(self, metadata: dict) -> list[str]:
        """
        Invoked by: src/doc_generator/infrastructure/generators/pdf/generator.py
        """
        lines = []
        author = metadata.get("author")
        authors = metadata.get("authors")
        if authors and isinstance(authors, list):
            author = ", ".join(authors)
        if author:
            lines.append(f"**Author:** {author}")

        generated_date = metadata.get("generated_date")
        formatted_date = self._format_date(generated_date)
        if formatted_date:
            lines.append(f"**Generated:** {formatted_date}")

        source_files = metadata.get("source_files")
        if source_files:
            lines.append(f"**Sources:** {len(source_files)} files")
        else:
            source_file = metadata.get("source_file")
            if source_file:
                lines.append(f"**Source:** {Path(source_file).name}")

        content_type = metadata.get("content_type")
        if content_type:
            lines.append(f"**Content Type:** {content_type.replace('_', ' ').title()}")

        return lines

    def _format_date(self, value: str | datetime | None) -> str:
        """
        Invoked by: src/doc_generator/infrastructure/generators/pdf/generator.py
        """
        if not value:
            return ""
        if isinstance(value, datetime):
            return value.strftime("%b %d, %Y")
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value).strftime("%b %d, %Y")
            except ValueError:
                return value
        return str(value)

    def _normalize_title(self, title: str) -> str:
        """
        Invoked by: src/doc_generator/infrastructure/generators/pdf/generator.py, src/doc_generator/infrastructure/generators/pptx/generator.py
        """
        return re.sub(r"\s+", " ", title or "").strip().lower()

    def _filter_cover_heading(
        self,
        headings: list[tuple[int, str]],
        cover_title: str
    ) -> list[tuple[int, str]]:
        """
        Invoked by: src/doc_generator/infrastructure/generators/pdf/generator.py
        """
        filtered = []
        for level, heading in headings:
            if level == 1 and self._normalize_title(heading) == self._normalize_title(cover_title):
                continue
            filtered.append((level, heading))
        return filtered
