"""
Output generation node for LangGraph workflow.

Generates PDF or PPTX from structured content.
"""

from pathlib import Path

from loguru import logger

from ...domain.exceptions import GenerationError
from ...domain.models import WorkflowState
from ...infrastructure.generators import get_generator
from ...infrastructure.settings import get_settings


def generate_output_node(state: WorkflowState) -> WorkflowState:
    """
    Generate PDF or PPTX from structured content.

    Args:
        state: Current workflow state

    Returns:
        Updated state with output_path
    Invoked by: src/doc_generator/application/graph_workflow.py, src/doc_generator/application/workflow/graph.py
    """
    try:
        # Get appropriate generator
        generator = get_generator(state["output_format"])

        # Check if custom output_path is provided
        custom_output_path = state.get("output_path", "")

        if custom_output_path:
            # Use custom output path if provided
            custom_path = Path(custom_output_path)
            output_dir = custom_path.parent
            # Generate with custom path by passing output_dir and using metadata to set filename
            state["metadata"]["custom_filename"] = custom_path.stem
            output_path = generator.generate(
                content=state["structured_content"],
                metadata=state["metadata"],
                output_dir=output_dir
            )
        else:
            # Get default output directory from settings
            settings = get_settings()

            # Create topic-specific output directory
            # Get folder name from metadata or derive from input path
            folder_name = state["metadata"].get("custom_filename") or state["metadata"].get("file_id")
            if not folder_name:
                input_path = state.get("input_path", "")
                if input_path:
                    input_p = Path(input_path)
                    # Look for file_id folder (f_xxx) in the path
                    # New structure: output/f_xxx/source/file.md
                    for part in input_p.parts:
                        if part.startswith("f_"):
                            folder_name = part
                            break
                    else:
                        # Fallback: use parent folder name if no f_xxx found
                        if input_p.parent.name == "source" and input_p.parent.parent.exists():
                            folder_name = input_p.parent.parent.name
                        else:
                            folder_name = input_p.parent.name if input_p.is_file() else input_p.name
                else:
                    folder_name = "output"

            # Create the file_id folder and format-specific subfolder
            output_format = state["output_format"]
            topic_output_dir = settings.generator.output_dir / folder_name / output_format
            topic_output_dir.mkdir(parents=True, exist_ok=True)

            logger.debug(f"Output will be saved to: {topic_output_dir}")

            # Generate output file in topic subfolder
            output_path = generator.generate(
                content=state["structured_content"],
                metadata=state["metadata"],
                output_dir=topic_output_dir
            )

        state["output_path"] = str(output_path)

        # Cache structured content for future use
        metadata = state.get("metadata", {})
        if "cache_content" in metadata:
            cache_content = metadata.get("cache_content", False)
        else:
            settings = get_settings()
            cache_content = settings.generator.reuse_cache_by_default

        if cache_content:
            from ...utils.content_cache import save_structured_content
            input_path = state.get("input_path", "")
            if input_path:
                save_structured_content(state["structured_content"], input_path)

        logger.info(f"Generated output: {output_path}")

    except GenerationError as e:
        error_msg = f"Generation failed: {str(e)}"
        state["errors"].append(error_msg)
        logger.error(error_msg)

    except Exception as e:
        error_msg = f"Unexpected generation error: {str(e)}"
        state["errors"].append(error_msg)
        logger.error(error_msg)

    return state
