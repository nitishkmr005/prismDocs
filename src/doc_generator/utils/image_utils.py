"""
Shared image utilities for document generator.

Contains common image path resolution used across PDF and PPTX generators.
"""

from pathlib import Path
from typing import Optional

from loguru import logger


def resolve_image_path(
    url: str,
    image_cache: Optional[Path] = None,
    rasterize_func: Optional[callable] = None
) -> Optional[Path]:
    """
    Resolve image URL or path to a local file path.

    Handles various input formats:
    - Absolute paths
    - Relative paths
    - Hugo static directory paths
    - SVG files (optionally rasterized to PNG)

    Args:
        url: Image URL or path string
        image_cache: Optional directory for cached/converted images
        rasterize_func: Optional function to convert SVG to PNG

    Returns:
        Path to resolved local image or None if not found
    Invoked by: (no references found)
    """
    # Remote URLs are not supported for local document generation
    if url.startswith("http://") or url.startswith("https://"):
        logger.warning(f"Remote image URLs not supported: {url}")
        return None

    # Try to resolve as local path
    cleaned = url.lstrip("/")

    # Check several possible locations
    candidates = [
        Path(url),  # Absolute path
        Path(cleaned),  # Relative path
        Path("static") / cleaned,  # Hugo static dir
        Path("src/output") / cleaned,  # Output dir
    ]

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            # Handle SVG files - rasterize if function provided
            if candidate.suffix.lower() == ".svg" and rasterize_func and image_cache:
                return rasterize_func(candidate, image_cache)
            return candidate

    logger.warning(f"Image not found: {url}")
    return None
