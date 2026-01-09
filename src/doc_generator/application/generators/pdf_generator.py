"""
PDF generator using ReportLab.

Generates blog-style PDF documents from structured markdown content with
inline visualizations.
"""

from pathlib import Path

from loguru import logger
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from ...domain.exceptions import GenerationError
from ...infrastructure.pdf_utils import (
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
)
from ...infrastructure.settings import get_settings
from ...utils.image_utils import resolve_image_path


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
        """
        settings = get_settings()
        self.image_cache = image_cache or Path(settings.pdf.image_cache_dir)
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
        """
        try:
            # Ensure output directory exists
            output_dir.mkdir(parents=True, exist_ok=True)
            self.image_cache.mkdir(parents=True, exist_ok=True)

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
        """
        section_images = section_images or {}
        # Create document with blog-like margins
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=60,
            leftMargin=60,
            topMargin=60,
            bottomMargin=48,
            title=title,
            author=metadata.get("author", ""),
        )

        story = []

        # Hero title section (blog-like)
        story.append(Spacer(1, 24))
        story.append(Paragraph(inline_md(title), self.styles["TitleCover"]))

        subtitle = metadata.get("subtitle", metadata.get("url", ""))
        if subtitle:
            story.append(Paragraph(inline_md(subtitle), self.styles["SubtitleCover"]))

        # Add executive summary if available
        exec_summary = metadata.get("executive_summary", "")
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

        story.append(Spacer(1, 16))

        # Table of contents (blog-like navigation)
        headings = extract_headings(markdown_content)
        if headings:
            story.extend(make_table_of_contents(headings, self.styles))
            story.extend(make_section_divider(self.styles))

        # Track which visualizations we've used (for any remaining at end)
        used_visualizations = set()

        # Track section index for section images
        section_index = -1  # Will be incremented on first ## header

        # Parse and add markdown content with inline visualizations
        for kind, content_item in parse_markdown_lines(markdown_content):
            if kind == "spacer":
                story.append(Spacer(1, 12))

            elif kind == "h1":
                # Major section - add divider before
                story.extend(make_section_divider(self.styles))
                story.append(Paragraph(inline_md(content_item), self.styles["Heading2Custom"]))

            elif kind == "h2":
                section_index += 1
                story.append(Spacer(1, 16))
                story.append(make_banner(content_item, self.styles))
                story.append(Spacer(1, 12))

                # Check for Gemini-generated section image
                if section_index in section_images:
                    img_info = section_images[section_index]
                    img_path = Path(img_info.get("path", ""))
                    if img_path.exists():
                        story.extend(make_image_flowable(
                            img_info.get("section_title", content_item),
                            img_path,
                            self.styles
                        ))
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
                story.append(Spacer(1, 12))
                story.extend(make_mermaid_flowable(content_item, self.styles, self.image_cache))
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

        logger.debug(f"PDF document built with {element_count} elements")

    def _resolve_image_path(self, url: str) -> Path | None:
        """
        Resolve image URL to local path.

        Args:
            url: Image URL or path

        Returns:
            Path to local image or None
        """
        return resolve_image_path(
            url,
            image_cache=self.image_cache,
            rasterize_func=rasterize_svg
        )
