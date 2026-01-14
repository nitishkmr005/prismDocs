"""
Image generation node for LangGraph workflow.

Generates images for document sections using auto-detection to choose
the best image type (infographic or decorative).
Uses Gemini for image generation based on merged markdown content.
Section IDs are synced with title numbering in the markdown file.
"""

import re
import time
from pathlib import Path
from typing import Optional

from loguru import logger

from ...domain.content_types import ImageType
from ...domain.models import ImageDecision, WorkflowState
from ...infrastructure.image import (
    GeminiImageGenerator,
    encode_image_base64,
)
from ...infrastructure.observability.opik import log_llm_call
from ...infrastructure.settings import get_settings
from ....domain.prompts.image.image_generation_prompts import build_prompt_generator_prompt
from ....utils.markdown_sections import extract_sections

# Try to import Gemini client for prompt generation
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    types = None

def _slugify(text: str, max_len: int = 80) -> str:
    """
    Create a safe, ASCII-only filename slug.
    Invoked by: src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/generate_images.py
    """
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_len].strip("-")


def _resolve_image_path(
    images_dir: Path,
    section_title: str,
    section_id: int,
    attempt_index: int,
) -> Path:
    """
    Resolve the output path for a section image using the section title.
    Invoked by: src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/generate_images.py
    """
    title_slug = _slugify(section_title) or f"section-{section_id}"
    if attempt_index > 1:
        return images_dir / f"{title_slug}_{attempt_index}.png"
    return images_dir / f"{title_slug}.png"


class GeminiPromptGenerator:
    """Generate image prompts using Gemini LLM based on section content."""

    def __init__(self) -> None:
        """
        Invoked by: (no references found)
        """
        import os
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.settings = get_settings()
        self.client = None

        if self.api_key and GENAI_AVAILABLE:
            self.client = genai.Client(api_key=self.api_key)
        elif not GENAI_AVAILABLE:
            logger.warning("google-genai not installed - image prompt generation disabled")

    def is_available(self) -> bool:
        """
        Invoked by: scripts/run_generator.py, src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/nodes/transform_content.py, src/doc_generator/application/workflow/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/transform_content.py, src/doc_generator/infrastructure/generators/pdf/utils.py, src/doc_generator/infrastructure/image/claude_svg.py, src/doc_generator/infrastructure/image/gemini.py, src/doc_generator/infrastructure/llm/content_generator.py, src/doc_generator/infrastructure/llm/service.py, src/doc_generator/infrastructure/pdf_utils.py, src/doc_generator/utils/content_merger.py
        """
        return self.client is not None

    def generate_prompt(
        self,
        section_title: str,
        content: str,
    ) -> str:
        """
        Generate an image prompt from content and strict style guidance.
        Invoked by: src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/generate_images.py
        """
        content_preview = content[:2400]
        prompt = build_prompt_generator_prompt(
            section_title=section_title,
            content_preview=content_preview,
        )

        model = self.settings.llm.content_model or self.settings.llm.model
        start_time = time.perf_counter()
        response = self.client.models.generate_content(
            model=model,
            contents=prompt,
        )
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        usage_metadata = getattr(response, "usage_metadata", None)
        input_tokens = getattr(usage_metadata, "prompt_token_count", None) if usage_metadata else None
        output_tokens = getattr(usage_metadata, "candidates_token_count", None) if usage_metadata else None
        response_text = (response.text or "").strip()
        log_llm_call(
            name="image_prompt",
            prompt=prompt,
            response=response_text,
            provider="gemini",
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_ms=duration_ms,
            metadata={"section_title": section_title},
        )
        if response_text.strip().lower() == "none":
            return ""
        return response_text


