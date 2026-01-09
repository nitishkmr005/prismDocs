"""
Image generation node for LangGraph workflow.

Generates images for document sections using auto-detection to choose
the best image type (infographic, decorative, diagram, chart, mermaid).
Uses Gemini for infographics/decorative, existing SVG generators for diagrams.
"""

import json
import re
from pathlib import Path
from typing import Optional

from loguru import logger

from ...config.prompts.image_prompts import (
    FALLBACK_PROMPTS,
    IMAGE_DETECTION_PROMPT,
    IMAGE_DETECTION_SYSTEM_PROMPT,
)
from ...domain.content_types import ImageType
from ...domain.models import ImageDecision, WorkflowState
from ...infrastructure.gemini_image_generator import (
    GeminiImageGenerator,
    encode_image_base64,
)
from ...infrastructure.settings import get_settings

# Try to import OpenAI for auto-detection
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class ImageTypeDetector:
    """
    Detect the best image type for a section using LLM.
    """

    def __init__(self):
        """Initialize detector with OpenAI client."""
        import os
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        self.settings = get_settings()

        if self.api_key and OPENAI_AVAILABLE:
            self.client = OpenAI(api_key=self.api_key)
            logger.debug("Image type detector initialized with OpenAI")

    def is_available(self) -> bool:
        """Check if detector is available."""
        return self.client is not None

    def detect(self, section_title: str, content: str) -> ImageDecision:
        """
        Detect the best image type for a section.

        Args:
            section_title: Title of the section
            content: Content of the section

        Returns:
            ImageDecision with type, prompt, and confidence
        """
        if not self.is_available():
            logger.debug("Detector not available, using fallback")
            return self._fallback_detection(section_title, content)

        # Truncate content for prompt
        content_preview = content[:1500] if len(content) > 1500 else content

        prompt = IMAGE_DETECTION_PROMPT.format(
            section_title=section_title,
            content_preview=content_preview
        )

        try:
            response = self.client.chat.completions.create(
                model=self.settings.llm.content_model,
                max_tokens=500,
                temperature=0.3,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": IMAGE_DETECTION_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ]
            )

            result = json.loads(response.choices[0].message.content)

            image_type_str = result.get("image_type", "none").lower()
            image_type = self._parse_image_type(image_type_str)

            return ImageDecision(
                image_type=image_type,
                prompt=result.get("prompt", ""),
                section_title=section_title,
                confidence=float(result.get("confidence", 0.8))
            )

        except Exception as e:
            logger.error(f"Image detection failed for '{section_title}': {e}")
            return self._fallback_detection(section_title, content)

    def _parse_image_type(self, type_str: str) -> ImageType:
        """Parse string to ImageType enum."""
        type_map = {
            "infographic": ImageType.INFOGRAPHIC,
            "decorative": ImageType.DECORATIVE,
            "diagram": ImageType.DIAGRAM,
            "chart": ImageType.CHART,
            "mermaid": ImageType.MERMAID,
            "none": ImageType.NONE,
        }
        return type_map.get(type_str.lower(), ImageType.NONE)

    def _fallback_detection(self, section_title: str, content: str) -> ImageDecision:
        """
        Fallback detection using heuristics.

        Args:
            section_title: Title of the section
            content: Content of the section

        Returns:
            ImageDecision based on heuristics
        """
        title_lower = section_title.lower()

        # Introduction/conclusion -> decorative
        if any(word in title_lower for word in ["introduction", "overview", "conclusion", "summary", "key takeaways"]):
            return ImageDecision(
                image_type=ImageType.DECORATIVE,
                prompt=FALLBACK_PROMPTS["decorative"].format(topic=section_title),
                section_title=section_title,
                confidence=0.6
            )

        # Architecture/system -> diagram
        if any(word in title_lower for word in ["architecture", "system", "design", "structure"]):
            return ImageDecision(
                image_type=ImageType.DIAGRAM,
                prompt=FALLBACK_PROMPTS["diagram"].format(topic=section_title),
                section_title=section_title,
                confidence=0.7
            )

        # Comparison/vs -> chart
        if any(word in title_lower for word in ["comparison", "vs", "versus", "benchmark"]):
            return ImageDecision(
                image_type=ImageType.CHART,
                prompt=FALLBACK_PROMPTS["chart"].format(topic=section_title),
                section_title=section_title,
                confidence=0.7
            )

        # Process/flow/steps -> mermaid
        if any(word in title_lower for word in ["process", "flow", "steps", "workflow", "pipeline"]):
            return ImageDecision(
                image_type=ImageType.MERMAID,
                prompt=FALLBACK_PROMPTS["mermaid"],
                section_title=section_title,
                confidence=0.6
            )

        # How/what/why with substantial content -> infographic
        if any(word in title_lower for word in ["how", "what", "why", "understanding", "explained"]):
            if len(content) > 500:
                return ImageDecision(
                    image_type=ImageType.INFOGRAPHIC,
                    prompt=FALLBACK_PROMPTS["infographic"].format(topic=section_title),
                    section_title=section_title,
                    confidence=0.6
                )

        # Default: no image for short sections, infographic for longer ones
        if len(content) < 300:
            return ImageDecision(
                image_type=ImageType.NONE,
                prompt="",
                section_title=section_title,
                confidence=0.5
            )

        return ImageDecision(
            image_type=ImageType.INFOGRAPHIC,
            prompt=FALLBACK_PROMPTS["infographic"].format(topic=section_title),
            section_title=section_title,
            confidence=0.5
        )


