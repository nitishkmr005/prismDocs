"""
Format detection node for LangGraph workflow.

Detects input format from file extension or URL pattern.
"""

from pathlib import Path

from loguru import logger

from ...domain.content_types import ContentFormat
from ...domain.models import WorkflowState


def detect_format_node(state: WorkflowState) -> WorkflowState:
    """
    Detect input format from file extension or URL pattern.

    Args:
        state: Current workflow state

    Returns:
        Updated state with input_format set
    Invoked by: src/doc_generator/application/graph_workflow.py, src/doc_generator/application/workflow/graph.py
    """
    input_path = state["input_path"]

    # URL detection
    if input_path.startswith("http://") or input_path.startswith("https://"):
        state["input_format"] = ContentFormat.URL
        logger.info(f"Detected format: URL ({input_path})")
        return state

    # File extension detection
    path = Path(input_path)
    suffix = path.suffix.lower()

    format_map = {
        ".pdf": ContentFormat.PDF,
        ".md": ContentFormat.MARKDOWN,
        ".markdown": ContentFormat.MARKDOWN,
        ".txt": ContentFormat.TEXT,
        ".docx": ContentFormat.DOCX,
        ".pptx": ContentFormat.PPTX,
        ".html": ContentFormat.HTML,
    }

    if suffix not in format_map:
        error_msg = f"Unsupported format: {suffix}"
        state["errors"].append(error_msg)
        logger.error(error_msg)
    else:
        state["input_format"] = format_map[suffix]
        logger.info(f"Detected format: {state['input_format']} ({input_path})")

    return state
