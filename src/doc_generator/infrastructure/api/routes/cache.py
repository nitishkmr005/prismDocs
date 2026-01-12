"""Cache management routes."""

import shutil
from pathlib import Path

from fastapi import APIRouter
from loguru import logger
from pydantic import BaseModel

from ...settings import get_settings

router = APIRouter(tags=["cache"])

# Base output directory
OUTPUT_BASE = Path("src/output")
CACHE_DIR = OUTPUT_BASE / "cache"


class ClearResponse(BaseModel):
    """Response for clear operations."""
    
    cleared_projects: int = 0
    cleared_cache: int = 0
    total_cleared: int = 0
    message: str = ""


class CacheStatsResponse(BaseModel):
    """Response for cache stats."""
    
    projects_count: int = 0
    projects_size_bytes: int = 0
    cache_entries: int = 0
    cache_size_bytes: int = 0


def get_project_dirs() -> list[Path]:
    """
    Get all project directories (f_xxx folders).
    Invoked by: src/doc_generator/infrastructure/api/routes/cache.py
    """
    if not OUTPUT_BASE.exists():
        return []
    return [d for d in OUTPUT_BASE.iterdir() if d.is_dir() and d.name.startswith("f_")]


def get_total_size(directory: Path) -> int:
    """
    Get total size of all files in directory recursively.
    Invoked by: src/doc_generator/infrastructure/api/routes/cache.py
    """
    if not directory.exists():
        return 0
    return sum(f.stat().st_size for f in directory.rglob("*") if f.is_file())


@router.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats() -> CacheStatsResponse:
    """Get cache and output statistics.
    
    Returns:
        Statistics about projects and cache entries
    Invoked by: (no references found)
    """
    project_dirs = get_project_dirs()
    projects_count = len(project_dirs)
    projects_size = sum(get_total_size(d) for d in project_dirs)
    
    cache_files = list(CACHE_DIR.glob("*.json")) if CACHE_DIR.exists() else []
    cache_count = len(cache_files)
    cache_size = sum(f.stat().st_size for f in cache_files if f.exists())
    
    return CacheStatsResponse(
        projects_count=projects_count,
        projects_size_bytes=projects_size,
        cache_entries=cache_count,
        cache_size_bytes=cache_size,
    )


@router.delete("/cache/clear", response_model=ClearResponse)
async def clear_cache() -> ClearResponse:
    """Clear all cache entries (keeps project files).
    
    Returns:
        Count of cleared items
    Invoked by: (no references found)
    """
    cache_cleared = 0
    if CACHE_DIR.exists():
        for f in CACHE_DIR.glob("*.json"):
            try:
                f.unlink()
                cache_cleared += 1
            except OSError:
                pass
    
    logger.info(f"Cleared {cache_cleared} cache entries")
    
    return ClearResponse(
        cleared_cache=cache_cleared,
        total_cleared=cache_cleared,
        message=f"Cleared {cache_cleared} cache entries",
    )


@router.delete("/cache/clear-all", response_model=ClearResponse)
async def clear_all() -> ClearResponse:
    """Clear all cache and project files.
    
    ⚠️ WARNING: This will delete all uploaded and generated files!
    
    Returns:
        Count of cleared items
    Invoked by: (no references found)
    """
    # Clear project directories (f_xxx folders)
    projects_cleared = 0
    for project_dir in get_project_dirs():
        try:
            shutil.rmtree(project_dir)
            projects_cleared += 1
        except OSError as e:
            logger.warning(f"Failed to remove {project_dir}: {e}")
    
    # Clear cache
    cache_cleared = 0
    if CACHE_DIR.exists():
        for f in CACHE_DIR.glob("*.json"):
            try:
                f.unlink()
                cache_cleared += 1
            except OSError:
                pass

    # Clear temp output directory
    temp_cleared = 0
    temp_dir = get_settings().generator.temp_dir
    if temp_dir.exists():
        for item in temp_dir.iterdir():
            try:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
                temp_cleared += 1
            except OSError as e:
                logger.warning(f"Failed to remove temp item {item}: {e}")
    
    total = projects_cleared + cache_cleared + temp_cleared
    
    logger.info(
        f"Cleared all: {projects_cleared} projects, "
        f"{cache_cleared} cache entries, {temp_cleared} temp items"
    )
    
    return ClearResponse(
        cleared_projects=projects_cleared,
        cleared_cache=cache_cleared,
        total_cleared=total,
        message=(
            f"Cleared {total} items "
            f"({projects_cleared} projects, {cache_cleared} cache entries, "
            f"{temp_cleared} temp items)"
        ),
    )
