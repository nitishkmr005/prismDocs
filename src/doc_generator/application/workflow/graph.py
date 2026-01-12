"""
LangGraph workflow for document generation.

Defines the state machine workflow for converting documents.
"""

from pathlib import Path

from langgraph.graph import END, StateGraph
from loguru import logger

from ..domain.models import WorkflowState
from ..infrastructure.image import GeminiImageGenerator
from ..infrastructure.llm import LLMContentGenerator
from ..infrastructure.llm import LLMService
from ..infrastructure.settings import get_settings
from .nodes import (
    detect_format_node,
    describe_images_node,
    enhance_content_node,
    generate_images_node,
    generate_output_node,
    parse_content_node,
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
    2. parse_content -> Extract content using appropriate parser
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
    workflow.add_node("parse_content", parse_content_node)
    workflow.add_node("transform_content", transform_content_node)
    workflow.add_node("enhance_content", enhance_content_node)
    workflow.add_node("generate_images", generate_images_node)
    workflow.add_node("describe_images", describe_images_node)
    workflow.add_node("persist_image_manifest", persist_image_manifest_node)
    workflow.add_node("generate_output", generate_output_node)
    workflow.add_node("validate_output", validate_output_node)

    # Define linear flow
    workflow.set_entry_point("detect_format")
    workflow.add_edge("detect_format", "parse_content")
    workflow.add_edge("parse_content", "transform_content")
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
    Invoked by: scripts/generate_from_folder.py, scripts/generate_pdf_from_cache.py, scripts/quick_pdf_with_images.py, scripts/run_generator.py, src/doc_generator/infrastructure/api/services/generation.py
    """
    settings = get_settings()
    output_format = output_format or settings.generator.default_output_format
    metadata = metadata or {}
    metadata.setdefault("audience", settings.generator.audience)
    input_path_obj = Path(input_path)
    if not input_path_obj.is_absolute() and not input_path_obj.exists():
        candidate = settings.generator.input_dir / input_path
        if candidate.exists():
            input_path = str(candidate)

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

    logger.info(f"Starting workflow: {input_path} -> {output_format}")

    # Execute workflow
    result = workflow.invoke(initial_state)

    # Log results
    if result.get("errors"):
        logger.error(f"Workflow completed with errors: {result['errors']}")
    else:
        logger.info(f"Workflow completed successfully: {result.get('output_path', 'N/A')}")

    llm_usage = LLMService.usage_summary()
    content_usage = LLMContentGenerator.usage_summary()
    total_llm_calls = llm_usage["total_calls"] + content_usage["total_calls"]
    models_used = sorted(set(llm_usage["models"]) | set(content_usage["models"]))
    providers_used = sorted(set(llm_usage["providers"]) | set(content_usage["providers"]))
    gemini_usage = GeminiImageGenerator.usage_summary()
    logger.opt(colors=True).info(
        "<cyan>LLM usage</cyan> calls={} models={} providers={}",
        total_llm_calls,
        models_used,
        providers_used,
    )
    logger.opt(colors=True).info(
        "<magenta>Gemini usage</magenta> calls={} models={}",
        gemini_usage["total_calls"],
        gemini_usage["models"],
    )

    llm_details = LLMService.usage_details() + LLMContentGenerator.usage_details()
    image_details = GeminiImageGenerator.usage_details()
    call_rows = llm_details + image_details
    if call_rows:
        logger.opt(colors=True).info(
            "<cyan>Call timings</cyan>\n{}",
            _format_call_table(call_rows)
        )

    return result


def _format_call_table(rows: list[dict]) -> str:
    """
    Invoked by: src/doc_generator/application/graph_workflow.py, src/doc_generator/application/workflow/graph.py
    """
    headers = ["type", "step", "provider", "model", "sec", "in_tokens", "out_tokens"]
    table_rows = [headers]

    for row in rows:
        kind = row.get("kind", "")
        step = row.get("step", "")
        provider = row.get("provider", "")
        model = row.get("model", "")
        duration_ms = row.get("duration_ms")
        duration_sec = "-"
        if isinstance(duration_ms, (int, float)):
            duration_sec = f"{duration_ms / 1000:.2f}"
        input_tokens = row.get("input_tokens")
        output_tokens = row.get("output_tokens")
        in_str = str(input_tokens) if input_tokens is not None else "-"
        out_str = str(output_tokens) if output_tokens is not None else "-"
        table_rows.append([kind, step, provider, model, duration_sec, in_str, out_str])

    col_widths = [max(len(str(row[i])) for row in table_rows) for i in range(len(headers))]

    lines = []
    header_line = "  ".join(
        str(headers[i]).ljust(col_widths[i]) for i in range(len(headers))
    )
    lines.append(header_line)
    lines.append("  ".join("-" * col_widths[i] for i in range(len(headers))))

    for row in table_rows[1:]:
        lines.append("  ".join(
            str(row[i]).ljust(col_widths[i]) for i in range(len(headers))
        ))

    return "\n".join(lines)
