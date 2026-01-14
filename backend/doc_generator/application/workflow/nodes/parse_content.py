"""
Content parsing node for LangGraph workflow.

Parses input content using appropriate parser.
"""

import hashlib

from loguru import logger

from ...domain.exceptions import ParseError
from ...domain.models import WorkflowState
from ..parsers import get_parser


def parse_content_node(state: WorkflowState) -> WorkflowState:
    """
    Parse input content using appropriate parser.

    Args:
        state: Current workflow state

    Returns:
        Updated state with raw_content and metadata
    Invoked by: src/doc_generator/application/graph_workflow.py, src/doc_generator/application/workflow/graph.py
    """
    try:
        # Get appropriate parser
        parser = get_parser(state["input_format"])

        # Parse content
        content, metadata = parser.parse(state["input_path"])

        state["raw_content"] = content
        state["metadata"].update(metadata)
        state["metadata"]["content_hash"] = hashlib.sha256(
            content.encode("utf-8")
        ).hexdigest()

        logger.info(f"Parsed content: {len(content)} characters, title='{metadata.get('title', 'N/A')}'")

    except ParseError as e:
        error_msg = f"Parsing failed: {str(e)}"
        state["errors"].append(error_msg)
        logger.error(error_msg)

    except Exception as e:
        error_msg = f"Unexpected parsing error: {str(e)}"
        state["errors"].append(error_msg)
        logger.error(error_msg)

    return state
