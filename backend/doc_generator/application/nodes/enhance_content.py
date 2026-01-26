"""
Content enhancement node for LangGraph workflow.
"""

from loguru import logger

from ...domain.models import WorkflowState
from ...infrastructure.llm import get_llm_service
from ...infrastructure.settings import get_settings
from ...infrastructure.logging_utils import (
    log_node_start,
    log_node_end,
    log_progress,
    log_metric,
    log_subsection,
    resolve_step_number,
    resolve_total_steps,
)


def enhance_content_node(state: WorkflowState) -> WorkflowState:
    """
    Add executive summaries and slide structures to structured content.
    Invoked by: src/doc_generator/application/graph_workflow.py, src/doc_generator/application/workflow/graph.py
    """
    log_node_start(
        "enhance_content",
        step_number=resolve_step_number(state, "enhance_content", 4),
        total_steps=resolve_total_steps(state, 9),
    )
    
    structured = state.get("structured_content", {})
    markdown = structured.get("markdown", "")
    
    if not markdown:
        log_node_end("enhance_content", success=True, details="No content to enhance")
        return state

    output_format = state.get("output_format", "pdf")
    log_metric("Output Format", output_format.upper())
    
    llm = state.get("llm_service") or get_llm_service()
    require_slide_llm = output_format in ("pptx", "pdf_from_pptx")
    metadata = state.get("metadata", {})
    if require_slide_llm:
        metadata["require_slide_llm"] = True
        state["metadata"] = metadata

    if not llm.is_available():
        log_progress("LLM not available - skipping enhancements")
        if require_slide_llm:
            error_msg = "LLM unavailable for slide generation"
            state["errors"].append(error_msg)
            log_node_end("enhance_content", success=False, details=error_msg)
        else:
            log_node_end("enhance_content", success=True, details="LLM unavailable")
        return state

    enhancements_added = []
    
    def _count_summary_points(summary) -> int:
        """
        Count bullet points in an executive summary.
        Invoked by: src/doc_generator/application/nodes/enhance_content.py
        """
        if isinstance(summary, dict):
            return len(summary.get("points", []))
        if isinstance(summary, str):
            lines = [line.strip() for line in summary.splitlines()]
            return sum(1 for line in lines if line.startswith(("-", "•")))
        return 0

    # Generate executive summary
    if not structured.get("executive_summary"):
        log_subsection("Generating Executive Summary")
        executive_summary = llm.generate_executive_summary(markdown)
        if executive_summary:
            structured["executive_summary"] = executive_summary
            summary_points = _count_summary_points(executive_summary)
            log_metric("Summary Points", summary_points)
            enhancements_added.append(f"{summary_points} summary points")

    # Generate slide structure for PPTX and PDF-from-PPTX
    if output_format in ("pptx", "pdf_from_pptx") and not structured.get("slides"):
        log_subsection("Generating Slide Structure")
        settings = get_settings()
        max_slides = metadata.get("max_slides")
        max_attempts = max(1, int(metadata.get("slide_generation_retries", 0) or settings.generator.max_retries))
        slides = []

        for attempt in range(1, max_attempts + 1):
            slides = llm.generate_slide_structure(markdown, max_slides=max_slides)
            if slides:
                structured["slides"] = slides
                log_metric("Slides Generated", len(slides))
                enhancements_added.append(f"{len(slides)} slides")
                break
            log_progress(f"Slide generation attempt {attempt} failed")

        if not slides and require_slide_llm:
            error_msg = f"Slide generation failed after {max_attempts} attempts"
            state["errors"].append(error_msg)
            log_node_end("enhance_content", success=False, details=error_msg)
            return state

    state["structured_content"] = structured
    
    details = ", ".join(enhancements_added) if enhancements_added else "No enhancements needed"
    log_node_end("enhance_content", success=True, details=details)
    return state
