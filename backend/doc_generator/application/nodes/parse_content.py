"""
Document content parsing node for LangGraph workflow.

Parses input content using the appropriate parser.
"""

import hashlib

from loguru import logger

from ...domain.exceptions import ParseError
from ...domain.models import WorkflowState
from ..parsers import get_parser
from ...infrastructure.logging_utils import (
    log_node_start,
    log_node_end,
    log_progress,
    log_metric,
    log_file_operation,
    resolve_step_number,
    resolve_total_steps,
)


def parse_document_content_node(state: WorkflowState) -> WorkflowState:
    """
    Parse document input content using appropriate parser.

    Args:
        state: Current workflow state

    Returns:
        Updated state with raw_content and metadata
    Invoked by: src/doc_generator/application/graph_workflow.py, src/doc_generator/application/workflow/graph.py
    """
    log_node_start(
        "parse_document_content",
        step_number=resolve_step_number(state, "parse_document_content", 4),
        total_steps=resolve_total_steps(state, 9),
    )
    
    try:
        # Get appropriate parser
        input_format = state["input_format"]
        log_progress(f"Using parser for format: {input_format}")
        parser = get_parser(input_format)

        # Parse content
        log_progress(f"Parsing: {state['input_path']}")
        content, metadata = parser.parse(state["input_path"])

        state["raw_content"] = content
        state["metadata"].update(metadata)
        
        # Compute content hash for caching
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        state["metadata"]["content_hash"] = content_hash

        # Log metrics
        log_metric("Content Length", len(content), "chars")
        log_metric("Title", metadata.get('title', 'N/A'))
        log_metric("Content Hash", content_hash[:16] + "...")
        
        if "page_count" in metadata:
            log_metric("Pages", metadata["page_count"])
        
        log_node_end("parse_document_content", success=True, 
                    details=f"Parsed {len(content)} characters")

    except ParseError as e:
        error_msg = f"Parsing failed: {str(e)}"
        state["errors"].append(error_msg)
        logger.error(error_msg)
        log_node_end("parse_document_content", success=False, details=error_msg)

    except Exception as e:
        error_msg = f"Unexpected parsing error: {str(e)}"
        state["errors"].append(error_msg)
        logger.error(error_msg)
        log_node_end("parse_document_content", success=False, details=error_msg)

    return state
