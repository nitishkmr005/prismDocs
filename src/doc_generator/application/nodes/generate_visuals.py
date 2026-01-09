"""
Visualization generation node for LangGraph workflow.

Generates SVG visualizations based on visual markers from LLM content transformation.
Visual markers are placed inline in the generated content where diagrams should appear.
Includes validation loop to ensure SVG quality.
"""

from pathlib import Path

from loguru import logger

from ...domain.models import WorkflowState
from ...infrastructure.claude_svg_generator import generate_visualization_with_claude
from ...infrastructure.llm_content_generator import VisualMarker, get_content_generator
from ...infrastructure.settings import get_settings
from ...infrastructure.svg_generator import generate_visualization
from ...infrastructure.svg_validator import SVGValidator, validate_svg


def _get_surrounding_context(content: str, position: int, context_size: int = 500) -> str:
    """
    Extract text surrounding a position in content for context.
    
    Args:
        content: Full content string
        position: Character position in content
        context_size: Number of characters to include before and after
        
    Returns:
        Surrounding context string
    """
    start = max(0, position - context_size)
    end = min(len(content), position + context_size)
    return content[start:end]


def _generate_with_validation(
    vis_type: str,
    data: dict,
    title: str,
    output_path: Path,
    use_claude: bool = True,
    max_retries: int = 3
) -> str:
    """
    Generate SVG with validation and retry loop.
    
    Attempts to generate SVG up to max_retries times, validating each result.
    If validation finds critical errors, regenerates with feedback.
    Minor issues are fixed automatically.
    
    Args:
        vis_type: Type of visualization
        data: Visualization data dictionary
        title: Title for the diagram
        output_path: Path to save SVG file
        use_claude: Whether to use Claude for generation
        max_retries: Maximum retry attempts
        
    Returns:
        Valid SVG content string
    """
    validator = SVGValidator()
    validation_feedback = None
    
    for attempt in range(max_retries):
        logger.debug(f"SVG generation attempt {attempt + 1}/{max_retries} for '{title}'")
        
        # Generate SVG
        svg_content = ""
        if use_claude:
            svg_content = generate_visualization_with_claude(
                visual_type=vis_type,
                data=data,
                title=title,
                output_path=None,  # Don't save yet - validate first
                validation_feedback=validation_feedback
            )
        
        # Fallback to basic generator if Claude failed or not available
        if not svg_content:
            logger.debug(f"Using basic SVG generator for {vis_type}")
            svg_content = generate_visualization(
                visual_type=vis_type,
                data=data,
                title=title,
                output_path=None,
                width=800,
                height=500
            )
        
        if not svg_content:
            logger.warning(f"Attempt {attempt + 1}: No SVG content generated for '{title}'")
            continue
        
        # Validate the generated SVG
        result = validate_svg(svg_content)
        
        if result.is_valid and len(result.warnings) == 0:
            # Perfect - save and return
            _save_svg(svg_content, output_path)
            logger.success(f"SVG validation passed for '{title}' on attempt {attempt + 1}")
            return svg_content
        
        if result.has_critical_errors:
            # Critical errors - need to regenerate with feedback
            logger.warning(f"Attempt {attempt + 1}: Critical SVG errors for '{title}': {result.errors}")
            validation_feedback = result.errors
            continue
        
        # Minor issues - try to fix
        if result.warnings:
            logger.debug(f"Attempt {attempt + 1}: SVG has warnings for '{title}': {result.warnings[:2]}")
            
            # Try to fix automatically
            fixed_svg, fixed_result = validator.validate_and_fix(svg_content)
            
            if fixed_result.is_valid:
                _save_svg(fixed_svg, output_path)
                logger.info(f"SVG auto-fixed and saved for '{title}'")
                return fixed_svg
            
            # If fix didn't work, accept with warnings (better than nothing)
            if not fixed_result.has_critical_errors:
                _save_svg(svg_content, output_path)
                logger.info(f"SVG saved with minor warnings for '{title}'")
                return svg_content
        
        # Set feedback for next attempt
        validation_feedback = result.errors + result.warnings[:2]
    
    # All retries exhausted - return last SVG or empty
    logger.warning(f"Max retries exhausted for '{title}', using last generated SVG")
    if svg_content:
        _save_svg(svg_content, output_path)
    return svg_content


