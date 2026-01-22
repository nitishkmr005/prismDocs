"""
Image generation node for LangGraph workflow.

Generates images for document sections using auto-detection to choose
the best image type (infographic or decorative).
Uses Gemini for image generation based on merged markdown content.
Section IDs are synced with title numbering in the markdown file.
"""

from __future__ import annotations

import re
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from pathlib import Path
from typing import Optional

from loguru import logger

from ...domain.prompts.image.image_generation_prompts import (
    build_prompt_generator_prompt,
)
from ...domain.content_types import ImageType
from ...domain.models import ImageDecision, WorkflowState
from ...infrastructure.image import (
    GeminiImageGenerator,
)
from ...infrastructure.observability.opik import log_llm_call
from ...infrastructure.settings import get_settings
from ...utils.gemini_client import create_gemini_client, get_gemini_api_key
from ...utils.images_paths import resolve_images_dir
from ...utils.markdown_sections import extract_sections

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


def _strip_visual_markers(markdown: str) -> str:
    """
    Remove [VISUAL:...] markers from markdown when images are disabled.
    Invoked by: src/doc_generator/application/nodes/generate_images.py
    """
    if not markdown:
        return markdown
    cleaned = re.sub(r"\[VISUAL:[^\]]+\]", "", markdown)
    cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


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


def _temp_image_output_path(output_path: Path) -> Path:
    """Return a temp output path to avoid overwriting on timeout."""
    return output_path.with_name(f"{output_path.stem}_tmp{output_path.suffix}")


def _generate_image_with_timeout(
    *,
    gemini_gen: GeminiImageGenerator,
    prompt: str,
    image_type: ImageType,
    section_title: str,
    output_path: Path,
    timeout_seconds: int,
) -> Path | None:
    """Run image generation with a timeout to allow model fallback."""
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(
            gemini_gen.generate_image,
            prompt=prompt,
            image_type=image_type,
            section_title=section_title,
            output_path=output_path,
        )
        try:
            return future.result(timeout=timeout_seconds)
        except TimeoutError:
            logger.warning(
                "Gemini image generation timed out after %ss for '%s'",
                timeout_seconds,
                section_title,
            )
            return None
        except Exception as e:
            logger.warning(
                "Gemini image generation failed for '%s': %s",
                section_title,
                e,
            )
            return None


def _should_skip_generation(metadata: dict, settings) -> bool:
    """
    Determine if image generation should be skipped for this run.
    Invoked by: src/doc_generator/application/nodes/generate_images.py
    """
    if "skip_image_generation" in metadata:
        return metadata.get("skip_image_generation", False)
    return settings.generator.reuse_cache_by_default


def _init_image_components(metadata: dict, settings):
    """
    Initialize image generation helpers based on configuration.
    Invoked by: src/doc_generator/application/nodes/generate_images.py
    """
    # Get API key from metadata
    api_keys = metadata.get("api_keys", {})
    image_api_key = api_keys.get("image")

    detector = ImageTypeDetector()
    provider = (
        metadata.get("image_provider") or settings.image_generation.default_provider
    )
    gemini_gen = None
    if provider == "gemini":
        gemini_gen = GeminiImageGenerator(
            api_key=image_api_key, model=metadata.get("image_model")
        )
    else:
        logger.info(f"Image provider '{provider}' not supported for raster generation")
    return detector, gemini_gen


def _apply_requested_style(
    decision: ImageDecision, requested_style: str | None
) -> None:
    """
    Apply an explicit image style override from metadata.
    Invoked by: src/doc_generator/application/nodes/generate_images.py
    """
    if not requested_style or requested_style == "auto":
        return
    if requested_style == "decorative":
        decision.image_type = ImageType.DECORATIVE
    elif requested_style == "mermaid":
        decision.image_type = ImageType.MERMAID
    else:
        decision.image_type = ImageType.INFOGRAPHIC


def _should_skip_image_type(decision: ImageDecision, settings) -> bool:
    """
    Check feature flags to decide if this image type should be skipped.
    Invoked by: src/doc_generator/application/nodes/generate_images.py
    """
    if (
        decision.image_type == ImageType.INFOGRAPHIC
        and not settings.image_generation.enable_infographics
    ):
        return True
    if (
        decision.image_type == ImageType.DECORATIVE
        and not settings.image_generation.enable_decorative_headers
    ):
        return True
    if (
        decision.image_type == ImageType.MERMAID
        and not settings.image_generation.enable_diagrams
    ):
        return True
    return False


