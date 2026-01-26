"""
Content caching utilities for reusing generated content and images.

Allows saving and loading structured content to avoid regenerating
images and LLM-processed content.
"""

import json
import re
from pathlib import Path
from typing import Optional

from loguru import logger

from ..infrastructure.settings import get_settings


def save_structured_content(
    structured_content: dict, input_path: str, cache_dir: Path | None = None
) -> Path:
    """
    Save structured content to JSON cache.

    Args:
        structured_content: Structured content dict from workflow
        input_path: Original input file path (used for cache filename)
        cache_dir: Directory to store cache files

    Returns:
        Path to saved cache file
    Invoked by: src/doc_generator/application/nodes/generate_output.py, src/doc_generator/application/workflow/nodes/generate_output.py
    """
    if cache_dir is None:
        cache_dir = get_settings().generator.cache_dir
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Create cache filename from input path
    input_name = Path(input_path).stem
    cache_file = cache_dir / f"{input_name}_content_cache.json"

    # Save to JSON
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(structured_content, f, indent=2, ensure_ascii=False)

        logger.info(f"Cached structured content: {cache_file}")
        return cache_file

    except Exception as e:
        logger.error(f"Failed to cache content: {e}")
        return None


def load_structured_content(
    input_path: str, cache_dir: Path | None = None
) -> Optional[dict]:
    """
    Load structured content from JSON cache.

    Args:
        input_path: Original input file path
        cache_dir: Directory where cache files are stored

    Returns:
        Structured content dict or None if not cached
    Invoked by: src/doc_generator/application/nodes/transform_content.py, src/doc_generator/application/workflow/nodes/transform_content.py
    """
    if cache_dir is None:
        cache_dir = get_settings().generator.cache_dir
    input_name = Path(input_path).stem
    cache_file = cache_dir / f"{input_name}_content_cache.json"

    if not cache_file.exists():
        logger.debug(f"No cache found for: {input_name}")
        return None

    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            content = json.load(f)

        logger.info(f"Loaded cached content: {cache_file}")
        return content

    except Exception as e:
        logger.error(f"Failed to load cached content: {e}")
        return None


def load_image_manifest(images_dir: Path) -> Optional[dict]:
    """
    Invoked by: src/doc_generator/utils/content_cache.py
    """
    manifest_path = images_dir / "manifest.json"
    if not manifest_path.exists():
        return None
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load image manifest: {e}")
        return None


def save_image_manifest(
    images_dir: Path,
    content_hash: str,
    section_titles: list[str],
    descriptions: Optional[dict] = None,
    section_map: Optional[dict] = None,
    image_types: Optional[dict] = None,
    image_style: Optional[str] = None,
) -> None:
    """
    Invoked by: src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/generate_images.py
    """
    try:
        images_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = images_dir / "manifest.json"
        data = {
            "content_hash": content_hash,
            "section_titles": section_titles,
            "descriptions": descriptions or {},
            "section_map": section_map or {},
            "image_types": image_types or {},
            "image_style": image_style or "",
        }
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save image manifest: {e}")


def load_existing_images(
    images_dir: Path | None = None,
    expected_hash: Optional[str] = None,
    expected_style: Optional[str] = None,
) -> dict:
    """
    Load existing section images from disk.

    Scans the images directory and creates a section_images mapping
    without regenerating images.

    Args:
        images_dir: Directory containing generated images

    Returns:
        Dict mapping section_id -> image info
    Invoked by: src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/generate_images.py
    """
    if images_dir is None:
        images_dir = Path(get_settings().image_generation.images_dir)
    section_images = {}

    if not images_dir.exists():
        logger.warning(f"Images directory not found: {images_dir}")
        return section_images

    descriptions = {}
    section_map = {}
    image_types = {}
    if expected_hash:
        manifest = load_image_manifest(images_dir)
        if not manifest or manifest.get("content_hash") != expected_hash:
            logger.info("Image cache skipped due to content hash mismatch")
            return section_images
        if expected_style and manifest.get("image_style") != expected_style:
            logger.info("Image cache skipped due to image style mismatch")
            return section_images
        descriptions = manifest.get("descriptions", {}) or {}
        section_map = manifest.get("section_map", {}) or {}
        image_types = manifest.get("image_types", {}) or {}

    if section_map:
        for section_id_str, title in section_map.items():
            try:
                section_id = int(section_id_str)
            except ValueError:
                continue
            if not title:
                continue
            slug = re.sub(r"[^a-zA-Z0-9]+", "-", title.lower()).strip("-")
            if not slug:
                continue
            candidates = []
            base_path = images_dir / f"{slug}.png"
            if base_path.exists():
                candidates.append(base_path)
            candidates.extend(sorted(images_dir.glob(f"{slug}_*.png")))
            if not candidates:
                continue
            chosen = candidates[-1]
            section_images[section_id] = {
                "path": str(chosen),
                "image_type": image_types.get(section_id_str, "infographic"),
                "section_title": title,
                "prompt": "Previously generated",
                "confidence": 1.0,
                "embed_base64": "",
                "description": descriptions.get(section_id_str, ""),
            }
        if section_images:
            logger.info(
                f"Loaded {len(section_images)} existing images from {images_dir}"
            )
            return section_images

    # Find all section images
    for img_path in sorted(images_dir.glob("section_*_*.png")):
        # Parse section ID from filename: section_0_infographic.png -> 0
        try:
            filename = (
                img_path.stem
            )  # section_0_infographic or section_0_infographic__desc
            parts = filename.split("_")
            if len(parts) >= 3:
                section_id = int(parts[1])
                image_type = parts[2].split("__", 1)[0]

                section_images[section_id] = {
                    "path": str(img_path),
                    "image_type": image_type or "infographic",
                    "section_title": f"Section {section_id}",
                    "prompt": "Previously generated",
                    "confidence": 1.0,
                    "embed_base64": "",  # Will be loaded if needed
                    "description": descriptions.get(str(section_id), ""),
                }

                logger.debug(f"Found existing image: section_{section_id}")

        except (ValueError, IndexError) as e:
            logger.debug(f"Could not parse section ID from: {img_path.name}")

    logger.info(f"Loaded {len(section_images)} existing images from {images_dir}")
    return section_images


def clear_cache(cache_dir: Path = Path("data/cache")) -> None:
    """
    Clear all cached content files.

    Args:
        cache_dir: Directory containing cache files
    Invoked by: (no references found)
    """
    if not cache_dir.exists():
        return

    deleted = 0
    for cache_file in cache_dir.glob("*_content_cache.json"):
        cache_file.unlink()
        deleted += 1

    logger.info(f"Cleared {deleted} cache files")
