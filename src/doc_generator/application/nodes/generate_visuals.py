"""
Visualization generation node for LangGraph workflow.

Generates SVG visualizations based on content analysis.
Works with or without LLM - parses figure references and generates diagrams automatically.
"""

from loguru import logger

from ...domain.models import WorkflowState
from ...infrastructure.claude_svg_generator import generate_visualization_with_claude
from ...infrastructure.llm_service import get_llm_service
from ...infrastructure.settings import get_settings
from ...infrastructure.svg_generator import generate_visualization
from ...utils.figure_parser import extract_figure_references, generate_diagram_data, map_to_visual_type


def generate_visuals_node(state: WorkflowState) -> WorkflowState:
    """
    Generate SVG visualizations based on content analysis.

    Uses LLM to analyze content and suggest appropriate visualizations
    (architecture diagrams, flowcharts, comparisons, concept maps, mind maps).
    Generates SVG files and stores paths in state for embedding in output.

    Args:
        state: Current workflow state

    Returns:
        Updated state with generated visualization paths
    """
    try:
        content = state.get("raw_content", "")
        structured_content = state.get("structured_content", {})

        if not content:
            logger.debug("No content to analyze for visualizations")
            return state

        # Get output directory for SVG files from settings
        settings = get_settings()
        output_dir = settings.generator.visuals_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        # Try to get visualizations from LLM or parse content directly
        llm = state.get("llm_service") or get_llm_service()
        visualizations = []

        if llm.is_available():
            logger.info("Using LLM to analyze content for visualization opportunities")
            suggestions = llm.suggest_visualizations(content, max_visuals=3)

            for i, suggestion in enumerate(suggestions):
                vis_type = suggestion.get("type", "")
                title = suggestion.get("title", f"Visualization {i + 1}")
                data = suggestion.get("data", {})

                if not vis_type or not data:
                    continue

                # Generate SVG using Claude if available, otherwise use basic generator
                svg_filename = f"visual_{i}_{vis_type}.svg"
                svg_path = output_dir / svg_filename

                # Try Claude-powered generation first
                settings = get_settings()
                if settings.llm.use_claude_for_visuals:
                    svg_content = generate_visualization_with_claude(
                        visual_type=vis_type,
                        data=data,
                        title=title,
                        output_path=svg_path
                    )
                else:
                    svg_content = ""

                # Fallback to basic generator if Claude fails
                if not svg_content:
                    logger.debug(f"Using basic SVG generator for {vis_type}")
                    svg_content = generate_visualization(
                        visual_type=vis_type,
                        data=data,
                        title=title,
                        output_path=svg_path,
                        width=800,
                        height=500
                    )

                if svg_content:
                    visualizations.append({
                        "type": vis_type,
                        "title": title,
                        "path": str(svg_path),
                        "svg": svg_content
                    })
                    logger.debug(f"Generated {vis_type} visualization: {title}")

            logger.info(f"Generated {len(visualizations)} visualizations using LLM")
        else:
            # Fallback: Parse figure references from content
            logger.info("LLM not available - parsing figure references from content")
            figures = extract_figure_references(content)

            if figures:
                logger.info(f"Found {len(figures)} figure references in content")

                for figure in figures[:5]:  # Limit to first 5 figures
                    fig_num = figure['number']
                    caption = figure['caption']
                    fig_type = figure['type']

                    # Generate diagram data based on figure type and context
                    data = generate_diagram_data(figure)

                    if not data:
                        logger.debug(f"Could not generate data for Figure {fig_num}")
                        continue

                    # Map figure type to visual type
                    vis_type = map_to_visual_type(fig_type)

                    # Generate SVG
                    svg_filename = f"figure_{fig_num}_{fig_type}.svg"
                    svg_path = output_dir / svg_filename

                    try:
                        svg_content = generate_visualization(
                            visual_type=vis_type,
                            data=data,
                            title=f"Figure {fig_num}: {caption[:50]}{'...' if len(caption) > 50 else ''}",
                            output_path=svg_path,
                            width=800,
                            height=500
                        )

                        if svg_content:
                            visualizations.append({
                                "type": vis_type,
                                "title": f"Figure {fig_num}",
                                "caption": caption,
                                "path": str(svg_path),
                                "svg": svg_content,
                                "number": fig_num
                            })
                            logger.success(f"Generated Figure {fig_num}: {fig_type} diagram")
                    except Exception as e:
                        logger.warning(f"Failed to generate Figure {fig_num}: {e}")

                logger.info(f"Generated {len(visualizations)} diagrams from figure references")
            else:
                logger.info("No figure references found in content")

        # Store visualizations in structured content
        if visualizations:
            structured_content["visualizations"] = visualizations
            state["structured_content"] = structured_content

    except Exception as e:
        error_msg = f"Visualization generation failed: {str(e)}"
        state["errors"].append(error_msg)
        logger.error(error_msg)

    return state