def _generate_raster_image(
    *,
    images_dir: Path,
    section_id: int,
    section_title: str,
    decision: ImageDecision,
    prompt_used: str,
    gemini_gen: GeminiImageGenerator | None,
    image_api_key: str | None,
    output_format: str,
    output_type: str,
) -> tuple[Path | None, str, dict, int, int]:
    """
    Generate or reuse a raster image with a single pass.
    Invoked by: src/doc_generator/application/nodes/generate_images.py
    """
    if not gemini_gen or not gemini_gen.is_available():
        logger.debug(f"Gemini not available, skipping {decision.image_type.value}")
        return None, prompt_used, {}, 0, 0

    output_path = _resolve_image_path(
        images_dir,
        section_title,
        section_id,
        1,
    )

    if output_path.exists():
        logger.info(f"Reusing existing image for section {section_id}: {section_title}")
        return output_path, prompt_used, {}, 1, 1

    image_path: Path | None = None
    fallback_allowed = _should_fallback_to_flash_image(output_format, output_type)

    if fallback_allowed and gemini_gen.model_name == "gemini-3-pro-image-preview":
        temp_output_path = _temp_image_output_path(output_path)
        image_path = _generate_image_with_timeout(
            gemini_gen=gemini_gen,
            prompt=prompt_used,
            image_type=decision.image_type,
            section_title=section_title,
            output_path=temp_output_path,
            timeout_seconds=180,
        )
        if image_path and image_path.exists():
            if image_path != output_path:
                try:
                    image_path.replace(output_path)
                    image_path = output_path
                except OSError as exc:
                    logger.warning(
                        "Failed to move image output for '%s': %s",
                        section_title,
                        exc,
                    )
            return image_path, prompt_used, {}, 1, 0
    else:
        image_path = gemini_gen.generate_image(
            prompt=prompt_used,
            image_type=decision.image_type,
            section_title=section_title,
            output_path=output_path,
        )
        if image_path and image_path.exists():
            return image_path, prompt_used, {}, 1, 0

    if fallback_allowed and gemini_gen.model_name == "gemini-3-pro-image-preview":
        logger.warning(
            "Image generation failed for '%s' with %s, retrying with gemini-2.5-flash-image",
            section_title,
            gemini_gen.model_name,
        )
        fallback_gen = GeminiImageGenerator(
            api_key=image_api_key or gemini_gen.api_key,
            model="gemini-2.5-flash-image",
        )
        fallback_path = fallback_gen.generate_image(
            prompt=prompt_used,
            image_type=decision.image_type,
            section_title=section_title,
            output_path=output_path,
        )
        if fallback_path and fallback_path.exists():
            return fallback_path, prompt_used, {}, 2, 0

    logger.warning(f"Image generation failed for '{section_title}'")
    return None, prompt_used, {}, 1, 0



def _maybe_load_cached_images(
    images_dir: Path,
    metadata: dict,
    settings,
) -> dict | None:
    """
    Load cached images if generation is skipped and cache matches.
    Invoked by: src/doc_generator/application/nodes/generate_images.py
    """
    if not _should_skip_generation(metadata, settings):
        return None

    # Cache reuse only applies when the content hash matches.
    from ...utils.content_cache import load_existing_images

    content_hash = metadata.get("content_hash")
    section_images = load_existing_images(images_dir, expected_hash=content_hash)
    return section_images or None


def _should_fallback_to_flash_image(output_format: str, output_type: str) -> bool:
    """Return True when fallback to gemini-2.5-flash-image is allowed."""
    if output_format != "pdf":
        return False
    if output_type and output_type != "article_pdf":
        return False
    return True


def _build_section_image_entry(
    *,
    section_id: int,
    section_title: str,
    decision: ImageDecision,
    prompt_used: str,
    image_path: Path,
    attempts: int,
    alignment_result: dict,
    images_dir: Path,
    settings,
) -> dict:
    """
    Build the section image entry for structured content.
    Invoked by: src/doc_generator/application/nodes/generate_images.py
    """
    title_slug = _slugify(section_title)
    # Normalize filename to keep a stable image path per section.
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

    return {
        "path": str(image_path),
        "image_type": decision.image_type.value,
        "section_title": section_title,
        "prompt": prompt_used,
        "confidence": decision.confidence,
        "embed_base64": "",
        "alignment": alignment_result,
        "attempts": attempts,
        "description": "",
    }