def _save_svg(svg_content: str, path: Path) -> None:
    """Save SVG content to file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg_content, encoding="utf-8")
    logger.debug(f"Saved SVG: {path}")


def generate_visuals_node(state: WorkflowState) -> WorkflowState:
    """
    Generate SVG visualizations based on visual markers from content transformation.

    The transform_content node inserts visual markers like:
    [VISUAL:architecture:Title:Description]
    
    This node:
    1. Extracts visual markers from structured_content
    2. Generates structured data for each marker using LLM
    3. Creates SVG visualizations with validation loop
    4. Maps marker IDs to generated file paths for inline replacement

    Args:
        state: Current workflow state

    Returns:
        Updated state with generated visualization paths mapped to marker IDs
    """
    try:
        # Check if SVG generation is enabled
        settings = get_settings()
        if not settings.llm.use_claude_for_visuals:
            logger.info("SVG generation disabled (use_claude_for_visuals=false), skipping")
            return state
        
        structured_content = state.get("structured_content", {})
        markdown_content = structured_content.get("markdown", "")
        visual_markers = structured_content.get("visual_markers", [])
        
        if not markdown_content:
            logger.debug("No content available for visualization generation")
            return state

        # Get output directory for SVG files from settings
        output_dir = settings.generator.visuals_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        visualizations = []
        marker_to_path = {}  # Map marker_id -> path for inline replacement
        
        # Get content generator for visual data generation
        content_generator = get_content_generator()
        use_claude = settings.llm.use_claude_for_visuals
        
        # Process visual markers from content transformation
        if visual_markers:
            logger.info(f"Processing {len(visual_markers)} visual markers from content")
            
            for marker_dict in visual_markers:
                marker_id = marker_dict.get("marker_id", "")
                vis_type = marker_dict.get("type", "")
                title = marker_dict.get("title", "Visualization")
                description = marker_dict.get("description", "")
                position = marker_dict.get("position", 0)
                
                if not vis_type:
                    logger.debug(f"Skipping marker {marker_id} - no type specified")
                    continue
                
                # Skip mermaid markers - they're handled inline in PDF
                if vis_type == "mermaid":
                    logger.debug(f"Skipping mermaid marker {marker_id} - rendered inline")
                    continue
                
                # Create VisualMarker object for data generation
                marker = VisualMarker(
                    marker_id=marker_id,
                    visual_type=vis_type,
                    title=title,
                    description=description,
                    position=position
                )
                
                # Get surrounding context for better data generation
                context = _get_surrounding_context(markdown_content, position)
                
                # Generate structured data using LLM
                data = {}
                if content_generator.is_available():
                    data = content_generator.generate_visual_data(marker, context)
                
                if not data:
                    # Fallback: create basic data from description
                    data = _create_fallback_data(vis_type, title, description)
                
                if not data:
                    logger.warning(f"Could not generate data for marker: {title}")
                    continue
                
                # Generate SVG with validation loop
                svg_filename = f"{marker_id}_{vis_type}.svg"
                svg_path = output_dir / svg_filename
                
                svg_content = _generate_with_validation(
                    vis_type=vis_type,
                    data=data,
                    title=title,
                    output_path=svg_path,
                    use_claude=use_claude,
                    max_retries=3
                )
                
                if svg_content:
                    visualization = {
                        "marker_id": marker_id,
                        "type": vis_type,
                        "title": title,
                        "description": description,
                        "path": str(svg_path),
                        "svg": svg_content
                    }
                    visualizations.append(visualization)
                    marker_to_path[marker_id] = str(svg_path)
                    logger.success(f"Generated {vis_type}: {title}")
                else:
                    logger.warning(f"Failed to generate SVG for: {title}")
            
            logger.info(f"Generated {len(visualizations)} visualizations from markers")
        
        # Fallback: If no markers processed, generate from content analysis
        if not visualizations and markdown_content:
            logger.info("No visual markers - generating basic visualizations from content")
            
            # Generate at least one visualization summarizing the content
            default_data = {
                "components": [
                    {"id": "1", "name": "Input", "layer": "frontend"},
                    {"id": "2", "name": "Process", "layer": "backend"},
                    {"id": "3", "name": "Output", "layer": "database"}
                ],
                "connections": [
                    {"from": "1", "to": "2", "label": "data"},
                    {"from": "2", "to": "3", "label": "result"}
                ]
            }
            
            title = structured_content.get("title", "Overview")
            svg_path = output_dir / "overview_architecture.svg"
            
            svg_content = _generate_with_validation(
                vis_type="architecture",
                data=default_data,
                title=f"{title} Overview",
                output_path=svg_path,
                use_claude=use_claude,
                max_retries=2
            )
            
            if svg_content:
                visualizations.append({
                    "marker_id": "overview",
                    "type": "architecture",
                    "title": f"{title} Overview",
                    "path": str(svg_path),
                    "svg": svg_content
                })
                marker_to_path["overview"] = str(svg_path)
        
        # Store visualizations and marker mapping in structured content
        if visualizations:
            structured_content["visualizations"] = visualizations
            structured_content["marker_to_path"] = marker_to_path
            state["structured_content"] = structured_content
            logger.info(f"Total visualizations: {len(visualizations)}")

    except Exception as e:
        error_msg = f"Visualization generation failed: {str(e)}"
        state["errors"].append(error_msg)
        logger.error(error_msg)
        logger.exception("Visualization error details:")

    return state


def _create_fallback_data(vis_type: str, title: str, description: str) -> dict:
    """
    Create basic fallback data for visualization when LLM is unavailable.
    
    Args:
        vis_type: Type of visualization
        title: Title of the visual
        description: Description of what to show
        
    Returns:
        Basic structured data dictionary
    """
    # Map aliases to canonical types
    type_map = {
        "diagram": "architecture",
        "comparison": "comparison_visual",
        "chart": "comparison_visual",
        "graph": "flowchart",
    }
    canonical_type = type_map.get(vis_type.lower(), vis_type.lower())
    
    if canonical_type == "architecture":
        return {
            "components": [
                {"id": "1", "name": "Component A", "layer": "frontend"},
                {"id": "2", "name": "Component B", "layer": "backend"},
                {"id": "3", "name": "Component C", "layer": "database"}
            ],
            "connections": [
                {"from": "1", "to": "2", "label": "requests"},
                {"from": "2", "to": "3", "label": "queries"}
            ]
        }
    elif canonical_type == "flowchart":
        return {
            "nodes": [
                {"id": "1", "type": "start", "text": "Start"},
                {"id": "2", "type": "process", "text": "Process"},
                {"id": "3", "type": "end", "text": "End"}
            ],
            "edges": [
                {"from": "1", "to": "2"},
                {"from": "2", "to": "3"}
            ]
        }
    elif canonical_type == "comparison_visual":
        return {
            "items": ["Option A", "Option B"],
            "categories": [
                {"name": "Feature 1", "scores": [8, 6]},
                {"name": "Feature 2", "scores": [7, 9]}
            ]
        }
    elif canonical_type == "mind_map":
        return {
            "central": title,
            "branches": [
                {"text": "Branch 1", "children": ["Sub 1.1", "Sub 1.2"]},
                {"text": "Branch 2", "children": ["Sub 2.1", "Sub 2.2"]}
            ]
        }
    elif canonical_type == "concept_map":
        return {
            "concepts": [
                {"id": "1", "text": "Main Concept", "level": 0},
                {"id": "2", "text": "Related A", "level": 1},
                {"id": "3", "text": "Related B", "level": 1}
            ],
            "relationships": [
                {"from": "1", "to": "2", "label": "includes"},
                {"from": "1", "to": "3", "label": "relates to"}
            ]
        }
    
    # Default to architecture
    return {
        "components": [
            {"id": "1", "name": title[:20], "layer": "frontend"}
        ],
        "connections": []
    }