def _extract_sections(markdown: str) -> list[dict]:
    """
    Extract sections from markdown content.

    Args:
        markdown: Full markdown content

    Returns:
        List of section dicts with title, content, and position
    """
    sections = []

    # Match ## headers (main sections)
    section_pattern = r'^##\s+(.+?)$'
    matches = list(re.finditer(section_pattern, markdown, re.MULTILINE))

    for i, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()

        # Find end of section (next ## header or end of document)
        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(markdown)

        content = markdown[start:end].strip()

        sections.append({
            "id": i,
            "title": title,
            "content": content,
            "position": match.start()
        })

    return sections


def generate_images_node(state: WorkflowState) -> WorkflowState:
    """
    Generate images for document sections using auto-detection.

    This node:
    1. Extracts sections from the markdown content
    2. Uses LLM to auto-detect the best image type for each section
    3. Routes to appropriate generator (Gemini or SVG)
    4. Stores images with paths and base64 data for embedding

    Args:
        state: Current workflow state

    Returns:
        Updated state with section_images in structured_content
    """
    try:
        structured_content = state.get("structured_content", {})
        markdown = structured_content.get("markdown", "")

        if not markdown:
            logger.debug("No markdown content for image generation")
            return state

        settings = get_settings()
        images_dir = settings.image_generation.images_dir
        images_dir.mkdir(parents=True, exist_ok=True)

        # Extract sections from markdown
        sections = _extract_sections(markdown)
        logger.info(f"Found {len(sections)} sections for image generation")

        if not sections:
            return state

        # Initialize components
        detector = ImageTypeDetector()
        gemini_gen = GeminiImageGenerator()

        section_images = {}
        generated_count = 0
        skipped_count = 0

        for section in sections:
            section_id = section["id"]
            section_title = section["title"]
            section_content = section["content"]

            # Skip sections that already have visual markers (handled by generate_visuals)
            if "[VISUAL:" in section_content:
                logger.debug(f"Skipping section {section_id} - has visual markers")
                skipped_count += 1
                continue

            # Auto-detect image type
            decision = detector.detect(section_title, section_content)
            logger.debug(
                f"Section '{section_title}': {decision.image_type.value} "
                f"(confidence: {decision.confidence:.2f})"
            )

            if decision.image_type == ImageType.NONE:
                skipped_count += 1
                continue

            # Generate image based on type
            image_path: Optional[Path] = None

            if decision.image_type in (ImageType.INFOGRAPHIC, ImageType.DECORATIVE):
                # Use Gemini for infographics and decorative images
                if gemini_gen.is_available():
                    output_path = images_dir / f"section_{section_id}_{decision.image_type.value}.png"
                    image_path = gemini_gen.generate_image(
                        prompt=decision.prompt,
                        image_type=decision.image_type,
                        section_title=section_title,
                        output_path=output_path
                    )
                else:
                    logger.debug(f"Gemini not available, skipping {decision.image_type.value}")

            elif decision.image_type in (ImageType.DIAGRAM, ImageType.CHART):
                # These are handled by generate_visuals_node with SVG
                # We could generate a visual marker here for later processing
                logger.debug(f"Diagram/chart for section {section_id} - handled by visuals node")
                skipped_count += 1
                continue

            elif decision.image_type == ImageType.MERMAID:
                # Mermaid diagrams are rendered inline by PDF generator
                logger.debug(f"Mermaid for section {section_id} - handled inline")
                skipped_count += 1
                continue

            # Store result
            if image_path and image_path.exists():
                embed_base64 = ""
                if settings.image_generation.embed_in_pdf:
                    embed_base64 = encode_image_base64(image_path)

                section_images[section_id] = {
                    "path": str(image_path),
                    "image_type": decision.image_type.value,
                    "section_title": section_title,
                    "prompt": decision.prompt,
                    "confidence": decision.confidence,
                    "embed_base64": embed_base64,
                }
                generated_count += 1
                logger.success(f"Generated {decision.image_type.value} for: {section_title}")

        # Store in structured content
        structured_content["section_images"] = section_images
        state["structured_content"] = structured_content

        logger.info(
            f"Image generation complete: {generated_count} generated, "
            f"{skipped_count} skipped"
        )

    except Exception as e:
        error_msg = f"Image generation failed: {str(e)}"
        state["errors"].append(error_msg)
        logger.error(error_msg)
        logger.exception("Image generation error details:")

    return state
