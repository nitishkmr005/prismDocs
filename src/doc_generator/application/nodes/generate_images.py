"""
Image generation node for LangGraph workflow.

Generates images for document sections using auto-detection to choose
the best image type (infographic or decorative).
Uses Gemini for image generation based on merged markdown content.
Section IDs are synced with title numbering in the markdown file.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

from loguru import logger

from ...domain.prompts.image.image_prompts import (
    CONCEPT_EXTRACTION_PROMPT,
    CONCEPT_EXTRACTION_SYSTEM_PROMPT,
    CONTENT_AWARE_IMAGE_PROMPT,
    IMAGE_STYLE_TEMPLATES,
)
from ...domain.prompts.image.image_generation_prompts import (
    build_alignment_prompt,
    build_image_description_prompt,
    build_prompt_generator_prompt,
    build_prompt_improvement_prompt,
)
from ...domain.content_types import ImageType
from ...domain.models import ImageDecision, WorkflowState
from ...infrastructure.image import (
    GeminiImageGenerator,
    encode_image_base64,
)
from ...infrastructure.observability.opik import log_llm_call
from ...infrastructure.settings import get_settings

# Try to import Gemini client for prompt generation
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    types = None

# Try to import Anthropic for auto-detection (preferred)
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


def _get_gemini_api_key() -> str | None:
    """
    Resolve the Gemini API key from environment variables.
    Invoked by: src/doc_generator/application/nodes/generate_images.py
    """
    import os
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def _create_gemini_client(api_key: str | None):
    """
    Create a Gemini client if possible.
    Invoked by: src/doc_generator/application/nodes/generate_images.py
    """
    if api_key and GENAI_AVAILABLE:
        return genai.Client(api_key=api_key)
    return None


def _extract_required_labels(section_title: str, content: str) -> list[str]:
    """
    Extract required labels from the section text for grounded diagrams.
    Invoked by: src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/generate_images.py
    """
    candidates = [
        "detect_format_node",
        "parse_content_node",
        "transform_content_node",
        "generate_images_node",
        "generate_output_node",
        "validate_output_node",
        "LangGraph",
        "Docling",
        "MarkItDown",
        "ReportLab",
        "python-pptx",
        "Gemini",
        "Gemini Image API",
        "PDF",
        "PPTX",
        "LLM",
    ]
    content_lower = content.lower()
    title_lower = section_title.lower()
    labels = []

    for label in candidates:
        label_lower = label.lower()
        if label_lower in content_lower or label_lower in title_lower:
            labels.append(label)

    node_matches = re.findall(r"\b[a-z_]+_node\b", content)
    for match in node_matches:
        if match not in labels:
            labels.append(match)

    if section_title and section_title not in labels:
        labels.insert(0, section_title)

    return labels


def _has_visual_trigger(content: str) -> bool:
    """
    Heuristic to force visuals for short but diagram-worthy sections.
    Invoked by: src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/generate_images.py
    """
    content_lower = content.lower()
    if "[visual:" in content_lower:
        return True
    triggers = [
        "architecture",
        "workflow",
        "pipeline",
        "flowchart",
        "diagram",
        "process",
        "steps",
        "node",
    ]
    return any(trigger in content_lower for trigger in triggers)


def _extract_visual_hint(content: str) -> dict | None:
    """
    Extract a [VISUAL:type:title:description] hint if present.
    Invoked by: src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/generate_images.py
    """
    match = re.search(r"\[VISUAL:(\w+):([^:]+):([^\]]+)\]", content)
    if not match:
        return None
    return {
        "type": match.group(1).strip(),
        "title": match.group(2).strip(),
        "description": match.group(3).strip(),
    }


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


def _resolve_images_dir(state: WorkflowState, settings) -> Path:
    """
    Resolve the images output directory for the current workflow run.
    Invoked by: src/doc_generator/application/nodes/generate_images.py
    """
    metadata = state.get("metadata", {})
    folder_name = metadata.get("custom_filename") or metadata.get("file_id")
    if not folder_name:
        input_path = state.get("input_path", "")
        if input_path:
            input_p = Path(input_path)
            for part in input_p.parts:
                if part.startswith("f_"):
                    folder_name = part
                    break
            else:
                if input_p.parent.name == "source" and input_p.parent.parent.exists():
                    folder_name = input_p.parent.parent.name
                else:
                    folder_name = input_p.parent.name if input_p.is_file() else input_p.name
        else:
            folder_name = "output"

    topic_output_dir = settings.generator.output_dir / folder_name
    images_dir = topic_output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    return images_dir


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
    detector = ImageTypeDetector()
    provider = metadata.get("image_provider") or settings.image_generation.default_provider
    gemini_gen = None
    if provider == "gemini":
        gemini_gen = GeminiImageGenerator(model=metadata.get("image_model"))
    else:
        logger.info(f"Image provider '{provider}' not supported for raster generation")
    alignment_validator = GeminiImageAlignmentValidator()
    describer = GeminiImageDescriber()
    return detector, gemini_gen, alignment_validator, describer


def _apply_requested_style(decision: ImageDecision, requested_style: str | None) -> None:
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
    if decision.image_type == ImageType.INFOGRAPHIC and not settings.image_generation.enable_infographics:
        return True
    if decision.image_type == ImageType.DECORATIVE and not settings.image_generation.enable_decorative_headers:
        return True
    if decision.image_type == ImageType.MERMAID and not settings.image_generation.enable_diagrams:
        return True
    return False


def _generate_raster_image(
    *,
    images_dir: Path,
    section_id: int,
    section_title: str,
    section_content: str,
    decision: ImageDecision,
    prompt_used: str,
    gemini_gen: GeminiImageGenerator | None,
    alignment_validator: GeminiImageAlignmentValidator,
    max_attempts: int,
) -> tuple[Path | None, str, dict, int, int]:
    """
    Generate or reuse a raster image with optional alignment feedback.
    Invoked by: src/doc_generator/application/nodes/generate_images.py
    """
    if (not gemini_gen or not gemini_gen.is_available()) and not alignment_validator.is_available():
        logger.debug(f"Gemini not available, skipping {decision.image_type.value}")
        return None, prompt_used, {}, 0, 0

    image_path: Optional[Path] = None
    alignment_result: dict = {}
    attempts = 0
    reused_count = 0

    for attempt_index in range(1, max_attempts + 1):
        output_path = _resolve_image_path(
            images_dir,
            section_title,
            section_id,
            attempt_index,
        )

        if attempt_index == 1 and output_path.exists():
            logger.info(f"Reusing existing image for section {section_id}: {section_title}")
            image_path = output_path
            reused_count += 1
        elif gemini_gen and gemini_gen.is_available():
            image_path = gemini_gen.generate_image(
                prompt=prompt_used,
                image_type=decision.image_type,
                section_title=section_title,
                output_path=output_path
            )
        else:
            image_path = None

        attempts = attempt_index

        if not image_path or not image_path.exists():
            logger.warning(
                f"Image generation failed for '{section_title}' "
                f"(attempt {attempt_index}/{max_attempts})"
            )
            continue

        if not alignment_validator.is_available():
            break

        alignment_result = alignment_validator.validate(
            section_title=section_title,
            content=section_content,
            image_path=image_path,
        )

        if alignment_result.get("aligned") is not False:
            break

        if gemini_gen and gemini_gen.is_available():
            notes = alignment_result.get("notes", "")
            visual_feedbacks = alignment_result.get("visual_feedbacks") or []
            label_feedbacks = alignment_result.get("labels_or_text_feedback") or []
            if visual_feedbacks:
                notes += f"\nVisual feedbacks: {', '.join(visual_feedbacks)}"
            if label_feedbacks:
                notes += f"\nLabels/text feedback: {', '.join(label_feedbacks)}"
            revised_prompt = alignment_validator.improve_prompt(
                section_title=section_title,
                content=section_content,
                original_prompt=prompt_used,
                alignment_notes=notes,
            )
            if revised_prompt != prompt_used:
                logger.info(
                    f"Updated prompt after alignment feedback for '{section_title}' "
                    f"(attempt {attempt_index}/{max_attempts})"
                )
            prompt_used = revised_prompt or prompt_used

    return image_path, prompt_used, alignment_result, attempts, reused_count


class GeminiPromptGenerator:
    """Generate image prompts using Gemini LLM based on section content."""

    def __init__(self) -> None:
        """
        Invoked by: (no references found)
        """
        self.api_key = _get_gemini_api_key()
        self.settings = get_settings()
        self.client = _create_gemini_client(self.api_key)
        if self.api_key and self.client is None:
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
        style_hint: str,
        required_labels: list[str],
        visual_hint: dict | None,
    ) -> str:
        """
        Generate an image prompt from content and strict style guidance.
        Invoked by: src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/generate_images.py
        """
        content_preview = content[:2400]
        required_labels_str = ", ".join(required_labels) if required_labels else section_title
        visual_title = visual_hint.get("title") if visual_hint else section_title
        visual_desc = visual_hint.get("description") if visual_hint else ""

        prompt = build_prompt_generator_prompt(
            section_title=section_title,
            content_preview=content_preview,
            style_hint=style_hint,
            required_labels_str=required_labels_str,
            visual_title=visual_title,
            visual_desc=visual_desc,
        )

        model = self.settings.llm.content_model or self.settings.llm.model
        response = self.client.models.generate_content(
            model=model,
            contents=prompt,
        )
        response_text = (response.text or "").strip()
        log_llm_call(
            name="image_prompt",
            prompt=prompt,
            response=response_text,
            provider="gemini",
            model=model,
            metadata={"section_title": section_title, "style_hint": style_hint},
        )
        return response_text


class GeminiImageAlignmentValidator:
    """Validate image alignment against section content using Gemini."""

    def __init__(self) -> None:
        """
        Invoked by: (no references found)
        """
        self.api_key = _get_gemini_api_key()
        self.settings = get_settings()
        self.client = _create_gemini_client(self.api_key)
        if self.api_key and self.client is None:
            logger.warning("google-genai not installed - image alignment validation disabled")

    def is_available(self) -> bool:
        """
        Invoked by: scripts/run_generator.py, src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/nodes/transform_content.py, src/doc_generator/application/workflow/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/transform_content.py, src/doc_generator/infrastructure/generators/pdf/utils.py, src/doc_generator/infrastructure/image/claude_svg.py, src/doc_generator/infrastructure/image/gemini.py, src/doc_generator/infrastructure/llm/content_generator.py, src/doc_generator/infrastructure/llm/service.py, src/doc_generator/infrastructure/pdf_utils.py, src/doc_generator/utils/content_merger.py
        """
        return self.client is not None and types is not None

    def validate(self, section_title: str, content: str, image_path: Path) -> dict:
        """
        Ask Gemini if the image aligns with the section content.
        Invoked by: .claude/skills/pptx/ooxml/scripts/pack.py, .claude/skills/pptx/ooxml/scripts/validate.py, .claude/skills/pptx/ooxml/scripts/validation/base.py, src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/generate_images.py, src/doc_generator/infrastructure/image/validator.py
        """
        try:
            image_bytes = image_path.read_bytes()
        except Exception as exc:
            logger.warning(f"Failed to read image for validation: {exc}")
            return {"aligned": False, "reason": "image_read_failed"}

        image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/png")
        prompt = build_alignment_prompt(section_title, content)

        model = self.settings.llm.content_model or self.settings.llm.model
        response = self.client.models.generate_content(
            model=model,
            contents=[prompt, image_part],
        )
        text = (response.text or "").strip()
        log_llm_call(
            name="image_alignment",
            prompt=prompt,
            response=text,
            provider="gemini",
            model=model,
            metadata={"section_title": section_title},
        )
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"aligned": False, "notes": text[:200]}

    def improve_prompt(
        self,
        section_title: str,
        content: str,
        original_prompt: str,
        alignment_notes: str,
    ) -> str:
        """
        Improve the image prompt using alignment feedback.
        Invoked by: src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/generate_images.py
        """
        if not self.is_available():
            return original_prompt

        prompt = build_prompt_improvement_prompt(
            section_title=section_title,
            content=content,
            original_prompt=original_prompt,
            alignment_notes=alignment_notes,
        )
        model = self.settings.llm.content_model or self.settings.llm.model
        response = self.client.models.generate_content(
            model=model,
            contents=prompt,
        )
        revised = (response.text or "").strip()
        log_llm_call(
            name="image_prompt_improvement",
            prompt=prompt,
            response=revised,
            provider="gemini",
            model=model,
            metadata={"section_title": section_title},
        )
        return revised or original_prompt


class GeminiImageDescriber:
    """Generate a blog-style description for an image using Gemini."""

    def __init__(self) -> None:
        """
        Invoked by: (no references found)
        """
        self.api_key = _get_gemini_api_key()
        self.settings = get_settings()
        self.client = _create_gemini_client(self.api_key)
        if self.api_key and self.client is None:
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
        prompt = build_image_description_prompt(section_title, content)
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


class ConceptExtractor:
    """
    Extract visual concepts from section content using LLM.
    
    This class analyzes the actual content and extracts specific concepts,
    relationships, and technical details that should be visualized.
    
    NOTE: Uses LLM-based concept extraction for consistent, content-aware prompts.
    """

    def __init__(self):
        """
        Initialize extractor with Gemini client (optional).
        Invoked by: (no references found)
        """
        self.api_key = _get_gemini_api_key()
        self.client = _create_gemini_client(self.api_key)
        self.settings = get_settings()

        if self.client:
            logger.debug("Concept extractor initialized with Gemini")
        else:
            logger.warning("Gemini not available - concept extraction disabled")

    def is_available(self) -> bool:
        """
        Check if extractor is available.
        Invoked by: scripts/run_generator.py, src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/nodes/transform_content.py, src/doc_generator/application/workflow/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/transform_content.py, src/doc_generator/infrastructure/generators/pdf/utils.py, src/doc_generator/infrastructure/image/claude_svg.py, src/doc_generator/infrastructure/image/gemini.py, src/doc_generator/infrastructure/llm/content_generator.py, src/doc_generator/infrastructure/llm/service.py, src/doc_generator/infrastructure/pdf_utils.py, src/doc_generator/utils/content_merger.py
        """
        return self.client is not None

    def extract(self, section_title: str, content: str) -> dict:
        """
        Extract visual concepts from section content.

        Args:
            section_title: Title of the section
            content: Content of the section

        Returns:
            Dict with primary_concept, secondary_concepts, recommended_style, key_terms
        Invoked by: src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/generate_images.py
        """
        if not self.is_available():
            raise RuntimeError("Concept extractor not available")

        # Truncate content for prompt (use more content for concept extraction)
        content_preview = content[:3000] if len(content) > 3000 else content

        try:
            prompt = CONCEPT_EXTRACTION_PROMPT.format(
                section_title=section_title,
                content=content_preview
            )
            full_prompt = f"{CONCEPT_EXTRACTION_SYSTEM_PROMPT}\n\n{prompt}"
            model = self.settings.llm.content_model or self.settings.llm.model
            response = self.client.models.generate_content(
                model=model,
                contents=full_prompt,
            )
            response_text = (response.text or "").strip()
            log_llm_call(
                name="image_concept_extraction",
                prompt=full_prompt,
                response=response_text,
                provider="gemini",
                model=model,
                metadata={"section_title": section_title},
            )
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(response_text)
            logger.debug(
                f"Extracted concepts for '{section_title}': "
                f"{result.get('recommended_style', 'unknown')}"
            )
            return result
        except Exception as e:
            logger.error(f"Concept extraction failed for '{section_title}': {e}")
            raise

    def generate_content_aware_prompt(self, concepts: dict) -> str:
        """
        Generate a content-aware image prompt from extracted concepts.

        Args:
            concepts: Dict with extracted concepts

        Returns:
            Detailed image generation prompt
        Invoked by: src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/generate_images.py
        """
        primary = concepts.get("primary_concept", {})
        style = concepts.get("recommended_style", "technical_infographic")
        key_terms = concepts.get("key_terms", [])

        # Get style-specific requirements
        style_requirements = IMAGE_STYLE_TEMPLATES.get(
            style,
            IMAGE_STYLE_TEMPLATES.get("technical_infographic", "")
        )

        # Format elements and relationships
        elements = primary.get("elements", [])
        elements_str = "\n".join(f"- {elem}" for elem in elements) if elements else "- Main concept visualization"

        relationships = primary.get("relationships", [])
        relationships_str = "\n".join(f"- {rel}" for rel in relationships) if relationships else "- Show how concepts connect"

        details = primary.get("details", "")
        key_terms_str = ", ".join(key_terms) if key_terms else "key concepts"
        required_labels = concepts.get("required_labels", [])
        required_labels_str = "\n".join(f"- {label}" for label in required_labels)

        # Generate the prompt using the template
        prompt = CONTENT_AWARE_IMAGE_PROMPT.format(
            style=style.replace("_", " "),
            title=primary.get("title", "Concept Visualization"),
            elements=elements_str,
            relationships=relationships_str,
            details=details,
            key_terms=key_terms_str,
            required_labels=required_labels_str or "- Use labels from the content",
            style_requirements=style_requirements
        )

        return prompt


class ImageTypeDetector:
    """
    Detect the best image type for a section using content-aware concept extraction.
    
    Uses ConceptExtractor to analyze actual content and generate specific,
    content-relevant image prompts instead of generic ones.
    """

    def __init__(self):
        """
        Initialize detector with concept extractor.
        Invoked by: (no references found)
        """
        self.settings = get_settings()
        self.concept_extractor = ConceptExtractor()
        logger.debug("Image type detector initialized with concept extractor")

    def is_available(self) -> bool:
        """
        Check if detector is available.
        Invoked by: scripts/run_generator.py, src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/nodes/transform_content.py, src/doc_generator/application/workflow/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/transform_content.py, src/doc_generator/infrastructure/generators/pdf/utils.py, src/doc_generator/infrastructure/image/claude_svg.py, src/doc_generator/infrastructure/image/gemini.py, src/doc_generator/infrastructure/llm/content_generator.py, src/doc_generator/infrastructure/llm/service.py, src/doc_generator/infrastructure/pdf_utils.py, src/doc_generator/utils/content_merger.py
        """
        return True  # Always available, uses fallback if LLM unavailable

    def detect(self, section_title: str, content: str) -> ImageDecision:
        """
        Detect the best image type and generate content-specific prompt.

        This method:
        1. Extracts visual concepts from the actual content
        2. Generates a detailed, content-specific prompt
        3. Returns an appropriate image type based on concepts

        Args:
            section_title: Title of the section
            content: Content of the section

        Returns:
            ImageDecision with type, content-specific prompt, and confidence
        Invoked by: src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/generate_images.py
        """
        # Skip very short sections unless they clearly need a diagram
        if len(content) < 200 and not _has_visual_trigger(content):
            logger.debug(f"Skipping short section: {section_title}")
            return ImageDecision(
                image_type=ImageType.NONE,
                prompt="",
                section_title=section_title,
                confidence=0.9
            )

        try:
            # Extract concepts from content
            concepts = self.concept_extractor.extract(section_title, content)
            concepts["required_labels"] = _extract_required_labels(section_title, content)
            visual_hint = _extract_visual_hint(content)
            if visual_hint:
                concepts["primary_concept"]["title"] = visual_hint.get("title", section_title)
            
            # Determine image type from extracted concepts
            style = concepts.get("recommended_style", "technical_infographic")
            if visual_hint:
                type_map = {
                    "architecture": "architecture_diagram",
                    "flowchart": "process_flow",
                    "comparison": "comparison_chart",
                    "concept_map": "concept_map",
                    "mind_map": "mind_map",
                    "mermaid": "process_flow",
                }
                style = type_map.get(visual_hint.get("type", ""), style)
            image_type = self._style_to_image_type(style)
            
            # Generate content-aware prompt (Gemini LLM preferred)
            prompt_generator = GeminiPromptGenerator()
            if prompt_generator.is_available():
                prompt = prompt_generator.generate_prompt(
                    section_title=section_title,
                    content=content,
                    style_hint=style,
                    required_labels=concepts.get("required_labels", []),
                    visual_hint=visual_hint,
                )
            else:
                prompt = self.concept_extractor.generate_content_aware_prompt(concepts)
            
            # Calculate confidence based on extraction quality
            primary = concepts.get("primary_concept", {})
            elements = primary.get("elements", [])
            confidence = 0.6 + min(len(elements) * 0.05, 0.3)  # 0.6 - 0.9 based on elements
            
            logger.info(
                f"Content-aware detection for '{section_title}': "
                f"style={style}, type={image_type.value}, elements={len(elements)}"
            )

            return ImageDecision(
                image_type=image_type,
                prompt=prompt,
                section_title=section_title,
                confidence=confidence
            )

        except Exception as e:
            logger.error(f"Content-aware detection failed for '{section_title}': {e}")
            return self._fallback_detection(section_title, content)

    def _style_to_image_type(self, style: str) -> ImageType:
        """
        Convert recommended style to ImageType enum.
        Invoked by: src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/generate_images.py
        """
        style_map = {
            "architecture_diagram": ImageType.INFOGRAPHIC,
            "comparison_chart": ImageType.INFOGRAPHIC,
            "process_flow": ImageType.INFOGRAPHIC,
            "formula_illustration": ImageType.INFOGRAPHIC,
            "handwritten_notes": ImageType.INFOGRAPHIC,
            "technical_infographic": ImageType.INFOGRAPHIC,
        }
        return style_map.get(style, ImageType.INFOGRAPHIC)

    def _fallback_detection(self, section_title: str, content: str) -> ImageDecision:
        """
        Fallback detection using basic keyword analysis.
        Invoked by: src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/generate_images.py
        """
        prompt_generator = GeminiPromptGenerator()
        if prompt_generator.is_available():
            prompt = prompt_generator.generate_prompt(
                section_title=section_title,
                content=content,
                style_hint="technical_infographic",
                required_labels=_extract_required_labels(section_title, content),
                visual_hint=None,
            )
        else:
            prompt = CONTENT_AWARE_IMAGE_PROMPT.format(
                style="technical infographic",
                title=section_title,
                elements="- Core concepts from the section",
                relationships="- Show how concepts connect",
                details="Summarize only what is in the section content.",
                key_terms=section_title,
                required_labels="\n".join(f"- {label}" for label in _extract_required_labels(section_title, content)),
                style_requirements=IMAGE_STYLE_TEMPLATES.get("technical_infographic", ""),
            )

        return ImageDecision(
            image_type=ImageType.INFOGRAPHIC,
            prompt=prompt,
            section_title=section_title,
            confidence=0.5
        )


def _extract_section_number(title: str) -> tuple[int | None, str]:
    """
    Extract section number from title if present.

    Args:
        title: Section title (e.g., "1. Introduction" or "Introduction")

    Returns:
        Tuple of (section_number or None, clean_title)
    Invoked by: src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/generate_images.py
    """
    # Match patterns like "1. Title", "1 Title", "1: Title", "1) Title"
    number_pattern = r'^(\d+)[\.\:\)\s]+\s*(.+)$'
    match = re.match(number_pattern, title)
    if match:
        return int(match.group(1)), match.group(2).strip()
    return None, title


def _extract_sections(markdown: str) -> list[dict]:
    """
    Extract sections from markdown content.

    Section IDs are synced with title numbering when present (e.g., "1. Introduction" -> id 1).
    If no number in title, uses sequential numbering starting from 1.

    Args:
        markdown: Full markdown content

    Returns:
        List of section dicts with id, title, content, and position
    Invoked by: src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/generate_images.py
    """
    sections = []

    # Match ## headers (main sections)
    section_pattern = r'^##\s+(.+?)$'
    matches = list(re.finditer(section_pattern, markdown, re.MULTILINE))

    # Track the next sequential ID for sections without numbers
    next_sequential_id = 1

    for i, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()

        # Find end of section (next ## header or end of document)
        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(markdown)

        content = markdown[start:end].strip()

        # Extract section number from title if present
        section_num, _ = _extract_section_number(title)

        if section_num is not None:
            section_id = section_num
            # Update next sequential ID to be after this numbered section
            next_sequential_id = max(next_sequential_id, section_num + 1)
        else:
            section_id = next_sequential_id
            next_sequential_id += 1

        sections.append({
            "id": section_id,
            "title": title,  # Keep original title for display
            "content": content,
            "position": match.start()
        })

    return sections


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
        images_dir = _resolve_images_dir(state, settings)
        logger.debug(f"Images will be saved to: {images_dir}")

        if _should_skip_generation(metadata, settings):
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
        sections = _extract_sections(markdown)
        logger.info(f"Found {len(sections)} sections for image generation")

        if not sections:
            return state

        detector, gemini_gen, alignment_validator, describer = _init_image_components(metadata, settings)

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
            _apply_requested_style(decision, metadata.get("image_style", "auto"))
            logger.debug(
                f"Section '{section_title}': {decision.image_type.value} "
                f"(confidence: {decision.confidence:.2f})"
            )

            if decision.image_type == ImageType.NONE:
                skipped_count += 1
                continue
            if _should_skip_image_type(decision, settings):
                skipped_count += 1
                continue

            # Generate image based on type
            prompt_used = existing_images.get(section_id, {}).get("prompt") or decision.prompt
            alignment_result = {}
            attempts = 0
            max_attempts = max(1, int(metadata.get("image_alignment_retries", 2)))
            image_path: Optional[Path] = None

            if decision.image_type in (ImageType.INFOGRAPHIC, ImageType.DECORATIVE):
                image_path, prompt_used, alignment_result, attempts, reused_delta = _generate_raster_image(
                    images_dir=images_dir,
                    section_id=section_id,
                    section_title=section_title,
                    section_content=section_content,
                    decision=decision,
                    prompt_used=prompt_used,
                    gemini_gen=gemini_gen,
                    alignment_validator=alignment_validator,
                    max_attempts=max_attempts,
                )
                reused_count += reused_delta
                if image_path is None:
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
