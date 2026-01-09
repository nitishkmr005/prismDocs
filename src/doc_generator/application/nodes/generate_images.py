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
    CONCEPT_EXTRACTION_PROMPT,
    CONCEPT_EXTRACTION_SYSTEM_PROMPT,
    CONTENT_AWARE_IMAGE_PROMPT,
    FALLBACK_PROMPTS,
    IMAGE_DETECTION_PROMPT,
    IMAGE_DETECTION_SYSTEM_PROMPT,
    IMAGE_STYLE_TEMPLATES,
)
from ...domain.content_types import ImageType
from ...domain.models import ImageDecision, WorkflowState
from ...infrastructure.gemini_image_generator import (
    GeminiImageGenerator,
    encode_image_base64,
)
from ...infrastructure.settings import get_settings

# Try to import Anthropic for auto-detection (preferred)
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class ConceptExtractor:
    """
    Extract visual concepts from section content using LLM.
    
    This class analyzes the actual content and extracts specific concepts,
    relationships, and technical details that should be visualized.
    """

    def __init__(self):
        """Initialize extractor with Anthropic client."""
        import os
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = None
        self.settings = get_settings()

        if self.api_key and ANTHROPIC_AVAILABLE:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            logger.debug("Concept extractor initialized with Claude")

    def is_available(self) -> bool:
        """Check if extractor is available."""
        return self.client is not None

    def extract(self, section_title: str, content: str) -> dict:
        """
        Extract visual concepts from section content.

        Args:
            section_title: Title of the section
            content: Content of the section

        Returns:
            Dict with primary_concept, secondary_concepts, recommended_style, key_terms
        """
        if not self.is_available():
            logger.debug("Concept extractor not available, using keyword extraction")
            return self._keyword_extraction(section_title, content)

        # Truncate content for prompt (use more content for concept extraction)
        content_preview = content[:3000] if len(content) > 3000 else content

        prompt = CONCEPT_EXTRACTION_PROMPT.format(
            section_title=section_title,
            content=content_preview
        )

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=800,
                messages=[
                    {"role": "user", "content": f"{CONCEPT_EXTRACTION_SYSTEM_PROMPT}\n\n{prompt}"}
                ]
            )

            # Parse JSON from response
            response_text = response.content[0].text
            # Extract JSON from response (might be wrapped in markdown)
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(response_text)

            logger.debug(f"Extracted concepts for '{section_title}': {result.get('recommended_style', 'unknown')}")
            return result

        except Exception as e:
            logger.error(f"Concept extraction failed for '{section_title}': {e}")
            return self._keyword_extraction(section_title, content)

    def _keyword_extraction(self, section_title: str, content: str) -> dict:
        """
        Fallback keyword-based concept extraction.

        Args:
            section_title: Title of the section
            content: Content of the section

        Returns:
            Dict with extracted concepts based on keywords
        """
        content_lower = content.lower()
        
        # Technical concept patterns
        patterns = {
            "architecture": [
                "transformer", "encoder", "decoder", "layer", "block",
                "architecture", "structure", "component", "module"
            ],
            "attention": [
                "attention", "query", "key", "value", "softmax",
                "multi-head", "self-attention", "cross-attention"
            ],
            "position": [
                "position", "embedding", "sinusoidal", "rope", "rotary",
                "positional encoding"
            ],
            "normalization": [
                "normalization", "layernorm", "rmsnorm", "batch norm",
                "normalize"
            ],
            "comparison": [
                "vs", "versus", "compare", "comparison", "different",
                "better", "advantage", "disadvantage"
            ],
            "process": [
                "step", "process", "flow", "pipeline", "sequence",
                "first", "then", "next", "finally"
            ]
        }

        # Find which patterns match
        detected_patterns = []
        for pattern_name, keywords in patterns.items():
            matches = sum(1 for kw in keywords if kw in content_lower)
            if matches >= 2:
                detected_patterns.append((pattern_name, matches))

        # Sort by match count
        detected_patterns.sort(key=lambda x: x[1], reverse=True)
        
        # Determine primary concept type
        if detected_patterns:
            primary_type = detected_patterns[0][0]
        else:
            primary_type = "concept"

        # Extract key terms from content
        key_terms = []
        all_keywords = [kw for kws in patterns.values() for kw in kws]
        for kw in all_keywords:
            if kw in content_lower and kw not in key_terms:
                key_terms.append(kw)
                if len(key_terms) >= 8:
                    break

        # Map to style
        style_map = {
            "architecture": "architecture_diagram",
            "attention": "technical_infographic",
            "position": "comparison_chart",
            "normalization": "technical_infographic",
            "comparison": "comparison_chart",
            "process": "process_flow",
            "concept": "handwritten_notes"
        }

        return {
            "primary_concept": {
                "type": primary_type,
                "title": section_title,
                "elements": key_terms[:5],
                "relationships": [],
                "details": f"Key concepts from {section_title}"
            },
            "secondary_concepts": [],
            "recommended_style": style_map.get(primary_type, "technical_infographic"),
            "key_terms": key_terms
        }

    def generate_content_aware_prompt(self, concepts: dict) -> str:
        """
        Generate a content-aware image prompt from extracted concepts.

        Args:
            concepts: Dict with extracted concepts

        Returns:
            Detailed image generation prompt
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

        # Generate the prompt using the template
        prompt = CONTENT_AWARE_IMAGE_PROMPT.format(
            style=style.replace("_", " "),
            title=primary.get("title", "Concept Visualization"),
            elements=elements_str,
            relationships=relationships_str,
            details=details,
            key_terms=key_terms_str,
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
        """Initialize detector with concept extractor."""
        self.settings = get_settings()
        self.concept_extractor = ConceptExtractor()
        logger.debug("Image type detector initialized with concept extractor")

    def is_available(self) -> bool:
        """Check if detector is available."""
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
        """
        # Skip very short sections
        if len(content) < 200:
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
            
            # Determine image type from extracted concepts
            style = concepts.get("recommended_style", "technical_infographic")
            image_type = self._style_to_image_type(style)
            
            # Generate content-aware prompt
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
        """Convert recommended style to ImageType enum."""
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
        """Fallback detection using basic keyword analysis."""
        # Use the keyword-based extraction as fallback
        concepts = self.concept_extractor._keyword_extraction(section_title, content)
        prompt = self.concept_extractor.generate_content_aware_prompt(concepts)
        
        return ImageDecision(
            image_type=ImageType.INFOGRAPHIC,
            prompt=prompt,
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

        # Check for skip_image_generation flag in metadata
        metadata = state.get("metadata", {})
        skip_generation = metadata.get("skip_image_generation", False)
        
        if skip_generation:
            # Load existing images instead of generating new ones
            from ...utils.content_cache import load_existing_images
            section_images = load_existing_images(images_dir)
            structured_content["section_images"] = section_images
            state["structured_content"] = structured_content
            logger.info(f"Loaded {len(section_images)} existing images (generation skipped)")
            return state

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
        reused_count = 0

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
                output_path = images_dir / f"section_{section_id}_{decision.image_type.value}.png"
                
                # Check if image already exists
                if output_path.exists():
                    logger.info(f"Reusing existing image for section {section_id}: {section_title}")
                    image_path = output_path
                    reused_count += 1
                # Use Gemini for infographics and decorative images
                elif gemini_gen.is_available():
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
            f"{reused_count} reused, {skipped_count} skipped"
        )

    except Exception as e:
        error_msg = f"Image generation failed: {str(e)}"
        state["errors"].append(error_msg)
        logger.error(error_msg)
        logger.exception("Image generation error details:")

    return state
