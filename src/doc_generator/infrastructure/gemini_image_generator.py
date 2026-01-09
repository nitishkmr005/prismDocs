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

from ..domain.content_types import ImageType
from .settings import get_settings

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

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini image generator.

        Args:
            api_key: Google API key. If not provided, uses GEMINI_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = None
        self.settings = get_settings().image_generation

        # Rate limiting state
        self._last_request_time: float = 0
        self._request_count: int = 0
        self._minute_start: float = time.time()

        if self.api_key and GENAI_AVAILABLE:
            self.client = genai.Client(api_key=self.api_key)
            logger.info(f"Gemini image generator initialized with model: {self.settings.gemini_model}")
        else:
            if not self.api_key:
                logger.warning("No Gemini API key provided - image generation disabled")
            if not GENAI_AVAILABLE:
                logger.warning("google-genai package not available")

    def is_available(self) -> bool:
        """Check if Gemini image generator is available."""
        return self.client is not None and GENAI_AVAILABLE

    def _wait_for_rate_limit(self) -> None:
        """
        Ensure we don't exceed rate limits.

        Implements:
        - 20 requests per minute limit
        - Minimum delay between requests (3 seconds default)
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
        """
        if image_type == ImageType.INFOGRAPHIC:
            return f"""Create a vibrant, educational infographic that explains: {prompt}

Style requirements:
- Clean, modern infographic design
- Use icons and visual metaphors to explain concepts
- Include clear labels and annotations
- Use a professional color palette (blues, teals, oranges)
- Make it suitable for inclusion in a professional document
- No text-heavy design - focus on visual explanation
- High contrast for readability when printed"""

        elif image_type == ImageType.DECORATIVE:
            return f"""Create a professional, thematic header image for: {prompt}

Style requirements:
- Abstract or semi-abstract design
- Professional and modern aesthetic
- Subtle and elegant - not distracting
- Use muted, professional colors
- Suitable as a section header in a document
- Wide aspect ratio (16:9 or similar)
- No text in the image"""

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
            logger.info(f"Generating {image_type.value} image for: {section_title}")

            # Create chat with image generation capabilities
            chat = self.client.chats.create(
                model=self.settings.gemini_model,
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
                        logger.success(f"Generated image saved: {output_path}")
                        return output_path

            logger.warning(f"No image in response for: {section_title}")
            return None

        except Exception as e:
            logger.error(f"Failed to generate image for '{section_title}': {e}")
            return None

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
        """
        return self.generate_image(
            prompt=theme,
            image_type=ImageType.DECORATIVE,
            section_title=section_title,
            output_path=output_path
        )


def encode_image_base64(image_path: Path) -> str:
    """
    Encode an image file to base64 string.

    Args:
        image_path: Path to image file

    Returns:
        Base64 encoded string
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
    """
    return GeminiImageGenerator(api_key=api_key)
