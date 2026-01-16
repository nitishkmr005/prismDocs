"""
Output validation node for LangGraph workflow.

Validates generated output file.
"""

from pathlib import Path

from loguru import logger

from ...domain.exceptions import ValidationError
from ...domain.models import WorkflowState


def validate_output_node(state: WorkflowState) -> WorkflowState:
    """
    Validate generated output file.

    Checks:
    - File exists
    - File size > 0
    - File extension matches output format

    Args:
        state: Current workflow state

    Returns:
        Updated state with validation results
    Invoked by: src/doc_generator/application/graph_workflow.py, src/doc_generator/application/workflow/graph.py
    """
    from ...infrastructure.logging_utils import (
        log_node_start,
        log_node_end,
        log_progress,
        log_metric,
    )
    
    log_node_start("validate_output", step_number=9)
    
    if not state.get("output_path"):
        error_msg = "No output path specified"
        state["errors"].append(error_msg)
        logger.error(error_msg)
        log_node_end("validate_output", success=False, details=error_msg)
        return state

    output_path = Path(state["output_path"])
    log_progress(f"Validating: {output_path.name}")

    try:
        # Check file exists
        if not output_path.exists():
            raise ValidationError(f"Output file not found: {output_path}")
        log_metric("File Exists", "✓")

        # Check file size
        file_size = output_path.stat().st_size
        if file_size == 0:
            raise ValidationError(f"Output file is empty: {output_path}")
        
        # Format file size
        if file_size < 1024:
            size_str = f"{file_size} bytes"
        elif file_size < 1024 * 1024:
            size_str = f"{file_size / 1024:.1f} KB"
        else:
            size_str = f"{file_size / (1024 * 1024):.1f} MB"
        log_metric("File Size", size_str)

        # Check extension
        format_value = str(state["output_format"]).lower()
        extension_map = {
            "markdown": ".md",
            "md": ".md",
        }
        expected_ext = extension_map.get(format_value, f".{format_value}")
        if output_path.suffix.lower() != expected_ext:
            raise ValidationError(
                f"Output file has wrong extension: {output_path.suffix}, expected {expected_ext}"
            )
        log_metric("Format Match", "✓")

        log_node_end("validate_output", success=True, 
                    details=f"Valid {state['output_format'].upper()}: {size_str}")

    except ValidationError as e:
        state["errors"].append(str(e))
        logger.error(f"Validation failed: {e}")
        log_node_end("validate_output", success=False, details=str(e))

    except Exception as e:
        error_msg = f"Unexpected validation error: {str(e)}"
        state["errors"].append(error_msg)
        logger.error(error_msg)
        log_node_end("validate_output", success=False, details=error_msg)

    return state