def _process_section_image(
    *,
    section: dict,
    existing_images: dict,
    detector: "ImageTypeDetector",
    gemini_gen: GeminiImageGenerator | None,
    settings,
    metadata: dict,
    images_dir: Path,
    output_format: str,
    output_type: str,
) -> tuple[int, dict | None, int, int]:
    """
    Process a single section and return a new image entry if created.
    Invoked by: src/doc_generator/application/nodes/generate_images.py
    """
    section_id = section["id"]
    section_title = section["title"]
    section_content = section["content"]

    # Get API key from metadata
    api_keys = metadata.get("api_keys", {})
    image_api_key = api_keys.get("image")

    # LLM decides image type + prompt based on section content.
    decision = detector.detect(section_title, section_content, api_key=image_api_key)
    _apply_requested_style(decision, metadata.get("image_style", "auto"))
    logger.debug(
        f"Section '{section_title}': {decision.image_type.value} "
        f"(confidence: {decision.confidence:.2f})"
    )

    if decision.image_type == ImageType.NONE:
        return section_id, None, 1, 0
    if _should_skip_image_type(decision, settings):
        return section_id, None, 1, 0
    if decision.image_type == ImageType.MERMAID:
        logger.debug(f"Mermaid for section {section_id} - handled inline")
        return section_id, None, 1, 0

    # Prefer cached prompt to keep outputs stable when reusing images.
    prompt_used = existing_images.get(section_id, {}).get("prompt") or decision.prompt
    # Single-pass image generation (no validation loop).
    image_path, prompt_used, alignment_result, attempts, reused_delta = (
        _generate_raster_image(
            images_dir=images_dir,
            section_id=section_id,
            section_title=section_title,
            decision=decision,
            prompt_used=prompt_used,
            gemini_gen=gemini_gen,
            image_api_key=image_api_key,
            output_format=output_format,
            output_type=output_type,
        )
    )
    if image_path is None:
        return section_id, None, 0, reused_delta

    entry = _build_section_image_entry(
        section_id=section_id,
        section_title=section_title,
        decision=decision,
        prompt_used=prompt_used,
        image_path=image_path,
        attempts=attempts,
        alignment_result=alignment_result,
        images_dir=images_dir,
        settings=settings,
    )
    return section_id, entry, 0, reused_delta


