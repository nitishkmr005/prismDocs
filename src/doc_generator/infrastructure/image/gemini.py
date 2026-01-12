"""
Gemini-powered image generator for document illustrations.

Uses Google's Gemini API to generate high-quality images for infographics
and decorative headers with rate limiting to stay within API limits.
"""

import base64
import os
import time
from pathlib import Path
from typing import Optional

from loguru import logger

from ...domain.content_types import ImageType
from ..observability.opik import log_llm_call
from ..settings import get_settings

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logger.warning("google-genai not installed - Gemini image generation disabled")


class GeminiImageGenerator:
    """
    Generate images using Google Gemini API with rate limiting.

    Supports infographic and decorative image generation with automatic
    rate limiting to stay within 20 requests/minute.
    """
    _total_calls: int = 0
    _models_used: set[str] = set()
    _call_details: list[dict] = []

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize Gemini image generator.

        Args:
            api_key: Google API key. If not provided, uses GEMINI_API_KEY env var.
        Invoked by: (no references found)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = None
        self.settings = get_settings().image_generation
        self._model_override = model

        # Rate limiting state
        self._last_request_time: float = 0
        self._request_count: int = 0
        self._minute_start: float = time.time()

        if self.api_key and GENAI_AVAILABLE:
            self.client = genai.Client(api_key=self.api_key)
            model_name = self._model_override or self.settings.gemini_model
            logger.info(f"Gemini image generator initialized with model: {model_name}")
        else:
            if not self.api_key:
                logger.warning("No Gemini API key provided - image generation disabled")
            if not GENAI_AVAILABLE:
                logger.warning("google-genai package not available")

    def is_available(self) -> bool:
        """
        Check if Gemini image generator is available.
        Invoked by: scripts/run_generator.py, src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/nodes/transform_content.py, src/doc_generator/application/workflow/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/transform_content.py, src/doc_generator/infrastructure/generators/pdf/utils.py, src/doc_generator/infrastructure/image/claude_svg.py, src/doc_generator/infrastructure/image/gemini.py, src/doc_generator/infrastructure/llm/content_generator.py, src/doc_generator/infrastructure/llm/service.py, src/doc_generator/infrastructure/pdf_utils.py, src/doc_generator/utils/content_merger.py
        """
        return self.client is not None and GENAI_AVAILABLE

    def _wait_for_rate_limit(self) -> None:
        """
        Ensure we don't exceed rate limits.

        Implements:
        - 20 requests per minute limit
        - Minimum delay between requests (3 seconds default)
        Invoked by: src/doc_generator/infrastructure/image/gemini.py
        """
        now = time.time()

        # Reset counter every minute
        if now - self._minute_start >= 60:
            self._request_count = 0
            self._minute_start = now
            logger.debug("Rate limit counter reset")

        # If at limit, wait for next minute
        if self._request_count >= self.settings.gemini_rate_limit:
            sleep_time = 60 - (now - self._minute_start)
            if sleep_time > 0:
                logger.info(f"Rate limit reached, waiting {sleep_time:.1f}s")
                time.sleep(sleep_time)
            self._request_count = 0
            self._minute_start = time.time()

        # Minimum delay between requests
        elapsed = now - self._last_request_time
        if elapsed < self.settings.gemini_request_delay:
            sleep_time = self.settings.gemini_request_delay - elapsed
            logger.debug(f"Waiting {sleep_time:.1f}s between requests")
            time.sleep(sleep_time)

    def _enhance_prompt(self, prompt: str, image_type: ImageType) -> str:
        """
        Enhance the prompt based on image type for better results.

        Args:
            prompt: Original prompt describing the image
            image_type: Type of image to generate

        Returns:
            Enhanced prompt string
        Invoked by: src/doc_generator/infrastructure/image/gemini.py
        """
        if image_type == ImageType.INFOGRAPHIC:
            return f"""Create a vibrant, educational infographic that explains: {prompt}

Style requirements:
- Clean, modern infographic design
- Use clear icons only when they represent actual concepts
- Include clear labels and annotations
- Use a professional color palette (blues, teals, oranges)
- Make it suitable for inclusion in a professional document
- No text-heavy design - focus on visual explanation
- High contrast for readability when printed
- Use ONLY the concepts in the prompt; do not add new information
- Avoid metaphorical objects (pipes, ropes, factories) unless explicitly mentioned
- For workflows/architectures, use flat rounded rectangles + arrows in a clean grid"""

        elif image_type == ImageType.DECORATIVE:
            return f"""Create a professional, thematic header image for: {prompt}

Style requirements:
- Abstract or semi-abstract design
- Professional and modern aesthetic
- Subtle and elegant - not distracting
- Use muted, professional colors
- Suitable as a section header in a document
- Wide aspect ratio (16:9 or similar)
- No text in the image
- Use ONLY the concepts in the prompt; do not add new information"""

        elif image_type == ImageType.MERMAID:
            return f"""Create a professional, clean flowchart/diagram image that represents: {prompt}

Style requirements:
- Clean, modern diagram design with clear flow
- Use boxes, arrows, and connections to show relationships
- Professional color scheme (blues, grays, with accent colors)
- Include clear labels for each step/component
- Make it suitable for inclusion in a corporate document
- High contrast for readability when printed
- No watermarks or decorative elements
- Focus on clarity and visual hierarchy
- Use ONLY the concepts in the prompt; do not add new information"""

        else:
            return prompt

    def generate_image(
        self,
        prompt: str,
        image_type: ImageType,
        section_title: str,
        output_path: Path
    ) -> Optional[Path]:
        """
        Generate an image using Gemini API with rate limiting.

        Args:
            prompt: Description/prompt for image generation
            image_type: Type of image (INFOGRAPHIC or DECORATIVE)
            section_title: Title of the section this image is for
            output_path: Path to save the generated image

        Returns:
            Path to saved image or None if generation failed
        Invoked by: src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/generate_images.py, src/doc_generator/infrastructure/image/gemini.py
        """
        if not self.is_available():
            logger.warning("Gemini not available, skipping image generation")
            return None

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Wait for rate limit
        self._wait_for_rate_limit()

        # Enhance prompt based on image type
        enhanced_prompt = self._enhance_prompt(prompt, image_type)

        try:
            GeminiImageGenerator._total_calls += 1
            model_name = self._model_override or self.settings.gemini_model
            if model_name:
                GeminiImageGenerator._models_used.add(model_name)
            logger.opt(colors=True).info(
                "<magenta>Gemini image call</magenta> model={} type={} section={}",
                model_name,
                image_type.value,
                section_title
            )
            start_time = time.perf_counter()

            # Create chat with image generation capabilities
            chat = self.client.chats.create(
                model=model_name,
                config=types.GenerateContentConfig(
                    response_modalities=['IMAGE']
                )
            )

            # Send the prompt
            response = chat.send_message(enhanced_prompt)

            # Update rate limiting state
            self._last_request_time = time.time()
            self._request_count += 1

            # Extract and save image from response
            for part in response.parts:
                if hasattr(part, 'as_image'):
                    image = part.as_image()
                    if image:
                        image.save(str(output_path))
                        duration_ms = int((time.perf_counter() - start_time) * 1000)
                        GeminiImageGenerator._call_details.append({
                            "kind": "image",
                            "step": "image_generate",
                            "provider": "gemini",
                            "model": model_name,
                            "duration_ms": duration_ms,
                            "input_tokens": None,
                            "output_tokens": None,
                        })
                        log_llm_call(
                            name="image_generate",
                            prompt=enhanced_prompt,
                            response=f"image_saved:{output_path}",
                            provider="gemini",
                            model=model_name,
                            duration_ms=duration_ms,
                            metadata={"image_type": image_type.value, "section_title": section_title},
                        )
                        logger.success(f"Generated image saved: {output_path}")
                        return output_path

            logger.warning(f"No image in response for: {section_title}")
            log_llm_call(
                name="image_generate",
                prompt=enhanced_prompt,
                response="no_image_in_response",
                provider="gemini",
                model=model_name,
                metadata={"image_type": image_type.value, "section_title": section_title},
            )
            return None

        except Exception as e:
            logger.error(f"Failed to generate image for '{section_title}': {e}")
            return None

    @classmethod
    def usage_summary(cls) -> dict:
        """
        Invoked by: src/doc_generator/application/graph_workflow.py, src/doc_generator/application/workflow/graph.py
        """
        return {
            "total_calls": cls._total_calls,
            "models": sorted(cls._models_used),
        }

    @classmethod
    def usage_details(cls) -> list[dict]:
        """
        Invoked by: src/doc_generator/application/graph_workflow.py, src/doc_generator/application/workflow/graph.py
        """
        return list(cls._call_details)

    def generate_infographic(
        self,
        concept: str,
        details: str,
        section_title: str,
        output_path: Path
    ) -> Optional[Path]:
        """
        Generate an infographic explaining a concept.

        Args:
            concept: Main concept to explain
            details: Additional details about the concept
            section_title: Title of the section
            output_path: Path to save the image

        Returns:
            Path to saved image or None if failed
        Invoked by: (no references found)
        """
        prompt = f"{concept}. {details}" if details else concept
        return self.generate_image(
            prompt=prompt,
            image_type=ImageType.INFOGRAPHIC,
            section_title=section_title,
            output_path=output_path
        )

    def generate_decorative_header(
        self,
        theme: str,
        section_title: str,
        output_path: Path
    ) -> Optional[Path]:
        """
        Generate a decorative header image for a section.

        Args:
            theme: Theme/mood for the header
            section_title: Title of the section
            output_path: Path to save the image

        Returns:
            Path to saved image or None if failed
        Invoked by: (no references found)
        """
        return self.generate_image(
            prompt=theme,
            image_type=ImageType.DECORATIVE,
            section_title=section_title,
            output_path=output_path
        )

    def generate_diagram_from_mermaid(
        self,
        mermaid_code: str,
        output_path: Path
    ) -> Optional[Path]:
        """
        Generate a diagram image from mermaid code description.

        Instead of rendering mermaid code, this converts it to a natural language
        description and generates a professional diagram image using Gemini.

        Args:
            mermaid_code: Mermaid diagram code
            output_path: Path to save the generated image

        Returns:
            Path to saved image or None if generation failed
        Invoked by: src/doc_generator/infrastructure/generators/pdf/utils.py, src/doc_generator/infrastructure/pdf_utils.py
        """
        # Parse mermaid code to create a description
        description = self._describe_mermaid(mermaid_code)

        return self.generate_image(
            prompt=description,
            image_type=ImageType.MERMAID,
            section_title="Diagram",
            output_path=output_path
        )

    def _describe_mermaid(self, mermaid_code: str) -> str:
        """
        Convert mermaid code to a natural language description.

        Args:
            mermaid_code: Mermaid diagram code

        Returns:
            Natural language description of the diagram
        Invoked by: src/doc_generator/infrastructure/image/gemini.py
        """
        lines = mermaid_code.strip().split('\n')

        # Detect diagram type
        diagram_type = "flowchart"
        if lines:
            first_line = lines[0].lower().strip()
            if first_line.startswith('graph'):
                diagram_type = "flowchart"
            elif first_line.startswith('sequencediagram'):
                diagram_type = "sequence diagram"
            elif first_line.startswith('classDiagram'):
                diagram_type = "class diagram"
            elif first_line.startswith('stateDiagram'):
                diagram_type = "state diagram"
            elif first_line.startswith('erDiagram'):
                diagram_type = "entity relationship diagram"
            elif first_line.startswith('gantt'):
                diagram_type = "gantt chart"
            elif first_line.startswith('pie'):
                diagram_type = "pie chart"

        # Extract nodes and connections
        nodes = []
        for line in lines[1:]:
            line = line.strip()
            if not line or line.startswith('%'):
                continue
            # Extract text between brackets
            import re
            matches = re.findall(r'\[([^\]]+)\]', line)
            for m in matches:
                if m not in nodes:
                    nodes.append(m)

        # Build description
        if nodes:
            nodes_desc = ", ".join(nodes[:10])
            return f"A {diagram_type} showing: {nodes_desc}. The diagram shows the flow and relationships between these components with arrows and connections."
        else:
            # Fallback to simplified code description
            simplified = ' '.join(lines[:5])
            return f"A {diagram_type} representing: {simplified}"


def encode_image_base64(image_path: Path) -> str:
    """
    Encode an image file to base64 string.

    Args:
        image_path: Path to image file

    Returns:
        Base64 encoded string
    Invoked by: src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/generate_images.py
    """
    if not image_path.exists():
        return ""

    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def get_gemini_generator(api_key: Optional[str] = None) -> GeminiImageGenerator:
    """
    Get or create Gemini image generator instance.

    Args:
        api_key: Optional API key

    Returns:
        GeminiImageGenerator instance
    Invoked by: src/doc_generator/infrastructure/generators/pdf/utils.py, src/doc_generator/infrastructure/pdf_utils.py
    """
    return GeminiImageGenerator(api_key=api_key)
