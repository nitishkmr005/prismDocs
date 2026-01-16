"""
PDF from PPTX generator.

Generates PowerPoint presentations and converts them to PDF format.
Supports:
1. LibreOffice headless conversion (primary, high quality)
2. Fallback rendering using slide images
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

from loguru import logger

from ..pptx.generator import PPTXGenerator


class PDFFromPPTXGenerator:
    """PDF from PPTX generator.

    Creates PowerPoint presentations using PPTXGenerator, then converts to PDF.
    """

    def __init__(self, image_cache: Path | None = None):
        """
        Initialize PDF from PPTX generator.

        Args:
            image_cache: Directory for cached images (optional)
        """
        self.pptx_generator = PPTXGenerator()
        self._libreoffice_available = self._check_libreoffice()

    def _check_libreoffice(self) -> bool:
        """Check if LibreOffice is available for conversion."""
        # Check for libreoffice or soffice command
        for cmd in [
            "libreoffice",
            "soffice",
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        ]:
            if shutil.which(cmd):
                logger.debug(f"Found LibreOffice: {cmd}")
                return True

        # On macOS, check for the app bundle
        mac_paths = [
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",
            "/opt/homebrew/bin/soffice",
        ]
        for path in mac_paths:
            if Path(path).exists():
                logger.debug(f"Found LibreOffice: {path}")
                return True

        logger.warning(
            "LibreOffice not found. Install LibreOffice for high-quality PPTX to PDF conversion. "
            "Falling back to basic PDF generation."
        )
        return False

    def generate(self, content: dict, metadata: dict, output_dir: Path) -> str:
        """
        Generate PDF from PPTX.

        First generates PPTX using PPTXGenerator, then converts to PDF.

        Args:
            content: Structured content dictionary with 'title' and 'markdown'
            metadata: Document metadata
            output_dir: Output directory

        Returns:
            Path to generated PDF file
        """
        logger.info("=== Starting PDF from PPTX Generation ===")

        # Step 1: Generate PPTX
        logger.info("Step 1: Generating PPTX...")
        pptx_path = self.pptx_generator.generate(content, metadata, output_dir)
        pptx_file = Path(pptx_path)

        if not pptx_file.exists():
            raise FileNotFoundError(f"PPTX generation failed: {pptx_path}")

        logger.info(f"PPTX generated: {pptx_file.name}")

        # Step 2: Convert PPTX to PDF
        logger.info("Step 2: Converting PPTX to PDF...")

        # PDF output path (same name, different extension)
        pdf_path = pptx_file.with_suffix(".pdf")

        if self._libreoffice_available:
            success = self._convert_with_libreoffice(pptx_file, output_dir)
            if success and pdf_path.exists():
                logger.success(f"PDF created via LibreOffice: {pdf_path.name}")
                # Keep the PPTX as well (user might want both)
                return str(pdf_path)
            else:
                logger.warning("LibreOffice conversion failed, using fallback")

        # Fallback: Generate a PDF with slide-based layout directly
        pdf_path = self._generate_fallback_pdf(content, metadata, output_dir, pptx_file)
        logger.success(f"PDF created via fallback method: {pdf_path}")

        return str(pdf_path)

    def _convert_with_libreoffice(self, pptx_path: Path, output_dir: Path) -> bool:
        """
        Convert PPTX to PDF using LibreOffice headless mode.

        Args:
            pptx_path: Path to PPTX file
            output_dir: Directory for output PDF

        Returns:
            True if conversion succeeded, False otherwise
        """
        # Find LibreOffice executable
        lo_cmd = None
        for cmd in [
            "libreoffice",
            "soffice",
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        ]:
            if shutil.which(cmd):
                lo_cmd = cmd
                break
            if Path(cmd).exists():
                lo_cmd = cmd
                break

        if not lo_cmd:
            return False

        try:
            # Use a temporary directory for the conversion to avoid conflicts
            with tempfile.TemporaryDirectory() as temp_dir:
                # Run LibreOffice in headless mode
                cmd = [
                    lo_cmd,
                    "--headless",
                    "--convert-to",
                    "pdf",
                    "--outdir",
                    temp_dir,
                    str(pptx_path),
                ]

                logger.debug(f"Running: {' '.join(cmd)}")

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=120,  # 2 minute timeout
                )

                if result.returncode != 0:
                    logger.error(f"LibreOffice conversion failed: {result.stderr}")
                    return False

                # Move the generated PDF to output directory
                temp_pdf = Path(temp_dir) / pptx_path.with_suffix(".pdf").name
                if temp_pdf.exists():
                    target_pdf = output_dir / temp_pdf.name
                    shutil.move(str(temp_pdf), str(target_pdf))
                    logger.info(f"PDF moved to: {target_pdf}")
                    return True
                else:
                    logger.error(f"PDF not found in temp dir: {temp_dir}")
                    return False

        except subprocess.TimeoutExpired:
            logger.error("LibreOffice conversion timed out")
            return False
        except Exception as e:
            logger.error(f"LibreOffice conversion error: {e}")
            return False

    def _generate_fallback_pdf(
        self, content: dict, metadata: dict, output_dir: Path, pptx_path: Path
    ) -> str:
        """
        Generate a PDF from structured content using slide-based layout.

        This is a fallback when LibreOffice is not available.
        Creates a presentation-style PDF directly from the content.

        Args:
            content: Structured content dictionary
            metadata: Document metadata
            output_dir: Output directory
            pptx_path: Path to the generated PPTX (for reference)

        Returns:
            Path to generated PDF
        """
        from datetime import datetime
        from reportlab.lib.pagesizes import landscape, A4
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            PageBreak,
            Image,
            Table,
            TableStyle,
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT

        # Create PDF path
        pdf_filename = pptx_path.stem + ".pdf"
        pdf_path = output_dir / pdf_filename

        # Create document with landscape orientation (like slides)
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=landscape(A4),
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
        )

        # Create styles
        styles = getSampleStyleSheet()

        # Slide title style
        slide_title_style = ParagraphStyle(
            "SlideTitle",
            parent=styles["Heading1"],
            fontSize=32,
            leading=38,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=colors.HexColor("#1a365d"),
        )

        # Title slide style
        main_title_style = ParagraphStyle(
            "MainTitle",
            parent=styles["Title"],
            fontSize=44,
            leading=52,
            alignment=TA_CENTER,
            spaceAfter=30,
            textColor=colors.HexColor("#1a365d"),
        )

        # Subtitle style
        subtitle_style = ParagraphStyle(
            "Subtitle",
            parent=styles["Normal"],
            fontSize=18,
            leading=22,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#4a5568"),
        )

        # Bullet style
        bullet_style = ParagraphStyle(
            "SlideBullet",
            parent=styles["Normal"],
            fontSize=18,
            leading=28,
            leftIndent=40,
            bulletIndent=20,
            spaceBefore=8,
            textColor=colors.HexColor("#2d3748"),
        )

        # Build story (content)
        story = []

        # Get content details
        title = content.get("title", metadata.get("title", "Presentation"))
        markdown_content = content.get("markdown", "")
        slides_data = content.get("slides", [])

        # === Title Slide ===
        story.append(Spacer(1, 2 * inch))
        story.append(Paragraph(title, main_title_style))
        story.append(Spacer(1, 0.5 * inch))

        # Add metadata as subtitle
        author = metadata.get("author", "")
        if author:
            story.append(Paragraph(f"By {author}", subtitle_style))

        date_str = datetime.now().strftime("%B %d, %Y")
        story.append(Paragraph(date_str, subtitle_style))
        story.append(PageBreak())

        # === Content Slides ===
        if slides_data:
            # Use LLM-generated slides structure
            for slide in slides_data:
                slide_title = slide.get("title", "")
                bullets = slide.get("bullets", [])

                # Slide title
                story.append(Spacer(1, 0.3 * inch))
                story.append(Paragraph(slide_title, slide_title_style))
                story.append(Spacer(1, 0.3 * inch))

                # Slide bullets
                for bullet in bullets:
                    story.append(Paragraph(f"• {bullet}", bullet_style))

                story.append(PageBreak())
        else:
            # Parse markdown content for slides
            self._add_slides_from_markdown(
                story, markdown_content, slide_title_style, bullet_style
            )

        # Build PDF
        try:
            doc.build(story)
            logger.info(f"Fallback PDF generated: {pdf_path}")
            return str(pdf_path)
        except Exception as e:
            logger.error(f"Failed to generate fallback PDF: {e}")
            raise

    def _add_slides_from_markdown(
        self, story: list, markdown_content: str, title_style, bullet_style
    ) -> None:
        """
        Parse markdown and add slides to the PDF story.

        Args:
            story: ReportLab story list to append to
            markdown_content: Markdown content to parse
            title_style: Style for slide titles
            bullet_style: Style for bullet points
        """
        import re
        from reportlab.platypus import Spacer, Paragraph, PageBreak
        from reportlab.lib.units import inch

        # Split content by H2 headings (slide boundaries)
        sections = re.split(r"^##\s+", markdown_content, flags=re.MULTILINE)

        for section in sections[1:]:  # Skip empty first element
            lines = section.strip().split("\n")
            if not lines:
                continue

            # First line is the slide title
            slide_title = lines[0].strip()
            story.append(Spacer(1, 0.3 * inch))
            story.append(Paragraph(slide_title, title_style))
            story.append(Spacer(1, 0.3 * inch))

            # Process remaining lines as bullets
            for line in lines[1:]:
                line = line.strip()
                if not line:
                    continue

                # Handle bullet points
                if line.startswith("- ") or line.startswith("* "):
                    bullet_text = line[2:]
                    story.append(Paragraph(f"• {bullet_text}", bullet_style))
                elif line.startswith("• "):
                    bullet_text = line[2:]
                    story.append(Paragraph(f"• {bullet_text}", bullet_style))
                elif not line.startswith("#"):
                    # Regular paragraph text
                    story.append(Paragraph(f"• {line}", bullet_style))

            story.append(PageBreak())
