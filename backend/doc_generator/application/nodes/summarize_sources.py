"""
Chunked summarization node for unified workflow.
"""

from pathlib import Path

from loguru import logger

from ..unified_state import UnifiedWorkflowState, is_document_type
from ...utils.chunked_summary import summarize_content_chunked


def summarize_sources_node(state: UnifiedWorkflowState) -> UnifiedWorkflowState:
    """
    Summarize extracted content without truncation using chunked summarization.
    """
    from ...infrastructure.logging_utils import (
        log_node_start,
        log_node_end,
        log_progress,
        log_metric,
        resolve_step_number,
        resolve_total_steps,
    )

    log_node_start(
        "summarize_sources",
        step_number=resolve_step_number(state, "summarize_sources", 2),
        total_steps=resolve_total_steps(state, 9),
    )

    raw_content = state.get("raw_content", "")
    if not raw_content.strip():
        log_node_end("summarize_sources", success=True, details="No content to summarize")
        return state

    request_data = state.get("request_data", {})
    provider = request_data.get("provider", "gemini")
    model = request_data.get("model", "gemini-2.5-flash")
    api_key = state.get("api_key", "")

    log_metric("Provider", provider)
    log_metric("Model", model)
    log_metric("Raw Content", f"{len(raw_content)} chars")
    log_progress("Summarizing content in chunks")

    summary = summarize_content_chunked(
        raw_content,
        api_key=api_key,
        provider=provider,
        model=model,
    )

    metadata = state.get("metadata", {})
    metadata["raw_content_chars"] = len(raw_content)
    metadata["summary_generated"] = False
    state["metadata"] = metadata

    if not summary:
        log_node_end(
            "summarize_sources",
            success=False,
            details="Summarization unavailable",
        )
        return state

    state["summary_content"] = summary
    state["raw_content"] = summary

    metadata["summary_chars"] = len(summary)
    metadata["summary_generated"] = True
    state["metadata"] = metadata

    if is_document_type(state.get("output_type", "")):
        input_path = state.get("input_path", "")
        if input_path:
            path = Path(input_path)
            try:
                path.write_text(summary, encoding="utf-8")
                log_progress(f"Rewrote summary markdown: {path.name}")
            except Exception as exc:
                logger.warning(f"Failed to write summary markdown: {exc}")

    log_node_end(
        "summarize_sources",
        success=True,
        details=f"Summarized to {len(summary)} chars",
    )
    return state