class GeminiPromptGenerator:
    """Generate image prompts using Gemini LLM based on section content."""

    def __init__(self, api_key: str | None = None) -> None:
        """
        Initialize with optional API key from request.

        Args:
            api_key: API key from request headers, falls back to ENV if not provided
        """
        self.api_key = api_key or get_gemini_api_key()
        self.settings = get_settings()
        self.client = create_gemini_client(self.api_key)
        if self.api_key and self.client is None:
            logger.warning(
                "google-genai not installed - image prompt generation disabled"
            )

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
        input_tokens = (
            getattr(usage_metadata, "prompt_token_count", None)
            if usage_metadata
            else None
        )
        output_tokens = (
            getattr(usage_metadata, "candidates_token_count", None)
            if usage_metadata
            else None
        )
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
        return True  # Always available, uses fallback if LLM unavailable

    def detect(
        self, section_title: str, content: str, api_key: str | None = None
    ) -> ImageDecision:
        """
        Detect the best image type and generate content-specific prompt.

        This method:
        1. Extracts visual concepts from the actual content
        2. Generates a detailed, content-specific prompt
        3. Returns an appropriate image type based on concepts

        Args:
            section_title: Title of the section
            content: Content of the section
            api_key: Optional API key from request headers

        Returns:
            ImageDecision with type, content-specific prompt, and confidence
        Invoked by: src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/generate_images.py
        """
        prompt_generator = GeminiPromptGenerator(api_key=api_key)
        if not prompt_generator.is_available():
            logger.warning("Prompt generator unavailable - skipping image generation")
            return ImageDecision(
                image_type=ImageType.NONE,
                prompt="",
                section_title=section_title,
                confidence=0.0,
            )

        prompt = prompt_generator.generate_prompt(
            section_title=section_title, content=content
        )
        if not prompt:
            return ImageDecision(
                image_type=ImageType.NONE,
                prompt="",
                section_title=section_title,
                confidence=0.9,
            )

        return ImageDecision(
            image_type=ImageType.INFOGRAPHIC,
            prompt=prompt,
            section_title=section_title,
            confidence=0.7,
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
    from ...infrastructure.logging_utils import (
        log_node_start,
        log_node_end,
        log_progress,
        log_metric,
        log_subsection,
        log_cache_hit,
        resolve_step_number,
        resolve_total_steps,
    )

    log_node_start(
        "generate_images",
        step_number=resolve_step_number(state, "generate_images", 7),
        total_steps=resolve_total_steps(state, 9),
    )

    try:
        structured_content = state.get("structured_content", {})
        markdown = structured_content.get("markdown", "")

        if not markdown:
            log_node_end("generate_images", success=True, details="No markdown content")
            return state

        settings = get_settings()
        metadata = state.get("metadata", {})

        # Check if image generation is disabled by user preference
        enable_generation = metadata.get("enable_image_generation", True)
        if not enable_generation:
            logger.info("Image generation disabled by user preference")
            cleaned = _strip_visual_markers(markdown)
            structured_content["markdown"] = cleaned
            structured_content["visual_markers"] = []
            structured_content.pop("section_images", None)
            state["structured_content"] = structured_content
            log_node_end(
                "generate_images", success=True, details="Skipped (user disabled)"
            )
            return state

        # Check settings-level master toggle
        if not settings.image_generation.enable_all:
            logger.info("Image generation disabled in settings")
            cleaned = _strip_visual_markers(markdown)
            structured_content["markdown"] = cleaned
            structured_content["visual_markers"] = []
            structured_content.pop("section_images", None)
            state["structured_content"] = structured_content
            log_node_end(
                "generate_images", success=True, details="Skipped (settings disabled)"
            )
            return state

        images_dir = resolve_images_dir(state, settings)
        log_metric("Images Directory", str(images_dir))

        # Reuse cached images when available to avoid regen costs.
        cached_images = _maybe_load_cached_images(images_dir, metadata, settings)
        if cached_images:
            structured_content["section_images"] = cached_images
            state["structured_content"] = structured_content
            log_cache_hit("image")
            log_metric("Cached Images", len(cached_images))
            log_node_end(
                "generate_images",
                success=True,
                details=f"Loaded {len(cached_images)} cached images",
            )
            return state
        if _should_skip_generation(metadata, settings):
            log_progress("Image cache mismatch, regenerating images")

        # Extract sections from markdown
        log_subsection("Extracting Sections")
        sections = extract_sections(markdown)
        log_metric("Sections Found", len(sections))

        if not sections:
            log_node_end("generate_images", success=True, details="No sections found")
            return state

        # Initialize LLM helpers and image generator once per run.
        log_subsection("Initializing Image Generator")
        detector, gemini_gen = _init_image_components(metadata, settings)

        if gemini_gen:
            log_metric("Image Provider", "Gemini Imagen")
        else:
            log_progress("No image generator available")

        existing_images = structured_content.get("section_images", {})
        section_images = dict(existing_images)
        generated_count = 0
        skipped_count = 0
        reused_count = 0

        # Process each section independently to avoid cross-section coupling.
        log_subsection(f"Processing {len(sections)} Sections")
        output_format = state.get("output_format", "")
        output_type = metadata.get("output_type", "")

        for idx, section in enumerate(sections, 1):
            section_title = section["title"]
            log_progress(f"[{idx}/{len(sections)}] {section_title}")

            # Encapsulated per-section logic to keep this loop readable.
            section_id, entry, skipped_delta, reused_delta = _process_section_image(
                section=section,
                existing_images=existing_images,
                detector=detector,
                gemini_gen=gemini_gen,
                settings=settings,
                metadata=metadata,
                images_dir=images_dir,
                output_format=output_format,
                output_type=output_type,
            )
            skipped_count += skipped_delta
            reused_count += reused_delta
            if entry:
                section_images[section_id] = entry
                generated_count += 1
                logger.success(
                    f"Generated {entry.get('image_type', '')} for: "
                    f"{entry.get('section_title', '')}"
                )

        # Store in structured content
        structured_content["section_images"] = section_images
        state["structured_content"] = structured_content

        log_metric("Images Generated", generated_count)
        log_metric("Images Reused", reused_count)
        log_metric("Sections Skipped", skipped_count)

        details = f"{generated_count} generated, {reused_count} reused, {skipped_count} skipped"
        log_node_end("generate_images", success=True, details=details)

    except Exception as e:
        error_msg = f"Image generation failed: {str(e)}"
        state["errors"].append(error_msg)
        logger.error(error_msg)
        logger.exception("Image generation error details:")
        log_node_end("generate_images", success=False, details=error_msg)

    return state
