"""
FAQ generation node for unified workflow.

Extracts FAQ Q&A pairs from content using LLM.
"""

import os

from loguru import logger

from ..unified_state import UnifiedWorkflowState
from ...domain.prompts.faq_prompts import build_faq_extraction_prompt
from ...infrastructure.api.services.common.json_utils import safe_json_parse
from ...infrastructure.llm import LLMService


def generate_faq_node(state: UnifiedWorkflowState) -> UnifiedWorkflowState:
    """
    Generate FAQ data from content using LLM.

    Args:
        state: Current workflow state with raw_content or summary_content

    Returns:
        Updated state with structured_content.faq_data
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
        "generate_faq",
        step_number=resolve_step_number(state, "generate_faq", 6),
        total_steps=resolve_total_steps(state, 8),
    )

    raw_content = state.get("summary_content") or state.get("raw_content", "")
    if not raw_content:
        error_msg = "No content available for FAQ extraction"
        state["errors"] = state.get("errors", []) + [error_msg]
        log_node_end("generate_faq", success=False, details=error_msg)
        return state

    request_data = state.get("request_data", {})
    provider = request_data.get("provider", "gemini")
    model = request_data.get("model", "gemini-2.5-flash")
    api_key = state.get("api_key", "")

    log_metric("Provider", provider)
    log_metric("Model", model)
    log_metric("Content Length", f"{len(raw_content)} chars")
    log_progress("Extracting FAQ questions and answers...")

    try:
        provider_name = provider if provider != "google" else "gemini"

        key_mapping = {
            "gemini": "GOOGLE_API_KEY",
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
        }
        env_var = key_mapping.get(provider_name)
        if env_var and api_key:
            os.environ[env_var] = api_key

        llm_service = LLMService(provider=provider_name, model=model)
        prompt = build_faq_extraction_prompt(raw_content)
        response = llm_service.generate(prompt)

        faq_data = safe_json_parse(response)
        if not faq_data:
            error_msg = "Failed to parse FAQ JSON response"
            state["errors"] = state.get("errors", []) + [error_msg]
            log_node_end("generate_faq", success=False, details=error_msg)
            return state

        structured_content = state.get("structured_content", {})
        structured_content["faq_data"] = faq_data
        state["structured_content"] = structured_content

        metadata = state.get("metadata", {})
        if "title" not in metadata and faq_data.get("title"):
            metadata["title"] = faq_data.get("title")
        state["metadata"] = metadata

        log_node_end(
            "generate_faq",
            success=True,
            details=f"Extracted {len(faq_data.get('items', []))} FAQ items",
        )
    except Exception as e:
        logger.error(f"FAQ generation failed: {e}")
        error_msg = f"FAQ generation failed: {str(e)}"
        state["errors"] = state.get("errors", []) + [error_msg]
        log_node_end("generate_faq", success=False, details=error_msg)

    return state
