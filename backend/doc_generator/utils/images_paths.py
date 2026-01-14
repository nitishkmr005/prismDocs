"""
Helpers for resolving image output paths.
"""

from __future__ import annotations

from pathlib import Path

from ..domain.models import WorkflowState


def resolve_images_dir(state: WorkflowState, settings) -> Path:
    """
    Resolve the images output directory for the current workflow run.
    Invoked by: src/doc_generator/application/utils/images_paths.py
    """
    metadata = state.get("metadata", {})
    folder_name = metadata.get("custom_filename") or metadata.get("file_id")
    if not folder_name:
        input_path = state.get("input_path", "")
        if input_path:
            input_p = Path(input_path)
            for part in input_p.parts:
                if part.startswith("f_"):
                    folder_name = part
                    break
            else:
                if input_p.parent.name == "source" and input_p.parent.parent.exists():
                    folder_name = input_p.parent.parent.name
                else:
                    folder_name = input_p.parent.name if input_p.is_file() else input_p.name
        else:
            folder_name = "output"

    topic_output_dir = settings.generator.output_dir / folder_name
    images_dir = topic_output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    return images_dir