class GeminiImageDescriber:
    """Generate a blog-style description for an image using Gemini."""

    def __init__(self) -> None:
        """
        Invoked by: (no references found)
        """
        import os
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.settings = get_settings()
        self.client = None

        if self.api_key and GENAI_AVAILABLE:
            self.client = genai.Client(api_key=self.api_key)
        elif not GENAI_AVAILABLE:
            logger.warning("google-genai not installed - image description disabled")

    def is_available(self) -> bool:
        """
        Invoked by: scripts/run_generator.py, src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/nodes/transform_content.py, src/doc_generator/application/workflow/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/transform_content.py, src/doc_generator/infrastructure/generators/pdf/utils.py, src/doc_generator/infrastructure/image/claude_svg.py, src/doc_generator/infrastructure/image/gemini.py, src/doc_generator/infrastructure/llm/content_generator.py, src/doc_generator/infrastructure/llm/service.py, src/doc_generator/infrastructure/pdf_utils.py, src/doc_generator/utils/content_merger.py
        """
        return self.client is not None and types is not None

    def describe(self, section_title: str, content: str, image_path: Path) -> str:
        """
        Describe the image in a short blog-style paragraph.
        Invoked by: src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/generate_images.py
        """
        try:
            image_bytes = image_path.read_bytes()
        except Exception as exc:
            logger.warning(f"Failed to read image for description: {exc}")
            return ""

        image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/png")
        prompt = (
            "Write a concise blog-style description of this image. "
            "Use only what is visible and what is supported by the section content. "
            "Keep it to 2-4 sentences.\n\n"
            f"Section Title: {section_title}\n\n"
            f"Section Content:\n{content[:2000]}"
        )
        model = self.settings.llm.content_model or self.settings.llm.model
        response = self.client.models.generate_content(
            model=model,
            contents=[prompt, image_part],
        )
        response_text = (response.text or "").strip()
        log_llm_call(
            name="image_description",
            prompt=prompt,
            response=response_text,
            provider="gemini",
            model=model,
            metadata={"section_title": section_title},
        )
        return response_text


class ImageTypeDetector:
    """
    Decide whether an image is needed and return a prompt if so.
    """

    def __init__(self):
        """
        Initialize detector.
        Invoked by: (no references found)
        """
        self.settings = get_settings()
        logger.debug("Image type detector initialized")

    def is_available(self) -> bool:
        """
        Check if detector is available.
        Invoked by: scripts/run_generator.py, src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/nodes/transform_content.py, src/doc_generator/application/workflow/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/transform_content.py, src/doc_generator/infrastructure/generators/pdf/utils.py, src/doc_generator/infrastructure/image/claude_svg.py, src/doc_generator/infrastructure/image/gemini.py, src/doc_generator/infrastructure/llm/content_generator.py, src/doc_generator/infrastructure/llm/service.py, src/doc_generator/infrastructure/pdf_utils.py, src/doc_generator/utils/content_merger.py
        """
        return True

    def detect(self, section_title: str, content: str) -> ImageDecision:
        """
        Decide if a section needs an image and produce a prompt.

        Args:
            section_title: Title of the section
            content: Content of the section

        Returns:
            ImageDecision with type and prompt
        Invoked by: src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/generate_images.py
        """
        prompt_generator = GeminiPromptGenerator()
        if not prompt_generator.is_available():
            logger.warning("Prompt generator unavailable - skipping image generation")
            return ImageDecision(
                image_type=ImageType.NONE,
                prompt="",
                section_title=section_title,
                confidence=0.0
            )

        prompt = prompt_generator.generate_prompt(section_title=section_title, content=content)
        if not prompt:
            return ImageDecision(
                image_type=ImageType.NONE,
                prompt="",
                section_title=section_title,
                confidence=0.9
            )

        return ImageDecision(
            image_type=ImageType.INFOGRAPHIC,
            prompt=prompt,
            section_title=section_title,
            confidence=0.7
        )


