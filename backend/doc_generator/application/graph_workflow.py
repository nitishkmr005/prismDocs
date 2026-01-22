"""
LangGraph workflow for document generation.

Defines the state machine workflow for converting documents.
"""

from pathlib import Path

from langgraph.graph import END, StateGraph
from loguru import logger

from ..domain.models import WorkflowState
from ..infrastructure.image import GeminiImageGenerator
from ..infrastructure.llm import LLMContentGenerator, LLMService
from ..infrastructure.settings import get_settings
from .nodes import (
    detect_format_node,
    describe_images_node,
    enhance_content_node,
    generate_images_node,
    generate_output_node,
    parse_document_content_node,
    persist_image_manifest_node,
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

    Invoked by: src/doc_generator/application/graph_workflow.py, src/doc_generator/application/workflow/graph.py
    """
    errors = state.get("errors", [])

    # Don't retry if no errors
    if not errors:
        return "end"

    max_retries = get_settings().generator.max_retries
    # Don't retry more than configured attempts
    retry_count = state.get("_retry_count", 0)
    if retry_count >= max_retries:
        logger.warning(f"Max retries reached ({retry_count}), ending workflow")
        return "end"

    # Only retry on generation/validation errors, not parsing errors
    last_error = errors[-1] if errors else ""
    if "Generation failed" in last_error or "Validation failed" in last_error:
        state["_retry_count"] = retry_count + 1
        logger.warning(f"Retrying generation (attempt {retry_count + 1}/{max_retries})")
        return "retry"

    return "end"




def build_workflow() -> StateGraph:
    """
    Build the LangGraph workflow for document generation.

    Workflow:
    1. detect_format -> Detect input format from extension/URL
    2. parse_document_content -> Extract content using appropriate parser
    3. transform_content -> Structure content for output (creates merged .md)
    4. enhance_content -> Generate summaries and slide structures
    5. generate_images -> Generate images per section (uses merged content)
    6. describe_images -> Generate image captions and embed data
    7. persist_image_manifest -> Persist image metadata for cache reuse
    8. generate_output -> Generate PDF or PPTX
    9. validate_output -> Validate generated file
    7. Conditional retry on validation errors (max 3 attempts)

    Returns:
        Compiled StateGraph ready for execution

    Invoked by: src/doc_generator/application/graph_workflow.py, src/doc_generator/application/workflow/graph.py
    """
    workflow = StateGraph(WorkflowState)

    # Add nodes
    workflow.add_node("detect_format", detect_format_node)
    workflow.add_node("parse_document_content", parse_document_content_node)
    workflow.add_node("transform_content", transform_content_node)
    workflow.add_node("enhance_content", enhance_content_node)
    workflow.add_node("generate_images", generate_images_node)
    workflow.add_node("describe_images", describe_images_node)
    workflow.add_node("persist_image_manifest", persist_image_manifest_node)
    workflow.add_node("generate_output", generate_output_node)
    workflow.add_node("validate_output", validate_output_node)

    # Define linear flow
    workflow.set_entry_point("detect_format")
    workflow.add_edge("detect_format", "parse_document_content")
    workflow.add_edge("parse_document_content", "transform_content")
    workflow.add_edge("transform_content", "enhance_content")
    workflow.add_edge("enhance_content", "generate_images")
    workflow.add_edge("generate_images", "describe_images")
    workflow.add_edge("describe_images", "persist_image_manifest")
    workflow.add_edge("persist_image_manifest", "generate_output")
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

    logger.debug("Built LangGraph workflow with 9 nodes")

    return workflow.compile()


def run_workflow(
    input_path: str,
    output_format: str | None = None,
    output_path: str = "",
    llm_service = None,
    metadata: dict = None,
    progress_callback=None,
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

    Invoked by: scripts/generate_from_folder.py, scripts/generate_pdf_from_cache.py, scripts/quick_pdf_with_images.py, scripts/run_generator.py, src/doc_generator/infrastructure/api/services/generation.py
    """
    import time
    from ..infrastructure.logging_utils import (
        log_workflow_start,
        log_workflow_end,
        log_usage_summary,
        reset_progress_callback,
        set_progress_callback,
    )
    
    start_time = time.time()
    
    settings = get_settings()
    output_format = output_format or settings.generator.default_output_format
    metadata = metadata or {}
    metadata.setdefault("audience", settings.generator.audience)
    input_path_obj = Path(input_path)
    if not input_path_obj.is_absolute() and not input_path_obj.exists():
        candidate = settings.generator.input_dir / input_path
        if candidate.exists():
            input_path = str(candidate)

    # Log workflow start
    log_workflow_start(input_path, output_format)

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
        "metadata": metadata,
        "llm_service": llm_service,
    }

    # Execute workflow
    token = None
    if progress_callback is not None:
        token = set_progress_callback(progress_callback)

    try:
        result = workflow.invoke(initial_state)
    finally:
        if token is not None:
            reset_progress_callback(token)
    
    # Calculate duration
    duration_seconds = time.time() - start_time

    # Gather usage statistics
    llm_usage = LLMService.usage_summary()
    content_usage = LLMContentGenerator.usage_summary()
    total_llm_calls = llm_usage["total_calls"] + content_usage["total_calls"]
    models_used = sorted(set(llm_usage["models"]) | set(content_usage["models"]))
    providers_used = sorted(set(llm_usage["providers"]) | set(content_usage["providers"]))
    gemini_usage = GeminiImageGenerator.usage_summary()
    
    llm_details = LLMService.usage_details() + LLMContentGenerator.usage_details()
    image_details = GeminiImageGenerator.usage_details()
    call_rows = llm_details + image_details

    # Log workflow end
    if result.get("errors"):
        log_workflow_end(
            success=False,
            errors=result["errors"],
            duration_seconds=duration_seconds
        )
    else:
        log_workflow_end(
            success=True,
            output_path=result.get("output_path", "N/A"),
            duration_seconds=duration_seconds
        )

    # Log usage summary
    log_usage_summary(
        llm_calls=total_llm_calls,
        image_calls=gemini_usage["total_calls"],
        models=models_used,
        providers=providers_used,
        call_details=call_rows if call_rows else None
    )

    return result
