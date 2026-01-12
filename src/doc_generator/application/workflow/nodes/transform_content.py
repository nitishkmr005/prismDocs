"""
Content transformation node for LangGraph workflow.

Transforms raw content into structured blog-style format for generators.
Uses LLM to generate well-structured educational content with visual markers.
"""

from loguru import logger

from ...domain.models import WorkflowState
from ...infrastructure.llm import LLMContentGenerator, get_content_generator
from ...infrastructure.llm import get_llm_service
from ...infrastructure.settings import get_settings
from ...utils.content_cleaner import clean_content_for_output
from ...utils.content_cache import load_structured_content


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
    try:
        content = state.get("raw_content", "")
        metadata = state.get("metadata", {})
        output_format = state.get("output_format", "pdf")
        input_format = state.get("input_format", "txt")
        
        if not content:
            logger.warning("No content to transform")
            state["structured_content"] = {"markdown": "", "title": "Empty Document"}
            return state
        
        # Detect content type for appropriate transformation
        content_type = _detect_content_type(input_format, content)
        topic = metadata.get("title", metadata.get("topic", ""))
        
        logger.info(f"Transforming content: type={content_type}, format={input_format}, topic={topic}")
        
        # Try cache reuse if requested/default and content hash matches
        settings = get_settings()
        if "use_cache" in metadata:
            use_cache = metadata.get("use_cache")
        elif "reuse_cache" in metadata:
            use_cache = metadata.get("reuse_cache")
        else:
            use_cache = settings.generator.reuse_cache_by_default

        if use_cache:
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
                    logger.info("Reused cached structured content (content hash match)")
                    return state
                logger.info("Cache ignored due to content hash mismatch")

        # Get content generator
        content_generator = get_content_generator()
        
        # Initialize structured content
        structured = {
            "title": metadata.get("title", "Document"),
            "visual_markers": [],
            "outline": "",
        }
        
        if content_generator.is_available():
            logger.info("LLM Content Generator available - transforming to blog format")
            
            # Transform content using LLM
            max_tokens = metadata.get("max_tokens")
            if not max_tokens:
                max_tokens = 8000
            generated = content_generator.generate_blog_content(
                raw_content=content,
                content_type=content_type,
                topic=topic,
                max_tokens=max_tokens,
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
            
            logger.info(
                f"LLM transformation complete: {len(generated.markdown)} chars, "
                f"{len(generated.visual_markers)} visual markers, "
                f"{len(generated.sections)} sections"
            )
            
            # Also get LLM service for additional enhancements
            llm = state.get("llm_service") or get_llm_service()
            
            if llm.is_available():
                # Generate executive summary from the blog content
                executive_summary = llm.generate_executive_summary(generated.markdown)
                if executive_summary:
                    structured["executive_summary"] = executive_summary
                    logger.debug("Generated executive summary")
                
                # For PPTX output, generate optimized slide structure
                if output_format == "pptx":
                    slides = llm.generate_slide_structure(generated.markdown)
                    if slides:
                        structured["slides"] = slides
                        logger.debug(f"Generated {len(slides)} slide structures")
                
        else:
            # Fallback: Just clean the content
            logger.info("LLM not available - using basic content cleaning")
            cleaned_content = clean_content_for_output(content)
            structured["markdown"] = cleaned_content
            
            # Try to get basic enhancements from llm_service
            llm = state.get("llm_service") or get_llm_service()
            if llm.is_available():
                executive_summary = llm.generate_executive_summary(cleaned_content)
                if executive_summary:
                    structured["executive_summary"] = executive_summary
                
                if output_format == "pptx":
                    slides = llm.generate_slide_structure(cleaned_content)
                    if slides:
                        structured["slides"] = slides
        
        structured["content_hash"] = metadata.get("content_hash")
        state["structured_content"] = structured
        
        # Update metadata with generated title
        if "title" not in metadata or not metadata["title"]:
            metadata["title"] = structured["title"]
            state["metadata"] = metadata
        
        logger.info(
            f"Transformed content: title='{structured['title']}', "
            f"{len(structured.get('markdown', ''))} chars, "
            f"{len(structured.get('visual_markers', []))} visual markers"
        )

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

    return state