def generate_images_node(state: WorkflowState) -> WorkflowState:
    """
    Generate images for document sections using auto-detection.

    This node runs after transform_content creates the merged markdown,
    ensuring images are generated from the complete merged content.

    This node:
    1. Extracts sections from the merged markdown content
    2. Syncs section IDs with title numbering (e.g., "1. Introduction" -> id 1)
    3. Uses content analysis to auto-detect the best image type for each section
    4. Generates images using Gemini API (no retries - single attempt per section)
    5. Stores images with paths and base64 data for embedding

    Args:
        state: Current workflow state

    Returns:
        Updated state with section_images in structured_content
    Invoked by: src/doc_generator/application/graph_workflow.py, src/doc_generator/application/workflow/graph.py
    """
    try:
        structured_content = state.get("structured_content", {})
        markdown = structured_content.get("markdown", "")

        if not markdown:
            logger.debug("No markdown content for image generation")
            return state

        settings = get_settings()
        metadata = state.get("metadata", {})

        # Create topic-specific images directory
        # Get folder name from metadata or derive from input path
        folder_name = metadata.get("custom_filename") or metadata.get("file_id")
        if not folder_name:
            input_path = state.get("input_path", "")
            if input_path:
                input_p = Path(input_path)
                # Look for file_id folder (f_xxx) in the path
                # New structure: output/f_xxx/source/file.md
                for part in input_p.parts:
                    if part.startswith("f_"):
                        folder_name = part
                        break
                else:
                    # Fallback: use parent folder name if no f_xxx found
                    # For paths like output/source/file.md use grandparent
                    if input_p.parent.name == "source" and input_p.parent.parent.exists():
                        folder_name = input_p.parent.parent.name
                    else:
                        folder_name = input_p.parent.name if input_p.is_file() else input_p.name
            else:
                folder_name = "output"

        topic_output_dir = settings.generator.output_dir / folder_name
        images_dir = topic_output_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)

        logger.debug(f"Images will be saved to: {images_dir}")

        # Check for skip_image_generation flag
        if "skip_image_generation" in metadata:
            skip_generation = metadata.get("skip_image_generation", False)
        else:
            skip_generation = settings.generator.reuse_cache_by_default
        
        if skip_generation:
            # Load existing images instead of generating new ones (hash-verified)
            from ...utils.content_cache import load_existing_images
            content_hash = metadata.get("content_hash")
            section_images = load_existing_images(images_dir, expected_hash=content_hash)
            if section_images:
                structured_content["section_images"] = section_images
                state["structured_content"] = structured_content
                logger.info(f"Loaded {len(section_images)} existing images (generation skipped)")
                return state
            logger.info("Image cache mismatch, regenerating images")

        # Extract sections from markdown
        sections = extract_sections(markdown)
        logger.info(f"Found {len(sections)} sections for image generation")

        if not sections:
            return state

        # Initialize components
        detector = ImageTypeDetector()
        provider = metadata.get("image_provider") or settings.image_generation.default_provider
        gemini_gen = None
        if provider == "gemini":
            gemini_gen = GeminiImageGenerator(model=metadata.get("image_model"))
        else:
            logger.info(f"Image provider '{provider}' not supported for raster generation")
        describer = GeminiImageDescriber()

        existing_images = structured_content.get("section_images", {})
        section_images = dict(existing_images)
        generated_count = 0
        skipped_count = 0
        reused_count = 0

        section_titles = [section["title"] for section in sections]
        for section in sections:
            section_id = section["id"]
            section_title = section["title"]
            section_content = section["content"]

            # Auto-detect image type
            decision = detector.detect(section_title, section_content)
            requested_style = metadata.get("image_style", "auto")
            if requested_style and requested_style != "auto":
                if requested_style == "decorative":
                    decision.image_type = ImageType.DECORATIVE
                elif requested_style == "mermaid":
                    decision.image_type = ImageType.MERMAID
                else:
                    decision.image_type = ImageType.INFOGRAPHIC
            logger.debug(
                f"Section '{section_title}': {decision.image_type.value} "
                f"(confidence: {decision.confidence:.2f})"
            )

            if decision.image_type == ImageType.NONE:
                skipped_count += 1
                continue
            if decision.image_type == ImageType.INFOGRAPHIC and not settings.image_generation.enable_infographics:
                skipped_count += 1
                continue
            if decision.image_type == ImageType.DECORATIVE and not settings.image_generation.enable_decorative_headers:
                skipped_count += 1
                continue
            if decision.image_type == ImageType.MERMAID and not settings.image_generation.enable_diagrams:
                skipped_count += 1
                continue

            # Generate image based on type
            image_path: Optional[Path] = None
            prompt_used = existing_images.get(section_id, {}).get("prompt") or decision.prompt
            alignment_result = {}
            attempts = 0

            if decision.image_type in (ImageType.INFOGRAPHIC, ImageType.DECORATIVE):
                if not gemini_gen or not gemini_gen.is_available():
                    logger.debug(f"Gemini not available, skipping {decision.image_type.value}")
                    continue

                output_path = _resolve_image_path(
                    images_dir,
                    section_title,
                    section_id,
                    1,
                )
                if output_path.exists():
                    logger.info(f"Reusing existing image for section {section_id}: {section_title}")
                    image_path = output_path
                    reused_count += 1
                    attempts = 1
                else:
                    image_path = gemini_gen.generate_image(
                        prompt=prompt_used,
                        image_type=decision.image_type,
                        section_title=section_title,
                        output_path=output_path
                    )
                    attempts = 1
                    if not image_path or not image_path.exists():
                        logger.warning(f"Image generation failed for '{section_title}'")
                        continue

            elif decision.image_type == ImageType.MERMAID:
                # Mermaid diagrams are rendered inline by PDF generator
                logger.debug(f"Mermaid for section {section_id} - handled inline")
                skipped_count += 1
                continue

            # Store result
            if image_path and image_path.exists():

                prior_info = existing_images.get(section_id, {})
                description = prior_info.get("description", "")
                if describer.is_available():
                    new_description = describer.describe(
                        section_title=section_title,
                        content=section_content,
                        image_path=image_path,
                    ).strip()
                    if new_description:
                        description = new_description
                    else:
                        logger.error(
                            f"Image description missing for section '{section_title}' "
                            f"(path={image_path})"
                        )
                else:
                    logger.error(
                        f"Image description unavailable (Gemini not ready) for section "
                        f"'{section_title}'"
                    )
                description = description.strip()
                title_slug = _slugify(section_title)
                if title_slug:
                    expected = _resolve_image_path(
                        images_dir,
                        section_title,
                        section_id,
                        attempts,
                    )
                    if expected != image_path:
                        try:
                            image_path.rename(expected)
                            image_path = expected
                        except OSError as exc:
                            logger.warning(f"Failed to rename image file: {exc}")

                embed_base64 = ""
                if settings.image_generation.embed_in_pdf:
                    embed_base64 = encode_image_base64(image_path)

                section_images[section_id] = {
                    "path": str(image_path),
                    "image_type": decision.image_type.value,
                    "section_title": section_title,
                    "prompt": prompt_used,
                    "confidence": decision.confidence,
                    "embed_base64": embed_base64,
                    "alignment": alignment_result,
                    "attempts": attempts,
                    "description": description,
                }
                generated_count += 1
                logger.success(f"Generated {decision.image_type.value} for: {section_title}")

        # Store in structured content
        structured_content["section_images"] = section_images
        from ...utils.content_cache import save_image_manifest
        if metadata.get("content_hash"):
            description_map = {
                str(section_id): info.get("description", "")
                for section_id, info in section_images.items()
                if info.get("description")
            }
            section_map = {
                str(section_id): info.get("section_title", "")
                for section_id, info in section_images.items()
                if info.get("section_title")
            }
            image_types = {
                str(section_id): info.get("image_type", "")
                for section_id, info in section_images.items()
                if info.get("image_type")
            }
            save_image_manifest(
                images_dir,
                metadata["content_hash"],
                section_titles,
                descriptions=description_map,
                section_map=section_map,
                image_types=image_types,
            )
        state["structured_content"] = structured_content

        logger.info(
            f"Image generation complete: {generated_count} generated, "
            f"{reused_count} reused, {skipped_count} skipped"
        )

    except Exception as e:
        error_msg = f"Image generation failed: {str(e)}"
        state["errors"].append(error_msg)
        logger.error(error_msg)
        logger.exception("Image generation error details:")

    return state
