"""
PDF generator using ReportLab.

Generates blog-style PDF documents from structured markdown content with
inline visualizations.
"""

from datetime import datetime
from pathlib import Path
import re

from loguru import logger
from reportlab.lib.pagesizes import letter
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

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
    rasterize_svg,
    reset_figure_counter,
)
from ...settings import get_settings
from ....utils.image_utils import resolve_image_path


class PDFGenerator:
    """
    PDF generator using ReportLab.

    Converts structured markdown content to blog-style PDF with:
    - Inline visualizations where markers appear
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
            content: Structured content dictionary with 'title', 'markdown',
                     'visualizations', and 'marker_to_path' keys
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

            # Get visualizations and marker mapping
            visualizations = content.get("visualizations", [])
            marker_to_path = content.get("marker_to_path", {})
            section_images = content.get("section_images", {})

            # Build visualization lookup by title for inline replacement
            visual_lookup = self._build_visual_lookup(visualizations)

            # Create PDF
            self._create_pdf(
                output_path,
                title,
                markdown_content,
                metadata,
                visualizations,
                marker_to_path,
                visual_lookup,
                section_images
            )

            logger.info(f"PDF generated successfully: {output_path}")

            return output_path

        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            raise GenerationError(f"Failed to generate PDF: {e}")

    def _build_visual_lookup(self, visualizations: list[dict]) -> dict:
        """
        Build lookup dictionary for visualizations by title and type.
        
        Args:
            visualizations: List of visualization dictionaries
            
        Returns:
            Dictionary mapping (type, title) -> visualization dict
        Invoked by: src/doc_generator/infrastructure/generators/pdf/generator.py
        """
        lookup = {}
        for vis in visualizations:
            vis_type = vis.get("type", "")
            title = vis.get("title", "")
            marker_id = vis.get("marker_id", "")
            
            # Index by multiple keys for flexible lookup
            if vis_type and title:
                lookup[(vis_type, title.lower())] = vis
            if marker_id:
                lookup[marker_id] = vis
            if title:
                lookup[title.lower()] = vis
                
        return lookup

    def _find_visualization(
        self, 
        marker_type: str, 
        marker_title: str, 
        visual_lookup: dict
    ) -> dict | None:
        """
        Find a visualization matching a marker.
        
        Args:
            marker_type: Type from the marker (architecture, flowchart, etc.)
            marker_title: Title from the marker
            visual_lookup: Lookup dictionary
            
        Returns:
            Visualization dict or None
        Invoked by: src/doc_generator/infrastructure/generators/pdf/generator.py
        """
        # Try exact match on type + title
        key = (marker_type, marker_title.lower())
        if key in visual_lookup:
            return visual_lookup[key]
        
        # Try title only
        if marker_title.lower() in visual_lookup:
            return visual_lookup[marker_title.lower()]
        
        # Try partial title match
        title_lower = marker_title.lower()
        for k, v in visual_lookup.items():
            if isinstance(k, str) and title_lower in k:
                return v
            if isinstance(k, tuple) and len(k) == 2 and title_lower in k[1]:
                return v
        
        return None

    def _create_pdf(
        self,
        output_path: Path,
        title: str,
        markdown_content: str,
        metadata: dict,
        visualizations: list[dict],
        marker_to_path: dict,
        visual_lookup: dict,
        section_images: dict = None
    ) -> None:
        """
        Create blog-like PDF document with inline visualizations.

        Features:
        - Hero title section with larger typography
        - Table of contents for navigation
        - Section dividers for visual separation
        - Inline SVG visualizations where markers appear
        - Mermaid diagrams rendered as images
        - Gemini-generated images for sections (infographic/decorative)

        Args:
            output_path: Path to output PDF
            title: Document title
            markdown_content: Markdown content to convert
            metadata: Document metadata
            visualizations: List of visualization dictionaries
            marker_to_path: Mapping of marker IDs to file paths
            visual_lookup: Lookup dict for finding visualizations
            section_images: Dict mapping section_id -> image info (from Gemini)
        Invoked by: src/doc_generator/infrastructure/generators/pdf/generator.py
        """
        section_images = section_images or {}
        display_title = self._resolve_display_title(title, markdown_content)

        # Create document with blog-like margins
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=60,
            leftMargin=60,
            topMargin=60,
            bottomMargin=48,
            title=display_title,
            author=metadata.get("author", ""),
        )

        story = []

        # Cover page
        story.append(Spacer(1, 48))
        cover_kicker = metadata.get("content_type", "Document").replace("_", " ").title()
        story.append(Paragraph(inline_md(cover_kicker), self.styles["CoverKicker"]))
        story.append(Paragraph(inline_md(display_title), self.styles["TitleCover"]))

        subtitle = metadata.get("subtitle", metadata.get("url", ""))
        if subtitle:
            story.append(Paragraph(inline_md(subtitle), self.styles["SubtitleCover"]))

        cover_lines = self._build_cover_metadata(metadata)
        if cover_lines:
            story.append(Spacer(1, 12))
            for line in cover_lines:
                story.append(Paragraph(inline_md(line), self.styles["CoverMeta"]))

        story.append(Spacer(1, 16))
        story.extend(make_section_divider(self.styles))
        story.append(PageBreak())

        # Add executive summary if available
        exec_summary = metadata.get("executive_summary", "")

        # Table of contents (blog-like navigation)
        headings = self._filter_cover_heading(
            extract_headings(markdown_content),
            display_title
        )
        if headings:
            story.extend(make_table_of_contents(headings, self.styles))
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

        # Track which visualizations we've used (for any remaining at end)
        used_visualizations = set()

        # Track section id for section images (prefer explicit numbering)
        next_section_id = 1
        skipped_cover_h1 = False

        # Parse and add markdown content with inline visualizations
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
                if section_id in section_images:
                    img_info = section_images[section_id]
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
                # Handle inline visual marker - find and embed the visualization
                marker_type = content_item.get("type", "")
                marker_title = content_item.get("title", "")
                marker_desc = content_item.get("description", "")
                
                # Skip SVG processing if disabled
                if not self.settings.llm.use_claude_for_visuals:
                    logger.debug(f"SVG generation disabled, skipping visual marker: {marker_title}")
                    continue
                
                logger.debug(f"Processing visual marker: {marker_type} - {marker_title}")
                
                # Find matching visualization
                vis = self._find_visualization(marker_type, marker_title, visual_lookup)
                
                if vis and vis.get("path"):
                    svg_path = Path(vis["path"])
                    if svg_path.exists():
                        # Rasterize and embed
                        png_path = rasterize_svg(svg_path, self.image_cache)
                        if png_path:
                            story.append(Spacer(1, 12))
                            story.extend(make_image_flowable(
                                marker_title,
                                png_path,
                                self.styles
                            ))
                            story.append(Spacer(1, 12))
                            used_visualizations.add(vis.get("marker_id", marker_title))
                            logger.debug(f"Embedded visualization inline: {marker_title}")
                        else:
                            # Fallback: show placeholder
                            story.append(Paragraph(
                                f"<i>[Diagram: {inline_md(marker_title)}]</i>",
                                self.styles["ImageCaption"]
                            ))
                    else:
                        logger.warning(f"Visualization file not found: {svg_path}")
                        story.append(Paragraph(
                            f"<i>[Diagram: {inline_md(marker_title)} - {inline_md(marker_desc)}]</i>",
                            self.styles["ImageCaption"]
                        ))
                else:
                    # No visualization generated for this marker - show placeholder
                    logger.debug(f"No visualization found for marker: {marker_title}")
                    story.append(Paragraph(
                        f"<i>[Diagram placeholder: {inline_md(marker_title)}]</i>",
                        self.styles["ImageCaption"]
                    ))

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
                story.append(make_code_block(content_item, self.styles))
                story.append(Spacer(1, 8))

            elif kind == "table":
                story.append(Spacer(1, 8))
                story.append(make_table(content_item, self.styles))
                story.append(Spacer(1, 12))

            else:  # para
                if content_item.strip():
                    story.append(Paragraph(inline_md(content_item), self.styles["BodyCustom"]))

        # Add any remaining visualizations that weren't placed inline
        # (from LLM suggestions or figure parsing fallback)
        # Skip if SVG generation is disabled
        if self.settings.llm.use_claude_for_visuals:
            remaining_visuals = [
                v for v in visualizations 
                if v.get("marker_id", v.get("title", "")) not in used_visualizations
            ]
            
            if remaining_visuals:
                story.append(Spacer(1, 20))
                story.append(make_banner("Additional Diagrams", self.styles))
                story.append(Spacer(1, 12))

                for visual in remaining_visuals:
                    vis_title = visual.get("title", "Visualization")
                    svg_path = visual.get("path", "")

                    if svg_path:
                        svg_path = Path(svg_path)
                        if svg_path.exists():
                            # Rasterize SVG to PNG for PDF embedding
                            png_path = rasterize_svg(svg_path, self.image_cache)
                            if png_path:
                                story.extend(make_image_flowable(vis_title, png_path, self.styles))
                                story.append(Spacer(1, 8))
                                vis_type = visual.get("type", "diagram")
                                logger.debug(f"Added remaining {vis_type} to PDF: {vis_title}")

        # Build PDF
        element_count = len(story)
        doc.build(story)

    def _resolve_section_id(self, title: str, next_id: int) -> tuple[int, int]:
        """
        Resolve section ID from numbered headings, falling back to sequential IDs.
        Invoked by: src/doc_generator/infrastructure/generators/pdf/generator.py, src/doc_generator/infrastructure/generators/pptx/generator.py
        """
        match = re.match(r"^(\\d+)[\\.:\\)\\s]+\\s*(.+)$", title)
        if match:
            section_id = int(match.group(1))
            next_id = max(next_id, section_id + 1)
            return section_id, next_id
        return next_id, next_id + 1

        logger.debug(f"PDF document built with {element_count} elements")

    def _resolve_image_path(self, url: str) -> Path | None:
        """
        Resolve image URL to local path.

        Args:
            url: Image URL or path

        Returns:
            Path to local image or None
        Invoked by: src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/generate_images.py, src/doc_generator/infrastructure/generators/pdf/generator.py, src/doc_generator/infrastructure/generators/pptx/generator.py
        """
        return resolve_image_path(
            url,
            image_cache=self.image_cache,
            rasterize_func=rasterize_svg
        )

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
        """
        Invoked by: src/doc_generator/infrastructure/generators/pdf/generator.py
        """
        self,
        headings: list[tuple[int, str]],
        cover_title: str
    ) -> list[tuple[int, str]]:
        filtered = []
        for level, heading in headings:
            if level == 1 and self._normalize_title(heading) == self._normalize_title(cover_title):
                continue
            filtered.append((level, heading))
        return filtered
