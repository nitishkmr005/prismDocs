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
    if not state.get("output_path"):
        error_msg = "No output path specified"
        state["errors"].append(error_msg)
        logger.error(error_msg)
        return state

    output_path = Path(state["output_path"])

    try:
        # Check file exists
        if not output_path.exists():
            raise ValidationError(f"Output file not found: {output_path}")

        # Check file size
        file_size = output_path.stat().st_size
        if file_size == 0:
            raise ValidationError(f"Output file is empty: {output_path}")

        # Check extension
        expected_ext = f".{state['output_format']}"
        if output_path.suffix.lower() != expected_ext:
            raise ValidationError(
                f"Output file has wrong extension: {output_path.suffix}, expected {expected_ext}"
            )

        logger.info(f"Validation passed: {output_path.name} ({file_size:,} bytes)")

    except ValidationError as e:
        state["errors"].append(str(e))
        logger.error(f"Validation failed: {e}")

    except Exception as e:
        error_msg = f"Unexpected validation error: {str(e)}"
        state["errors"].append(error_msg)
        logger.error(error_msg)

    return state
