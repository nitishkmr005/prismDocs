"""
Content caching utilities for reusing generated content and images.

Allows saving and loading structured content to avoid regenerating
images and LLM-processed content.
"""

import json
from pathlib import Path
from typing import Optional

from loguru import logger


def save_structured_content(
    structured_content: dict,
    input_path: str,
    cache_dir: Path = Path("src/output/cache")
) -> Path:
    """
    Save structured content to JSON cache.
    
    Args:
        structured_content: Structured content dict from workflow
        input_path: Original input file path (used for cache filename)
        cache_dir: Directory to store cache files
        
    Returns:
        Path to saved cache file
    """
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
    input_path: str,
    cache_dir: Path = Path("src/output/cache")
) -> Optional[dict]:
    """
    Load structured content from JSON cache.
    
    Args:
        input_path: Original input file path
        cache_dir: Directory where cache files are stored
        
    Returns:
        Structured content dict or None if not cached
    """
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


def load_existing_images(
    images_dir: Path = Path("src/output/images")
) -> dict:
    """
    Load existing section images from disk.
    
    Scans the images directory and creates a section_images mapping
    without regenerating images.
    
    Args:
        images_dir: Directory containing generated images
        
    Returns:
        Dict mapping section_id -> image info
    """
    section_images = {}
    
    if not images_dir.exists():
        logger.warning(f"Images directory not found: {images_dir}")
        return section_images
    
    # Find all section images
    for img_path in sorted(images_dir.glob("section_*_infographic.png")):
        # Parse section ID from filename: section_0_infographic.png -> 0
        try:
            filename = img_path.stem  # section_0_infographic
            parts = filename.split("_")
            if len(parts) >= 2:
                section_id = int(parts[1])
                
                section_images[section_id] = {
                    "path": str(img_path),
                    "image_type": "infographic",
                    "section_title": f"Section {section_id}",
                    "prompt": "Previously generated",
                    "confidence": 1.0,
                    "embed_base64": "",  # Will be loaded if needed
                }
                
                logger.debug(f"Found existing image: section_{section_id}")
        
        except (ValueError, IndexError) as e:
            logger.debug(f"Could not parse section ID from: {img_path.name}")
    
    logger.info(f"Loaded {len(section_images)} existing images from {images_dir}")
    return section_images


def clear_cache(cache_dir: Path = Path("src/output/cache")) -> None:
    """
    Clear all cached content files.
    
    Args:
        cache_dir: Directory containing cache files
    """
    if not cache_dir.exists():
        return
    
    deleted = 0
    for cache_file in cache_dir.glob("*_content_cache.json"):
        cache_file.unlink()
        deleted += 1
    
    logger.info(f"Cleared {deleted} cache files")
