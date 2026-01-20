"""
LLM-backed image understanding utilities.
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Tuple

from loguru import logger

from ..domain.exceptions import ParseError

try:
    from google import genai
    from google.genai import types

    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    types = None

try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from anthropic import Anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tiff"}
MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".tiff": "image/tiff",
}


def is_image_file(path: Path) -> bool:
    """Return True when the file path is an image we can interpret."""
    return path.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES


def extract_image_content(
    path: Path,
    provider: str,
    model: str,
    api_key: str,
    max_tokens: int = 800,
) -> Tuple[str, dict]:
    """
    Extract text and description from an image using the selected LLM provider.
    """
    if not api_key:
        raise ParseError("Missing API key for image understanding.")

    if not path.exists():
        raise ParseError(f"File not found: {path}")

    provider_name = provider.lower()
    if provider_name == "google":
        provider_name = "gemini"

    mime_type = MIME_TYPES.get(path.suffix.lower(), "image/png")
    image_bytes = path.read_bytes()

    prompt = (
        "Extract all visible text from this image verbatim. "
        "If there is no text, write 'No text detected.' "
        "Then provide a concise description of the image content in 2-4 sentences.\n\n"
        "Return in this format:\n"
        "## Extracted Text\n<text>\n\n"
        "## Image Description\n<description>"
    )

    if provider_name == "gemini":
        if not GENAI_AVAILABLE:
            raise ParseError("Gemini image understanding not available (google-genai missing).")
        client = genai.Client(api_key=api_key)
        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        response = client.models.generate_content(
            model=model,
            contents=[prompt, image_part],
        )
        response_text = (response.text or "").strip()
    elif provider_name == "openai":
        if not OPENAI_AVAILABLE:
            raise ParseError("OpenAI image understanding not available (openai missing).")
        client = OpenAI(api_key=api_key)
        data_url = f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode('ascii')}"
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
            max_tokens=max_tokens,
        )
        response_text = (response.choices[0].message.content or "").strip()
    elif provider_name in {"anthropic", "claude"}:
        if not ANTHROPIC_AVAILABLE:
            raise ParseError("Anthropic image understanding not available (anthropic missing).")
        client = Anthropic(api_key=api_key)
        data_b64 = base64.b64encode(image_bytes).decode("ascii")
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mime_type,
                                "data": data_b64,
                            },
                        },
                    ],
                }
            ],
        )
        response_text = "".join(
            block.text for block in response.content if getattr(block, "text", None)
        ).strip()
    else:
        raise ParseError(f"Unsupported provider for image understanding: {provider}")

    if not response_text:
        raise ParseError("Image understanding returned empty response.")

    metadata = {
        "title": path.stem,
        "source_file": str(path),
        "parser": "llm-image",
        "provider": provider_name,
        "model": model,
    }
    logger.info(
        f"Image understanding complete: provider={provider_name} model={model} "
        f"chars={len(response_text)}"
    )
    return response_text, metadata
