"""
PPTX generator using python-pptx.

Generates PowerPoint presentations from structured markdown content.
Supports LLM-enhanced slide generation for executive presentations.
"""

import hashlib
import re
from pathlib import Path

from loguru import logger

from ....domain.exceptions import GenerationError
from ...pdf_utils import parse_markdown_lines
from ...settings import get_settings
from .utils import (
    add_content_slide,
    add_executive_summary_slide,
    add_image_slide,
    add_section_header_slide,
    add_title_slide,
    create_presentation,
    save_presentation,
)
from ...llm.service import LLMService, get_llm_service
from ....utils.image_utils import resolve_image_path


class PPTXGenerator:
    """
    PPTX generator using python-pptx.

    Converts structured markdown content to PowerPoint presentation.
    """

    def __init__(self):
        """
        Initialize PPTX generator.
        Invoked by: (no references found)
        """
        self.settings = get_settings()
        self._image_cache: Path | None = None
        self._max_bullets_per_slide = 5  # Max bullets per content slide
        self._min_bullets_continuation = 3  # Minimum for continuation slides

    def _generate_mermaid_image(self, mermaid_code: str) -> Path | None:
        """
        Generate an image from mermaid code using Gemini.

        Args:
            mermaid_code: Mermaid diagram code

        Returns:
            Path to generated image or None if failed
        Invoked by: (no references found)
        """
        if not self._image_cache:
            return None

        try:
            from ...image.gemini import get_gemini_generator
        except ImportError:
            logger.warning("Gemini generator not available")
            return None

        self._image_cache.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256(mermaid_code.encode("utf-8")).hexdigest()[:12]
        out_path = self._image_cache / f"mermaid-pptx-{digest}.png"

        if out_path.exists():
            return out_path

        generator = get_gemini_generator()
        if not generator.is_available():
            logger.warning("Gemini not available for mermaid rendering")
            return None

        result = generator.generate_diagram_from_mermaid(mermaid_code, out_path)
        return result

    def generate(self, content: dict, metadata: dict, output_dir: Path) -> Path:
        """
        Generate PPTX from structured content.

        Uses LLM-enhanced content when available for executive-quality presentations.

        Args:
            content: Structured content dictionary with 'title', 'markdown',
                     and optional 'slides', 'executive_summary' keys
            metadata: Document metadata
            output_dir: Output directory

        Returns:
            Path to generated PPTX

        Raises:
            GenerationError: If PPTX generation fails
        Invoked by: scripts/generate_from_folder.py, src/doc_generator/application/nodes/generate_output.py, src/doc_generator/application/workflow/nodes/generate_output.py, src/doc_generator/infrastructure/api/routes/generate.py, tests/api/test_generation_service.py
        """
        try:
            # Ensure output directory exists
            output_dir.mkdir(parents=True, exist_ok=True)

            # Set up image cache for mermaid diagrams
            self._image_cache = output_dir / "images"

            # Create output path
            # Get title for presentation content
            markdown_content = content.get("markdown", content.get("raw_content", ""))
            title = self._resolve_display_title(
                metadata.get("title", "presentation"), markdown_content
            )

            # Check for custom filename for output file
            if "custom_filename" in metadata:
                filename = metadata["custom_filename"]
            else:
                filename = title.replace(" ", "_").replace("/", "_")

            output_path = output_dir / f"{filename}.pptx"

            logger.info(f"Generating PPTX: {output_path.name}")

            if not markdown_content:
                raise GenerationError("No content provided for PPTX generation")

            # Check for LLM enhancements
            has_llm_enhancements = any(
                key in content
                for key in ["slides", "executive_summary", "visualizations"]
            )

            if has_llm_enhancements:
                logger.info("Using LLM-enhanced slide generation")

            # Create presentation with full structured content
            self._create_presentation(
                output_path,
                title,
                markdown_content,
                metadata,
                structured_content=content if has_llm_enhancements else None,
            )

            logger.info(f"PPTX generated successfully: {output_path}")

            return output_path

        except Exception as e:
            logger.error(f"PPTX generation failed: {e}")
            raise GenerationError(f"Failed to generate PPTX: {e}")

    def _create_presentation(
        self,
        output_path: Path,
        title: str,
        markdown_content: str,
        metadata: dict,
        structured_content: dict = None,
    ) -> None:
        """
        Create PowerPoint presentation.

        Uses LLM-generated slide structure when available for executive-quality output.

        Args:
            output_path: Path to output PPTX
            title: Presentation title
            markdown_content: Markdown content to convert
            metadata: Document metadata
            structured_content: Optional structured content with LLM enhancements
        Invoked by: src/doc_generator/infrastructure/generators/pptx/generator.py
        """
        # Create presentation
        prs = create_presentation()

        # Add title slide
        subtitle = metadata.get("subtitle", metadata.get("author", ""))
        add_title_slide(prs, title, subtitle)

        agenda_items = self._extract_agenda(markdown_content)
        if agenda_items:
            add_content_slide(prs, "Agenda", agenda_items, is_bullets=True)

        # Check for LLM-enhanced content
        allow_diagrams = metadata.get("enable_pptx_diagrams", False)
        if structured_content:
            # Add executive summary if available
            executive_summary = structured_content.get("executive_summary", "")
            if executive_summary:
                summary_points = [
                    line.strip()
                    for line in executive_summary.split("\n")
                    if line.strip()
                    and (line.strip().startswith("-") or line.strip().startswith("•"))
                ]
                if summary_points:
                    add_executive_summary_slide(
                        prs, "Executive Summary", summary_points
                    )
                    logger.debug("Added executive summary slide")

            embed_images = metadata.get("embed_in_pptx")
            if embed_images is None:
                embed_images = metadata.get(
                    "enable_image_generation",
                    self.settings.image_generation.embed_in_pptx,
                )
            available_images = structured_content.get("section_images", {})
            if not embed_images and available_images:
                logger.info(
                    "Section images present but embedding disabled for PPTX"
                )
            section_images = available_images if embed_images else {}
            section_images = self._normalize_section_images(section_images)
            slides, sections = self._generate_section_slides(
                markdown_content, section_images, metadata
            )
            if slides and sections:
                self._add_llm_section_slides(prs, slides, sections, section_images)
            else:
                self._add_slides_from_markdown(
                    prs, markdown_content, allow_diagrams, section_images=section_images
                )

        else:
            # No LLM enhancement - use markdown-based generation
            self._add_slides_from_markdown(
                prs, markdown_content, allow_diagrams, section_images={}
            )

        # Save presentation
        save_presentation(prs, output_path)

        logger.debug(f"Created presentation with {len(prs.slides)} slides")

    def _add_llm_slides(self, prs, slides: list[dict]) -> None:
        """
        Add slides from LLM-generated structure.

        Args:
            prs: Presentation object
            slides: List of slide dictionaries with title, bullets, speaker_notes
        Invoked by: (no references found)
        """
        for slide_data in slides:
            title = self._strip_inline_markdown(slide_data.get("title", ""))
            bullets = slide_data.get("bullets", [])
            speaker_notes = slide_data.get("speaker_notes", "")

            if title and bullets:
                normalized = self._expand_bullets(bullets)
                self._add_bullet_slide_series(
                    prs, title, normalized, speaker_notes=speaker_notes
                )

        logger.debug(f"Added {len(slides)} LLM-generated slides")

    def _add_section_image_slides(self, prs, section_images: dict) -> None:
        """
        Add slides from Gemini-generated section images.

        Args:
            prs: Presentation object
            section_images: Dict mapping section_id -> image info
        Invoked by: (no references found)
        """
        if not section_images:
            return

        for section_id, img_info in section_images.items():
            title = img_info.get("section_title", f"Section {section_id}")
            img_path = img_info.get("path", "")
            image_type = img_info.get("image_type", "image")

            if not img_path:
                continue

            img_path = Path(img_path)
            if not img_path.exists():
                logger.warning(f"Section image not found: {img_path}")
                continue

            try:
                add_image_slide(
                    prs, title, img_path, f"{image_type.title()} for {title}"
                )
                logger.debug(f"Added {image_type} slide for section: {title}")
            except Exception as e:
                logger.warning(f"Failed to add section image slide: {e}")

    def _add_slides_from_markdown(
        self,
        prs,
        markdown_content: str,
        allow_diagrams: bool = False,
        section_images: dict | None = None,
    ) -> None:
        """
        Parse markdown and add slides to presentation.

        Creates slides based on markdown structure:
        - H1: Section header slides
        - H2: Content slide titles
        - Bullets: Bullet points on content slides
        - Images: Image slides

        Args:
            prs: Presentation object
            markdown_content: Markdown content to parse
        Invoked by: src/doc_generator/infrastructure/generators/pptx/generator.py
        """
        section_images = section_images or {}
        current_slide_title = None
        current_slide_content = []
        next_section_id = 1
        for kind, content_item in parse_markdown_lines(markdown_content):
            # H1 becomes section header
            if kind == "h1":
                content_item = self._strip_inline_markdown(content_item)
                # Flush current slide if any
                if current_slide_title and current_slide_content:
                    self._add_bullet_slide_series(
                        prs, current_slide_title, current_slide_content
                    )
                    current_slide_content = []

                # Add section header
                add_section_header_slide(prs, content_item)
                current_slide_title = None

            # H2 becomes slide title
            elif kind == "h2":
                content_item = self._strip_inline_markdown(content_item)
                section_id, next_section_id = self._resolve_section_id(
                    content_item, next_section_id
                )
                # Flush current slide if any
                if current_slide_title and current_slide_content:
                    self._add_bullet_slide_series(
                        prs, current_slide_title, current_slide_content
                    )

                if section_id in section_images:
                    img_info = section_images[section_id]
                    img_path = Path(img_info.get("path", ""))
                    if img_path.exists():
                        image_type = img_info.get("image_type", "image").title()
                        add_image_slide(
                            prs,
                            content_item,
                            img_path,
                            f"{image_type} for {content_item}",
                        )

                # Start new slide
                current_slide_title = content_item
                current_slide_content = []

            # H3 becomes content item (if no H2 title yet, becomes title)
            elif kind == "h3":
                content_item = self._strip_inline_markdown(content_item)
                if current_slide_title:
                    current_slide_content.append(content_item)
                else:
                    current_slide_title = content_item
                    current_slide_content = []

            # Bullets
            elif kind == "bullets":
                current_slide_content.extend(self._expand_bullets(content_item))

            # Paragraphs
            elif kind == "para":
                if content_item.strip():
                    current_slide_content.extend(self._expand_bullets([content_item]))

            # Images
            elif kind == "image":
                # Flush current slide if any
                if current_slide_title and current_slide_content:
                    self._add_bullet_slide_series(
                        prs, current_slide_title, current_slide_content
                    )
                    current_slide_content = []
                    current_slide_title = None

                alt, url = content_item
                alt = self._strip_inline_markdown(alt)
                image_path = self._resolve_image_path(url)
                if image_path:
                    add_image_slide(prs, alt, image_path, alt)
                else:
                    # Add as text slide if image not found
                    if not current_slide_title:
                        current_slide_title = "Image"
                    current_slide_content.append(f"Image: {alt}")

            # Code blocks, quotes - add as text content
            elif kind in ["code", "quote"]:
                # Truncate long code blocks for slides
                if len(content_item) > 200:
                    content_item = content_item[:200] + "..."
                current_slide_content.append(content_item)

            # Tables - add summary
            elif kind == "table":
                if content_item:
                    current_slide_content.append(f"Table with {len(content_item)} rows")

            # Mermaid diagrams - intentionally skipped
            elif kind == "mermaid":
                continue

            elif kind == "visual_marker":
                continue

        # Flush final slide
        if current_slide_title and current_slide_content:
            self._add_bullet_slide_series(
                prs, current_slide_title, current_slide_content
            )

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

    def _normalize_section_images(self, section_images: dict) -> dict:
        """
        Normalize section_images keys to integers for reliable lookups.
        Invoked by: src/doc_generator/infrastructure/generators/pptx/generator.py
        """
        if not section_images:
            return {}
        normalized: dict[int, dict] = {}
        for key, value in section_images.items():
            try:
                normalized[int(key)] = value
            except (TypeError, ValueError):
                continue
        return normalized or section_images

    def _generate_section_slides(
        self, markdown_content: str, section_images: dict, metadata: dict
    ) -> tuple[list[dict], list[dict]]:
        """
        Invoked by: src/doc_generator/infrastructure/generators/pptx/generator.py
        """
        llm = None
        api_keys = metadata.get("api_keys", {})
        content_key = api_keys.get("content") if isinstance(api_keys, dict) else None
        provider = metadata.get("provider") or self.settings.llm.content_provider
        model = metadata.get("model") or self.settings.llm.content_model
        max_slides = metadata.get("max_slides") or self.settings.llm.max_slides

        if provider == "google":
            provider = "gemini"

        if content_key:
            llm = LLMService(
                api_key=content_key,
                model=model,
                provider=provider,
                max_summary_points=self.settings.llm.max_summary_points,
                max_slides=max_slides,
                max_tokens_summary=self.settings.llm.max_tokens_summary,
                max_tokens_slides=self.settings.llm.max_tokens_slides,
                temperature_summary=self.settings.llm.temperature_summary,
                temperature_slides=self.settings.llm.temperature_slides,
            )

        if llm is None or not llm.is_available():
            llm = get_llm_service(api_key=content_key)
            if max_slides:
                llm.max_slides = max_slides
            if not llm.is_available():
                return [], []

        sections = self._extract_sections(markdown_content, section_images)
        if not sections:
            return [], []

        slides = llm.generate_slide_structure_from_sections(
            sections, max_slides=max_slides
        )
        return slides, sections

    def _extract_sections(
        self, markdown_content: str, section_images: dict
    ) -> list[dict]:
        """
        Extract sections from markdown, deduplicating similar headings.
        Invoked by: src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/generate_images.py, src/doc_generator/infrastructure/generators/pptx/generator.py
        """
        sections = []
        seen_normalized = set()
        current_title = None
        current_lines = []
        next_section_id = 1
        current_section_id = None

        for line in markdown_content.splitlines():
            match = re.match(r"^##\s+(.+)$", line)
            if match:
                # Flush previous section
                if current_title is not None:
                    sections.append(
                        {
                            "title": current_title,
                            "section_id": current_section_id,
                            "content": "\n".join(current_lines).strip(),
                        }
                    )

                new_title = match.group(1).strip()
                normalized = self._normalize_section_title(new_title)

                # Skip duplicate sections
                if normalized in seen_normalized:
                    logger.debug(f"Skipping duplicate section: {new_title}")
                    current_title = None  # Don't process this section
                    current_lines = []
                    continue

                seen_normalized.add(normalized)
                current_title = new_title
                current_section_id, next_section_id = self._resolve_section_id(
                    current_title, next_section_id
                )
                current_lines = []
            elif current_title is not None:
                current_lines.append(line)

        # Flush final section
        if current_title is not None:
            sections.append(
                {
                    "title": current_title,
                    "section_id": current_section_id,
                    "content": "\n".join(current_lines).strip(),
                }
            )

        # Add image hints
        for section in sections:
            section_id = section.get("section_id")
            img_info = section_images.get(section_id)
            if img_info:
                image_type = img_info.get("image_type", "image").title()
                section["image_hint"] = f"{image_type} for {section['title']}"
            else:
                section["image_hint"] = ""

        return sections

    def _add_llm_section_slides(
        self, prs, slides: list[dict], sections: list[dict], section_images: dict
    ) -> None:
        """
        Add slides for each section, using LLM-enhanced bullets when available.

        Falls back to section content if LLM slide matching fails.

        Invoked by: src/doc_generator/infrastructure/generators/pptx/generator.py
        """
        # Build slide lookup by normalized title (with and without numbers)
        slide_map = {}
        for slide in slides:
            section_title = slide.get("section_title", slide.get("title", ""))
            if section_title:
                section_title = self._strip_inline_markdown(section_title)
                # Add both normalized and number-stripped versions
                slide_map[self._normalize_title(section_title)] = slide
                slide_map[self._normalize_section_title(section_title)] = slide

        logger.debug(f"LLM slide map keys: {list(slide_map.keys())[:5]}...")
        slides_added = 0

        for section in sections:
            section_title = section.get("title", "")
            if not section_title:
                continue
            clean_title = self._strip_inline_markdown(section_title)

            # Try to find matching LLM slide (check both normalized versions)
            normalized = self._normalize_title(clean_title)
            normalized_no_num = self._normalize_section_title(clean_title)
            slide = slide_map.get(normalized) or slide_map.get(normalized_no_num)

            # Handle section image first
            img_info = section_images.get(section.get("section_id"))
            if img_info:
                img_path = Path(img_info.get("path", ""))
                if img_path.exists():
                    image_type = img_info.get("image_type", "image").title()
                    add_image_slide(
                        prs,
                        clean_title,
                        img_path,
                        f"{image_type} for {clean_title}",
                    )

            # Get bullets from LLM slide or extract from section content
            bullets = []
            speaker_notes = ""

            if slide:
                bullets = slide.get("bullets", [])
                speaker_notes = slide.get("speaker_notes", "")

            # Fallback: extract bullets from section content if LLM didn't provide them
            if not bullets:
                section_content = section.get("content", "")
                if section_content:
                    bullets = self._extract_bullets_from_content(section_content)

            if bullets:
                self._add_bullet_slide_series(
                    prs, clean_title, bullets, speaker_notes=speaker_notes
                )
                slides_added += 1
            else:
                logger.warning(f"No content for section: {section_title}")

        logger.info(f"Added {slides_added} content slides from sections")

    def _normalize_title(self, title: str) -> str:
        """
        Invoked by: src/doc_generator/infrastructure/generators/pdf/generator.py, src/doc_generator/infrastructure/generators/pptx/generator.py
        """
        return re.sub(r"\s+", " ", title or "").strip().lower()

    def _normalize_section_title(self, title: str) -> str:
        """
        Normalize section title for duplicate detection.
        Removes leading numbers like "1." from "1. Introduction".
        """
        # Remove leading number patterns like "1.", "1)", "1:", "1 "
        cleaned = re.sub(r"^\d+[\.:\)\s]+\s*", "", (title or "").strip())
        return re.sub(r"\s+", " ", cleaned).strip().lower()

    def _extract_bullets_from_content(self, content: str) -> list[str]:
        """
        Extract bullet points from section content.

        Handles markdown bullets, numbered lists, and paragraphs.

        Args:
            content: Raw section content

        Returns:
            List of bullet point strings
        """
        bullets = []

        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue

            # Skip sub-headings
            if line.startswith("#"):
                continue

            # Already a bullet/list item
            if line.startswith(("-", "*", "•")) or re.match(r"^\d+\.", line):
                clean = re.sub(r"^[-*•]\s*", "", line)
                clean = re.sub(r"^\d+\.\s*", "", clean)
                clean = re.sub(r"^\[[xX ]\]\s*", "", clean)
                if clean:
                    bullets.append(self._strip_inline_markdown(clean.strip()))
            # Convert short paragraphs to bullets
            elif len(line) > 20 and len(line) < 300:
                bullets.append(self._strip_inline_markdown(line))

        # If no bullets found, split long content into sentences
        if not bullets and content.strip():
            cleaned_content = self._strip_inline_markdown(content.strip())
            sentences = re.split(r"(?<=[.!?])\s+", cleaned_content)
            bullets = [s.strip() for s in sentences if len(s.strip()) > 20][:6]

        return bullets

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

    def _extract_agenda(self, markdown_content: str) -> list[str]:
        """
        Extract agenda items from markdown, deduplicating similar headings.
        Invoked by: src/doc_generator/infrastructure/generators/pptx/generator.py
        """
        headings = []
        seen_normalized = set()

        for match in re.finditer(r"^##\s+(.+)$", markdown_content, re.MULTILINE):
            heading = self._strip_inline_markdown(match.group(1).strip())
            if not heading:
                continue

            # Normalize to detect duplicates like "Introduction" vs "1. Introduction"
            normalized = self._normalize_section_title(heading)
            if normalized in seen_normalized:
                logger.debug(f"Skipping duplicate agenda item: {heading}")
                continue

            seen_normalized.add(normalized)
            headings.append(heading)

        return headings[:6]

    def _resolve_display_title(self, metadata_title: str, markdown_content: str) -> str:
        """
        Invoked by: src/doc_generator/infrastructure/generators/pdf/generator.py, src/doc_generator/infrastructure/generators/pptx/generator.py
        """
        raw_title = (metadata_title or "").strip()
        markdown_title = self._extract_markdown_title(markdown_content)
        cleaned_meta = self._clean_title(raw_title)

        if markdown_title and (
            not raw_title or self._looks_like_placeholder(raw_title)
        ):
            return markdown_title

        return cleaned_meta or markdown_title or "Presentation"

    def _extract_markdown_title(self, markdown_content: str) -> str:
        """
        Invoked by: src/doc_generator/infrastructure/generators/pdf/generator.py, src/doc_generator/infrastructure/generators/pptx/generator.py
        """
        match = re.search(r"^#\s+(.+)$", markdown_content, re.MULTILINE)
        return self._strip_inline_markdown(match.group(1).strip()) if match else ""

    def _looks_like_placeholder(self, title: str) -> bool:
        """
        Check if title looks like a placeholder/temp file name.

        Detects patterns like:
        - temp_input_abc123
        - Temp Input 4438De0B96A248E4Aca780...
        - file paths
        - filenames with extensions

        Invoked by: src/doc_generator/infrastructure/generators/pdf/generator.py, src/doc_generator/infrastructure/generators/pptx/generator.py
        """
        if "/" in title or "\\" in title:
            return True
        if re.search(r"\.(pdf|docx|pptx|md|txt)$", title, re.IGNORECASE):
            return True
        if "_" in title and " " not in title:
            return True
        # Detect temp input patterns (with or without underscore)
        if re.search(r"temp.?input", title, re.IGNORECASE):
            return True
        # Detect long hex/UUID strings (16+ hex chars)
        if re.search(r"[0-9a-f]{16,}", title, re.IGNORECASE):
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
            parts = [
                part for part in cleaned.split() if "/" not in part and "\\" not in part
            ]
            cleaned = " ".join(parts) if parts else Path(cleaned).stem
        if re.search(r"\.(pdf|docx|pptx|md|txt)$", cleaned, re.IGNORECASE):
            cleaned = Path(cleaned).stem
        cleaned = cleaned.replace("_", " ").strip()
        return re.sub(r"\s+", " ", cleaned)

    def _add_bullet_slide_series(
        self, prs, title: str, bullets: list[str], speaker_notes: str = ""
    ) -> None:
        """
        Invoked by: src/doc_generator/infrastructure/generators/pptx/generator.py
        """
        chunks = list(self._chunk_items(bullets, self._max_bullets_per_slide))
        for idx, chunk in enumerate(chunks):
            slide_title = title if idx == 0 else f"{title} (cont.)"
            add_content_slide(
                prs,
                slide_title,
                chunk,
                is_bullets=True,
                speaker_notes=speaker_notes if idx == 0 else "",
            )

    def _chunk_items(self, items: list[str], chunk_size: int) -> list[list[str]]:
        """
        Split items into chunks with intelligent handling of orphan items.

        Avoids creating continuation slides with just 1-2 items by:
        - Merging small final chunks into the previous slide
        - Ensuring minimum items on continuation slides

        Invoked by: src/doc_generator/infrastructure/generators/pptx/generator.py
        """
        if not items:
            return []

        # Create initial chunks
        chunks = [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]

        # If we have multiple chunks and the last one is too small, merge it
        if len(chunks) > 1 and len(chunks[-1]) < self._min_bullets_continuation:
            # Merge last chunk into previous one
            chunks[-2].extend(chunks[-1])
            chunks.pop()

        return chunks

    def _expand_bullets(self, items: list[str]) -> list[str]:
        """
        Invoked by: src/doc_generator/infrastructure/generators/pptx/generator.py
        """
        expanded = []
        for item in items:
            clean = self._normalize_bullet(item)
            if not clean:
                continue
            expanded.extend(self._split_sentences(clean))
        return expanded

    def _normalize_bullet(self, text: str) -> str:
        """
        Invoked by: src/doc_generator/infrastructure/generators/pptx/generator.py
        """
        cleaned = text.lstrip("•-* ").strip()
        cleaned = re.sub(r"^\d+[\.\)]\s*", "", cleaned)
        cleaned = re.sub(r"^\[[xX ]\]\s*", "", cleaned)
        return self._strip_inline_markdown(cleaned)

    def _split_sentences(self, text: str) -> list[str]:
        """
        Split long text into sentences for slides.

        Uses a higher threshold (180 chars) to keep content together
        and avoid overly fragmented bullet points.

        Invoked by: src/doc_generator/infrastructure/generators/pptx/generator.py
        """
        # Higher threshold for executive presentations - keep content together
        if len(text) < 180:
            return [text]
        parts = [
            part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()
        ]
        if len(parts) > 1:
            return parts
        clauses = [part.strip() for part in re.split(r"[;:]\s+", text) if part.strip()]
        return clauses if len(clauses) > 1 else [text]

    def _strip_inline_markdown(self, text: str) -> str:
        """
        Strip common inline markdown for slide-friendly text.
        Invoked by: src/doc_generator/infrastructure/generators/pptx/generator.py
        """
        if not text:
            return ""
        cleaned = text
        cleaned = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", cleaned)
        cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned)
        cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
        cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", cleaned)
        cleaned = re.sub(r"\*([^*]+)\*", r"\1", cleaned)
        cleaned = re.sub(r"~~([^~]+)~~", r"\1", cleaned)
        cleaned = re.sub(r"<[^>]+>", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned
