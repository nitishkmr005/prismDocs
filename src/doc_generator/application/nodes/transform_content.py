"""
Content transformation node for LangGraph workflow.

Transforms raw content into structured format for generators.
Uses LLM for intelligent content enhancement when available.
"""

from loguru import logger

from ...domain.models import WorkflowState
from ...infrastructure.llm_service import get_llm_service
from ...utils.content_cleaner import clean_content_for_output


def transform_content_node(state: WorkflowState) -> WorkflowState:
    """
    Transform raw content into structured format for generators.

    Structures content for both PDF and PPTX generation by:
    - Storing raw markdown content
    - Extracting title and metadata
    - Using LLM to generate executive summaries
    - Creating optimized slide structures
    - Suggesting data visualizations

    Args:
        state: Current workflow state

    Returns:
        Updated state with structured_content
    """
    try:
        content = state.get("raw_content", "")
        metadata = state.get("metadata", {})
        output_format = state.get("output_format", "pdf")

        # Clean content before structuring
        cleaned_content = clean_content_for_output(content)

        # Base structured content with cleaned markdown
        structured = {
            "markdown": cleaned_content,
            "title": metadata.get("title", "Document"),
        }

        # Try to enhance with LLM
        llm = state.get("llm_service") or get_llm_service()

        if llm.is_available():
            logger.info("LLM service available - enhancing content")

            # Generate executive summary using cleaned content
            executive_summary = llm.generate_executive_summary(cleaned_content)
            if executive_summary:
                structured["executive_summary"] = executive_summary
                logger.debug("Generated executive summary")

            # For PPTX output, generate optimized slide structure
            if output_format == "pptx":
                slides = llm.generate_slide_structure(cleaned_content)
                if slides:
                    structured["slides"] = slides
                    logger.debug(f"Generated {len(slides)} slide structures")

            # Suggest chart data
            chart_suggestions = llm.suggest_chart_data(cleaned_content)
            if chart_suggestions:
                structured["charts"] = chart_suggestions
                logger.debug(f"Suggested {len(chart_suggestions)} charts")

        else:
            logger.info("LLM service not available - using basic transformation")

        state["structured_content"] = structured

        logger.info(
            f"Transformed content: title='{structured['title']}', "
            f"{len(cleaned_content)} chars (cleaned from {len(content)}), "
            f"enhanced={'slides' in structured or 'executive_summary' in structured}"
        )

    except Exception as e:
        error_msg = f"Transformation failed: {str(e)}"
        state["errors"].append(error_msg)
        logger.error(error_msg)

    return state
