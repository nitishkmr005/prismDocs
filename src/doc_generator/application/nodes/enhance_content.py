"""
Content enhancement node for LangGraph workflow.
"""

from loguru import logger

from ...domain.models import WorkflowState
from ...infrastructure.llm import get_llm_service
from ...infrastructure.logging_utils import (
    log_node_start,
    log_node_end,
    log_progress,
    log_metric,
    log_subsection,
)


def enhance_content_node(state: WorkflowState) -> WorkflowState:
    """
    Add executive summaries and slide structures to structured content.
    Invoked by: src/doc_generator/application/graph_workflow.py, src/doc_generator/application/workflow/graph.py
    """
    log_node_start("enhance_content", step_number=4)
    
    structured = state.get("structured_content", {})
    markdown = structured.get("markdown", "")
    
    if not markdown:
        log_node_end("enhance_content", success=True, details="No content to enhance")
        return state

    output_format = state.get("output_format", "pdf")
    log_metric("Output Format", output_format.upper())
    
    llm = state.get("llm_service") or get_llm_service()
    if not llm.is_available():
        log_progress("LLM not available - skipping enhancements")
        log_node_end("enhance_content", success=True, details="LLM unavailable")
        return state

    enhancements_added = []
    
    # Generate executive summary
    if not structured.get("executive_summary"):
        log_subsection("Generating Executive Summary")
        executive_summary = llm.generate_executive_summary(markdown)
        if executive_summary:
            structured["executive_summary"] = executive_summary
            summary_points = len(executive_summary.get("points", []))
            log_metric("Summary Points", summary_points)
            enhancements_added.append(f"{summary_points} summary points")

    # Generate slide structure for PPTX
    if output_format == "pptx" and not structured.get("slides"):
        log_subsection("Generating Slide Structure")
        slides = llm.generate_slide_structure(markdown)
        if slides:
            structured["slides"] = slides
            log_metric("Slides Generated", len(slides))
            enhancements_added.append(f"{len(slides)} slides")

    state["structured_content"] = structured
    
    details = ", ".join(enhancements_added) if enhancements_added else "No enhancements needed"
    log_node_end("enhance_content", success=True, details=details)
    return state
