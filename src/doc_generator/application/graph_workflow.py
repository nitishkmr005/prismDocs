"""
LangGraph workflow for document generation.

Defines the state machine workflow for converting documents.
"""

from langgraph.graph import END, StateGraph
from loguru import logger

from ..domain.models import WorkflowState
from .nodes import (
    detect_format_node,
    generate_images_node,
    generate_output_node,
    generate_visuals_node,
    parse_content_node,
    transform_content_node,
    validate_output_node,
)


def should_retry(state: WorkflowState) -> str:
    """
    Decide whether to retry generation or end workflow.

    Args:
        state: Current workflow state

    Returns:
        "retry" or "end"
    """
    errors = state.get("errors", [])

    # Don't retry if no errors
    if not errors:
        return "end"

    # Don't retry more than 3 times
    retry_count = state.get("_retry_count", 0)
    if retry_count >= 3:
        logger.warning(f"Max retries reached ({retry_count}), ending workflow")
        return "end"

    # Only retry on generation/validation errors, not parsing errors
    last_error = errors[-1] if errors else ""
    if "Generation failed" in last_error or "Validation failed" in last_error:
        state["_retry_count"] = retry_count + 1
        logger.warning(f"Retrying generation (attempt {retry_count + 1}/3)")
        return "retry"

    return "end"


def build_workflow() -> StateGraph:
    """
    Build the LangGraph workflow for document generation.

    Workflow:
    1. detect_format → Detect input format from extension/URL
    2. parse_content → Extract content using appropriate parser
    3. transform_content → Structure content for output
    4. generate_visuals → Generate SVG visualizations from content
    5. generate_images → Generate Gemini images for sections (infographic/decorative)
    6. generate_output → Generate PDF or PPTX
    7. validate_output → Validate generated file
    8. Conditional retry on validation errors (max 3 attempts)

    Returns:
        Compiled StateGraph ready for execution
    """
    workflow = StateGraph(WorkflowState)

    # Add nodes
    workflow.add_node("detect_format", detect_format_node)
    workflow.add_node("parse_content", parse_content_node)
    workflow.add_node("transform_content", transform_content_node)
    workflow.add_node("generate_visuals", generate_visuals_node)
    workflow.add_node("generate_images", generate_images_node)
    workflow.add_node("generate_output", generate_output_node)
    workflow.add_node("validate_output", validate_output_node)

    # Define linear flow
    workflow.set_entry_point("detect_format")
    workflow.add_edge("detect_format", "parse_content")
    workflow.add_edge("parse_content", "transform_content")
    workflow.add_edge("transform_content", "generate_visuals")
    workflow.add_edge("generate_visuals", "generate_images")
    workflow.add_edge("generate_images", "generate_output")
    workflow.add_edge("generate_output", "validate_output")

    # Conditional retry logic
    workflow.add_conditional_edges(
        "validate_output",
        should_retry,
        {
            "retry": "generate_output",
            "end": END
        }
    )

    logger.debug("Built LangGraph workflow with 7 nodes")

    return workflow.compile()


def run_workflow(
    input_path: str,
    output_format: str = "pdf",
    output_path: str = "",
    llm_service = None,
    metadata: dict = None
) -> WorkflowState:
    """
    Run the document generation workflow.

    Args:
        input_path: Path to input file or URL
        output_format: Desired output format (pdf or pptx)
        output_path: Optional custom output path
        llm_service: Optional LLM service for content enhancement
        metadata: Optional metadata to include in the document

    Returns:
        Final workflow state with output_path or errors
    """
    # Build workflow
    workflow = build_workflow()

    # Initial state
    initial_state: WorkflowState = {
        "input_path": input_path,
        "input_format": "",
        "output_format": output_format,
        "raw_content": "",
        "structured_content": {},
        "output_path": output_path,
        "errors": [],
        "metadata": metadata or {},
        "llm_service": llm_service,
    }

    logger.info(f"Starting workflow: {input_path} → {output_format}")

    # Execute workflow
    result = workflow.invoke(initial_state)

    # Log results
    if result.get("errors"):
        logger.error(f"Workflow completed with errors: {result['errors']}")
    else:
        logger.info(f"Workflow completed successfully: {result.get('output_path', 'N/A')}")

    return result
