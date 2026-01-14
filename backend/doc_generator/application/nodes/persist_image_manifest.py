"""
Persist image manifest for cache reuse.
"""

from __future__ import annotations

from ...domain.models import WorkflowState
from ...infrastructure.settings import get_settings
from ...utils.content_cache import save_image_manifest
from ...utils.images_paths import resolve_images_dir
from ...utils.markdown_sections import extract_sections


def persist_image_manifest_node(state: WorkflowState) -> WorkflowState:
    """
    Save manifest.json for generated images.
    Invoked by: src/doc_generator/application/graph_workflow.py, src/doc_generator/application/workflow/graph.py
    """
    from loguru import logger
    from ...infrastructure.logging_utils import (
        log_node_start,
        log_node_end,
        log_progress,
        log_metric,
        log_file_operation,
    )
    
    log_node_start("persist_image_manifest", step_number=7)
    
    metadata = state.get("metadata", {})
    if not metadata.get("content_hash"):
        log_node_end("persist_image_manifest", success=True, details="No content hash")
        return state

    structured_content = state.get("structured_content", {})
    section_images = structured_content.get("section_images", {})
    if not section_images:
        log_node_end("persist_image_manifest", success=True, details="No images to persist")
        return state

    log_progress("Creating image manifest")
    
    markdown = structured_content.get("markdown", "")
    section_titles = [section["title"] for section in extract_sections(markdown)]

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

    settings = get_settings()
    images_dir = resolve_images_dir(state, settings)
    manifest_path = images_dir / "manifest.json"
    
    save_image_manifest(
        images_dir,
        metadata["content_hash"],
        section_titles,
        descriptions=description_map,
        section_map=section_map,
        image_types=image_types,
    )
    
    log_metric("Manifest Entries", len(section_images))
    log_metric("Content Hash", metadata["content_hash"][:16] + "...")
    log_file_operation("write", str(manifest_path))
    log_node_end("persist_image_manifest", success=True, 
                details=f"Saved manifest with {len(section_images)} entries")
    return state
