"""
Format detection node for LangGraph workflow.

Detects input format from file extension or URL pattern.
"""

from pathlib import Path

from loguru import logger

from ...domain.content_types import ContentFormat
from ...domain.models import WorkflowState
from ...infrastructure.logging_utils import (
    log_node_start,
    log_node_end,
    log_progress,
    log_metric,
)


def detect_format_node(state: WorkflowState) -> WorkflowState:
    """
    Detect input format from file extension or URL pattern.

    Args:
        state: Current workflow state

    Returns:
        Updated state with input_format set
    Invoked by: src/doc_generator/application/graph_workflow.py, src/doc_generator/application/workflow/graph.py
    """
    log_node_start("detect_format", step_number=1)
    
    input_path = state["input_path"]
    log_progress(f"Analyzing input: {input_path}")

    # URL detection
    if input_path.startswith("http://") or input_path.startswith("https://"):
        state["input_format"] = ContentFormat.URL
        log_metric("Format", "URL")
        log_metric("Source", input_path)
        log_node_end("detect_format", success=True, details="URL detected")
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
        log_node_end("detect_format", success=False, details=error_msg)
    else:
        state["input_format"] = format_map[suffix]
        log_metric("Format", state["input_format"])
        log_metric("Extension", suffix)
        log_metric("File", path.name)
        log_node_end("detect_format", success=True, details=f"Format: {state['input_format']}")

    return state
