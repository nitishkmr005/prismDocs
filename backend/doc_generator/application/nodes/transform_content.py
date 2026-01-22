"""
Content transformation node for LangGraph workflow.

Transforms raw content into structured blog-style format for generators.
Uses LLM to generate well-structured educational content with visual markers.
"""

from pathlib import Path

from loguru import logger

from ...domain.models import WorkflowState
from ...infrastructure.llm import LLMContentGenerator, get_content_generator
from ...infrastructure.settings import get_settings
from ...utils.content_cleaner import clean_content_for_output
from ...utils.content_cache import load_structured_content
from ...infrastructure.logging_utils import (
    log_node_start,
    log_node_end,
    log_progress,
    log_metric,
    log_cache_hit,
    log_subsection,
    resolve_step_number,
    resolve_total_steps,
)


def _detect_content_type(input_format: str, raw_content: str) -> str:
    """
    Detect the type of content for appropriate LLM transformation.
    
    Args:
        input_format: The detected input format (txt, pdf, md, etc.)
        raw_content: The raw content string
        
    Returns:
        Content type: "transcript", "slides", or "document"
    Invoked by: src/doc_generator/application/nodes/transform_content.py, src/doc_generator/application/workflow/nodes/transform_content.py
    """
    # Check for transcript indicators (timestamps)
    import re
    timestamp_pattern = r'^\d{1,2}:\d{2}(:\d{2})?\s*$'
    timestamp_count = len(re.findall(timestamp_pattern, raw_content, re.MULTILINE))
    
    # If many timestamps, it's likely a transcript
    if timestamp_count > 10:
        return "transcript"
    
    # PDF/PPTX inputs are likely slides
    if input_format in ("pdf", "pptx"):
        return "slides"
    
    # Default to document
    return "document"


def transform_content_node(state: WorkflowState) -> WorkflowState:
    """
    Transform raw content into structured blog-style format for generators.

    Uses LLM to:
    - Transform raw content (transcripts, docs) into well-structured blog posts
    - Insert visual markers where diagrams should appear
    - Generate inline mermaid diagrams for simple concepts
    - Create executive summaries and slide structures

    Args:
        state: Current workflow state

    Returns:
        Updated state with structured_content including:
        - markdown: Blog-style markdown content
        - title: Extracted/generated title
        - visual_markers: List of visual marker specifications
        - executive_summary: Brief summary (optional)
        - slides: Slide structures for PPTX (optional)
    Invoked by: src/doc_generator/application/graph_workflow.py, src/doc_generator/application/workflow/graph.py
    """
    log_node_start(
        "transform_content",
        step_number=resolve_step_number(state, "transform_content", 5),
        total_steps=resolve_total_steps(state, 9),
    )
    
    try:
        content = state.get("raw_content", "")
        metadata = state.get("metadata", {})
        output_format = state.get("output_format", "pdf")
        input_format = state.get("input_format", "txt")
        
        if not content:
            logger.warning("No content to transform")
            state["structured_content"] = {"markdown": "", "title": "Empty Document"}
            log_node_end("transform_content", success=True, details="No content to transform")
            return state
        
        # Detect content type for appropriate transformation
        content_type = _detect_content_type(input_format, content)
        topic = metadata.get("title", metadata.get("topic", ""))
        
        log_metric("Content Type", content_type)
        log_metric("Input Format", input_format)
        log_metric("Topic", topic or "Auto-detected")
        
        # Try cache reuse if requested/default and content hash matches
        settings = get_settings()
        if "use_cache" in metadata:
            use_cache = metadata.get("use_cache")
        elif "reuse_cache" in metadata:
            use_cache = metadata.get("reuse_cache")
        else:
            use_cache = settings.generator.reuse_cache_by_default

        if use_cache:
            log_subsection("Checking Content Cache")
            cached = load_structured_content(state.get("input_path", ""))
            if cached:
                cached_hash = cached.get("content_hash")
                current_hash = metadata.get("content_hash")
                if cached_hash and current_hash and cached_hash == current_hash:
                    state["structured_content"] = cached
                    metadata["from_cache"] = True
                    if "title" not in metadata or not metadata["title"]:
                        metadata["title"] = cached.get("title", metadata.get("title", "Document"))
                    state["metadata"] = metadata
                    log_cache_hit("content")
                    log_node_end("transform_content", success=True, 
                                details="Reused cached content")
                    return state
                log_progress("Cache miss - content hash mismatch")

        # Get content generator
        log_subsection("LLM Content Transformation")
        api_keys = metadata.get("api_keys", {})
        content_api_key = api_keys.get("content") if isinstance(api_keys, dict) else None
        provider = metadata.get("provider")
        model = metadata.get("model")
        content_generator = get_content_generator(
            api_key=content_api_key,
            provider=provider,
            model=model,
        )
        
        # Initialize structured content
        structured = {
            "title": metadata.get("title", "Document"),
            "visual_markers": [],
            "outline": "",
        }
        
        if content_generator.is_available():
            log_progress("LLM available - transforming to blog format")
            
            # Transform content using LLM
            max_tokens = metadata.get("max_tokens")
            if not max_tokens:
                max_tokens = settings.llm.content_max_tokens
            
            log_metric("Max Tokens", max_tokens)
            
            include_visual_markers = (
                metadata.get("enable_image_generation", True)
                and settings.image_generation.enable_all
            )

            generated = content_generator.generate_blog_content(
                raw_content=content,
                content_type=content_type,
                topic=topic,
                max_tokens=max_tokens,
                include_visual_markers=include_visual_markers,
                force_single_chunk=bool(metadata.get("summary_generated")),
            )
            
            # Store generated content
            structured["markdown"] = generated.markdown
            structured["title"] = generated.title
            structured["sections"] = generated.sections
            structured["outline"] = generated.outline
            
            # Convert visual markers to dict format for state
            structured["visual_markers"] = [
                {
                    "marker_id": m.marker_id,
                    "type": m.visual_type,
                    "title": m.title,
                    "description": m.description,
                    "position": m.position
                }
                for m in generated.visual_markers
            ]
            
            log_metric("Generated Length", len(generated.markdown), "chars")
            log_metric("Visual Markers", len(generated.visual_markers))
            log_metric("Sections", len(generated.sections))
            log_metric("Title", generated.title)
            
        else:
            # Fallback: Just clean the content
            log_progress("LLM not available - using basic content cleaning")
            cleaned_content = clean_content_for_output(content)
            structured["markdown"] = cleaned_content
            log_metric("Cleaned Length", len(cleaned_content), "chars")
        
        structured["content_hash"] = metadata.get("content_hash")
        state["structured_content"] = structured
        
        # Update metadata with generated title when filename-derived titles are used
        input_path = state.get("input_path", "")
        input_stem = Path(input_path).stem if input_path else ""
        current_title = metadata.get("title", "")
        if (
            not current_title
            or current_title == input_stem
            or input_stem.startswith("temp_input_")
        ):
            metadata["title"] = structured["title"]
            state["metadata"] = metadata
        
        log_node_end("transform_content", success=True,
                    details=f"Transformed to {len(structured.get('markdown', ''))} chars")

    except Exception as e:
        error_msg = f"Transformation failed: {str(e)}"
        state["errors"].append(error_msg)
        logger.error(error_msg)
        logger.exception("Transformation error details:")
        
        # Fallback to raw content
        state["structured_content"] = {
            "markdown": state.get("raw_content", ""),
            "title": state.get("metadata", {}).get("title", "Document"),
            "visual_markers": []
        }
        
        log_node_end("transform_content", success=False, details=error_msg)

    return state
