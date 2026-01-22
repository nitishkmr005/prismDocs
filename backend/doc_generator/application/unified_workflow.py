"""
Unified LangGraph workflow for all content generation types.

Supports:
- Documents (PDF, Markdown, PPTX slides)
- Podcasts (audio generation)
- Mind Maps (hierarchical visualization)
- Images (generation and editing)

This workflow uses a routing architecture to direct requests
to the appropriate processing branch while sharing common
content extraction and enhancement steps.

Key Features:
- Checkpointing: Reuse extracted/enhanced content across output formats
- Session-based state: Same sources = same session = reuse work
"""

import time
from typing import Any, Callable, Optional

from langgraph.graph import END, StateGraph
from loguru import logger

from .unified_state import (
    UnifiedWorkflowState,
    get_output_branch,
    is_document_type,
    requires_content_extraction,
)

# Import existing document generation nodes
from .nodes import (
    detect_format_node,
    describe_images_node,
    enhance_content_node,
    generate_images_node,
    generate_output_node,
    parse_document_content_node,
    persist_image_manifest_node,
    transform_content_node,
    validate_output_node,
)

# Import new unified nodes
from .nodes.extract_sources import ingest_sources_node, route_by_output_type
from .nodes.summarize_sources import summarize_sources_node
from .nodes.podcast_nodes import (
    generate_podcast_script_node,
    synthesize_podcast_audio_node,
)
from .nodes.mindmap_nodes import generate_mindmap_node
from .nodes.image_nodes import generate_image_node, edit_image_node


def _build_step_metadata(output_type: str) -> tuple[dict, int]:
    """
    Build step metadata for logging progress.
    """
    if is_document_type(output_type):
        step_numbers = {
            "ingest_sources": 1,
            "summarize_sources": 2,
            "detect_format": 3,
            "parse_document_content": 4,
            "transform_content": 5,
            "enhance_content": 6,
            "generate_images": 7,
            "describe_images": 8,
            "persist_image_manifest": 9,
            "generate_output": 10,
            "validate_output": 11,
        }
        return step_numbers, 11
    return {"ingest_sources": 1, "summarize_sources": 2}, 2


def build_unified_workflow(checkpointer: Any = None) -> StateGraph:
    """
    Build the unified LangGraph workflow for all content types.

    Workflow Structure:

    1. COMMON: ingest_sources -> summarize_sources -> (Route by output_type)

    2a. DOCUMENT BRANCH:
        detect_format -> parse_document_content -> transform_content -> enhance_content
        -> generate_images -> describe_images -> generate_output -> validate_output

    2b. PODCAST BRANCH:
        generate_podcast_script -> synthesize_podcast_audio

    2c. MINDMAP BRANCH:
        generate_mindmap

    2d. IMAGE_GENERATE BRANCH:
        generate_image

    2e. IMAGE_EDIT BRANCH:
        edit_image

    Args:
        checkpointer: Optional LangGraph checkpointer for state persistence

    Returns:
        Compiled StateGraph ready for execution
    """
    workflow = StateGraph(UnifiedWorkflowState)

    # ==========================================
    # COMMON NODES
    # ==========================================
    # ingest_sources
    # Input: sources (file/url/text), output_type, api/model
    # Core: load files/URLs/text, parse/OCR images, merge content,
    #       write temp markdown for docs, record source metadata.
    # Output: raw_content, input_path (docs), metadata source_count/file_id
    # LLM: image understanding for image files only; 1 call per image source.
    workflow.add_node("ingest_sources", ingest_sources_node)
    # summarize_sources
    # Input: raw_content, request_data (provider/model)
    # Core: chunked map-reduce summarization without truncation; rewrite temp md for docs.
    # Output: summary_content, raw_content (summary), metadata summary stats
    # LLM: 1 call per chunk + 1 reduce call when multiple chunks.
    workflow.add_node("summarize_sources", summarize_sources_node)

    # ==========================================
    # DOCUMENT BRANCH NODES
    # (Wrapper nodes that adapt existing nodes to unified state)
    # ==========================================
    # doc_detect_format
    # Input: input_path
    # Core: detect format from URL or file extension; validate support.
    # Output: input_format
    workflow.add_node("doc_detect_format", _wrap_document_node(detect_format_node))
    # doc_parse_document_content
    # Input: input_format, input_path
    # Core: parse content with format parser; collect metadata; compute content hash.
    # Output: raw_content, metadata (title/page_count/content_hash)
    workflow.add_node(
        "doc_parse_document_content",
        _wrap_document_node(parse_document_content_node),
    )
    # doc_transform_content
    # Input: raw_content, input_format, metadata
    # Core: LLM transform to structured markdown (title/outline/sections/markers),
    #       reuse cache when valid, fallback to basic cleaning if needed.
    # Output: structured_content
    # LLM: 1 call per request when available (generate blog-style structure).
    workflow.add_node(
        "doc_transform_content", _wrap_document_node(transform_content_node)
    )
    # doc_enhance_content
    # Input: structured_content, output_format
    # Core: generate executive summary and slide structure when applicable.
    # Output: structured_content (summary/slides)
    # LLM: 0-2 calls (summary, slides) depending on missing fields/output_format.
    workflow.add_node("doc_enhance_content", _wrap_document_node(enhance_content_node))
    # doc_generate_images
    # Input: structured_content, metadata (image prefs), output_format
    # Core: decide image types, build prompts, generate/reuse assets per section.
    # Output: structured_content.section_images
    # LLM: 0-1 call per section for prompt generation (Gemini), when enabled.
    workflow.add_node("doc_generate_images", _wrap_document_node(generate_images_node))
    # doc_describe_images
    # Input: structured_content.section_images, markdown, metadata
    # Core: generate image descriptions; embed base64 for PDFs when enabled.
    # Output: structured_content.section_images (description/embed_base64)
    # LLM: 0-1 call per image when description is missing.
    workflow.add_node("doc_describe_images", _wrap_document_node(describe_images_node))
    # doc_persist_images
    # Input: structured_content.section_images, metadata.content_hash
    # Core: persist image manifest for cache reuse.
    # Output: manifest.json on disk
    workflow.add_node(
        "doc_persist_images", _wrap_document_node(persist_image_manifest_node)
    )
    # doc_generate_output
    # Input: structured_content, output_format, metadata
    # Core: render PDF/PPTX/Markdown, choose output path, cache structured content.
    # Output: output_path
    workflow.add_node("doc_generate_output", _wrap_document_node(generate_output_node))
    # doc_validate_output
    # Input: output_path, output_format
    # Core: validate file exists, non-empty, expected extension.
    # Output: errors (on failure)
    workflow.add_node("doc_validate_output", _wrap_document_node(validate_output_node))

    # ==========================================
    # PODCAST BRANCH NODES
    # ==========================================
    # podcast_generate_script
    # Input: raw_content, request_data (style/speakers/model)
    # Core: LLM generates JSON dialogue script + title/description.
    # Output: podcast_script, podcast_dialogue, podcast_title/description
    # LLM: 1 call per request for script generation.
    workflow.add_node("podcast_generate_script", generate_podcast_script_node)
    # podcast_synthesize_audio
    # Input: podcast_dialogue, speakers, gemini_api_key
    # Core: Gemini TTS synthesis, build WAV, compute duration.
    # Output: podcast_audio_base64, podcast_duration_seconds
    workflow.add_node("podcast_synthesize_audio", synthesize_podcast_audio_node)

    # ==========================================
    # MINDMAP BRANCH NODE
    # ==========================================
    # mindmap_generate
    # Input: raw_content, request_data (mode/model)
    # Core: LLM extracts concepts and builds hierarchical tree + summary.
    # Output: mindmap_tree, mindmap_mode
    # LLM: 1 call per request for mind map JSON output.
    workflow.add_node("mindmap_generate", generate_mindmap_node)

    # ==========================================
    # IMAGE BRANCH NODES
    # ==========================================
    # image_generate
    # Input: prompt/style/output_format, api key
    # Core: generate raster or SVG image with optional style.
    # Output: image_data, image_output_format, image_prompt_used
    # LLM: 1 model call per request (image generation).
    workflow.add_node("image_generate", generate_image_node)
    # image_edit
    # Input: source image, edit prompt, mode/style/region, api key
    # Core: edit image (basic/style/region) and return raster output.
    # Output: image_data, image_edit_mode
    # LLM: 1 model call per request (image edit).
    workflow.add_node("image_edit", edit_image_node)

    # ==========================================
    # WORKFLOW EDGES
    # ==========================================

    # Entry point
    workflow.set_entry_point("ingest_sources")
    workflow.add_edge("ingest_sources", "summarize_sources")

    # Route after summarization based on output_type
    workflow.add_conditional_edges(
        "summarize_sources",
        route_by_output_type,
        {
            "document": "doc_detect_format",
            "podcast": "podcast_generate_script",
            "mindmap": "mindmap_generate",
            "image_generate": "image_generate",
            "image_edit": "image_edit",
        },
    )

    # ==========================================
    # DOCUMENT BRANCH FLOW
    # ==========================================
    workflow.add_edge("doc_detect_format", "doc_parse_document_content")
    workflow.add_edge("doc_parse_document_content", "doc_transform_content")
    workflow.add_edge("doc_transform_content", "doc_enhance_content")
    workflow.add_edge("doc_enhance_content", "doc_generate_images")
    workflow.add_edge("doc_generate_images", "doc_describe_images")
    workflow.add_edge("doc_describe_images", "doc_persist_images")
    workflow.add_edge("doc_persist_images", "doc_generate_output")
    workflow.add_edge("doc_generate_output", "doc_validate_output")

    # Document validation with retry
    workflow.add_conditional_edges(
        "doc_validate_output",
        _should_retry_document,
        {"retry": "doc_generate_output", "end": END},
    )

    # ==========================================
    # PODCAST BRANCH FLOW
    # ==========================================
    workflow.add_edge("podcast_generate_script", "podcast_synthesize_audio")
    workflow.add_edge("podcast_synthesize_audio", END)

    # ==========================================
    # MINDMAP BRANCH FLOW (Single node)
    # ==========================================
    workflow.add_edge("mindmap_generate", END)

    # ==========================================
    # IMAGE BRANCH FLOWS (Single nodes)
    # ==========================================
    workflow.add_edge("image_generate", END)
    workflow.add_edge("image_edit", END)

    logger.debug("Built unified LangGraph workflow with routing for all content types")

    # Compile with or without checkpointer
    if checkpointer:
        logger.debug("Compiling workflow with checkpointer enabled")
        return workflow.compile(checkpointer=checkpointer)
    else:
        return workflow.compile()


def _wrap_document_node(original_node: Callable) -> Callable:
    """
    Wrap existing document generation nodes to work with UnifiedWorkflowState.

    The existing nodes expect WorkflowState, so we:
    1. Extract compatible fields to a WorkflowState-like dict
    2. Run the original node
    3. Merge results back to UnifiedWorkflowState

    Args:
        original_node: Original node function expecting WorkflowState

    Returns:
        Wrapped function expecting UnifiedWorkflowState
    """
    from ..domain.models import WorkflowState

    def wrapped(state: UnifiedWorkflowState) -> UnifiedWorkflowState:
        # Build compatible state for document nodes
        request_data = state.get("request_data", {})

        # Map output_type to output_format
        output_type = state.get("output_type", "")
        format_mapping = {
            "article_pdf": "pdf",
            "article_markdown": "markdown",
            "slide_deck_pdf": "pdf_from_pptx",
            "presentation_pptx": "pptx",
        }
        output_format = format_mapping.get(output_type, "pdf")

        # Create WorkflowState-compatible dict
        compat_state: WorkflowState = {
            "input_path": state.get("input_path", ""),
            "input_format": state.get("input_format", ""),
            "output_format": output_format,
            "raw_content": state.get("raw_content", ""),
            "structured_content": state.get("structured_content", {}),
            "output_path": state.get("output_path", ""),
            "errors": state.get("errors", []),
            "metadata": state.get("metadata", {}),
            "llm_service": state.get("llm_service"),
        }

        # Add request-specific metadata
        if request_data:
            preferences = request_data.get("preferences", {})
            compat_state["metadata"]["audience"] = preferences.get(
                "audience", "general"
            )
            compat_state["metadata"]["image_style"] = preferences.get(
                "image_style", "auto"
            )
            if "image_model" in request_data:
                compat_state["metadata"]["image_model"] = request_data.get(
                    "image_model"
                )
            if "max_slides" in preferences:
                compat_state["metadata"]["max_slides"] = preferences.get("max_slides")
            compat_state["metadata"]["provider"] = request_data.get("provider")
            compat_state["metadata"]["model"] = request_data.get("model")
            compat_state["metadata"]["output_type"] = state.get("output_type", "")
            enable_images = bool(preferences.get("enable_image_generation", True))
            compat_state["metadata"]["enable_image_generation"] = enable_images
            if compat_state["metadata"]["output_type"] in (
                "slide_deck_pdf",
                "presentation_pptx",
            ):
                compat_state["metadata"]["embed_in_pptx"] = enable_images
            compat_state["metadata"]["api_keys"] = {
                "content": state.get("api_key", ""),
                "image": (
                    state.get("gemini_api_key", "") or state.get("api_key", "")
                )
                if enable_images
                else "",
            }

        # Run original node
        result = original_node(compat_state)

        # Merge results back
        state["input_path"] = result.get("input_path", state.get("input_path", ""))
        state["input_format"] = result.get(
            "input_format", state.get("input_format", "")
        )
        state["raw_content"] = result.get("raw_content", state.get("raw_content", ""))
        state["structured_content"] = result.get(
            "structured_content", state.get("structured_content", {})
        )
        state["output_path"] = result.get("output_path", state.get("output_path", ""))
        state["errors"] = result.get("errors", [])
        state["metadata"] = result.get("metadata", state.get("metadata", {}))

        # Check for completion
        if result.get("output_path") and not result.get("errors"):
            state["completed"] = True

        return state

    return wrapped


def _should_retry_document(state: UnifiedWorkflowState) -> str:
    """
    Decide whether to retry document generation or end workflow.

    Args:
        state: Current workflow state

    Returns:
        "retry" or "end"
    """
    from ..infrastructure.settings import get_settings

    errors = state.get("errors", [])

    if not errors:
        return "end"

    max_retries = get_settings().generator.max_retries
    retry_count = state.get("metadata", {}).get("_retry_count", 0)

    if retry_count >= max_retries:
        logger.warning(f"Max retries reached ({retry_count}), ending workflow")
        return "end"

    last_error = errors[-1] if errors else ""
    if "Generation failed" in last_error or "Validation failed" in last_error:
        state["metadata"] = state.get("metadata", {})
        state["metadata"]["_retry_count"] = retry_count + 1
        logger.warning(f"Retrying generation (attempt {retry_count + 1}/{max_retries})")
        return "retry"

    return "end"


# ==========================================
# CHECKPOINTED WORKFLOW FUNCTIONS
# ==========================================


def run_unified_workflow_with_session(
    output_type: str,
    request_data: dict,
    api_key: str,
    gemini_api_key: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    reuse_content: bool = True,
    progress_callback: Optional[Callable] = None,
) -> tuple[UnifiedWorkflowState, str]:
    """
    Run the unified workflow with session-based checkpointing.

    This enables reusing extracted/enhanced content across different output types.
    Same sources = same session = shared work.

    Args:
        output_type: Target output type
        request_data: Request data specific to the output type
        api_key: Primary API key for LLM provider
        gemini_api_key: Optional Gemini API key for TTS/images
        user_id: Optional user identifier
        session_id: Optional explicit session ID (auto-generated if not provided)
        reuse_content: If True, attempt to reuse content from existing session

    Returns:
        Tuple of (final workflow state, session_id used)
    """
    from .checkpoint_manager import get_checkpoint_manager

    start_time = time.time()
    checkpoint_mgr = get_checkpoint_manager()

    # Generate or use provided session ID
    sources = request_data.get("sources", [])
    if not session_id:
        session_id = checkpoint_mgr.generate_session_id(sources, user_id)

    logger.info(
        f"Running workflow with session {session_id}, output_type={output_type}"
    )

    # Build workflow with checkpointer
    workflow = build_unified_workflow(checkpointer=checkpoint_mgr.checkpointer)

    # Get checkpoint config
    config = checkpoint_mgr.get_checkpoint_config(session_id)

    # Check if we have an existing checkpoint with content
    has_existing_content = False
    existing_state = None

    if reuse_content:
        try:
            # Try to get existing checkpoint state
            checkpoint = checkpoint_mgr.checkpointer.get(config)
            if checkpoint and checkpoint.get("channel_values"):
                existing_state = checkpoint.get("channel_values", {})
                raw_content = existing_state.get("raw_content", "")
                if raw_content:
                    has_existing_content = True
                    logger.info(
                        f"Found existing content in session {session_id} "
                        f"({len(raw_content)} chars), reusing for {output_type}"
                    )
        except Exception as e:
            logger.debug(f"Could not retrieve checkpoint: {e}")

    # Build initial state
    step_numbers, total_steps = _build_step_metadata(output_type)
    initial_state: UnifiedWorkflowState = {
        "output_type": output_type,
        "request_data": request_data,
        "api_key": api_key,
        "gemini_api_key": gemini_api_key or api_key,
        "user_id": user_id or "",
        "input_path": "",
        "input_format": "",
        "raw_content": "",
        "structured_content": {},
        "enhanced_content": {},
        "output_path": "",
        "errors": [],
        "metadata": {
            "session_id": session_id,
            "reused_content": has_existing_content,
            "step_numbers": step_numbers,
            "total_steps": total_steps,
        },
        "completed": False,
    }

    # If we have existing content, inject it to skip extraction
    if has_existing_content and existing_state:
        initial_state["raw_content"] = existing_state.get("raw_content", "")
        initial_state["structured_content"] = existing_state.get(
            "structured_content", {}
        )
        initial_state["enhanced_content"] = existing_state.get("enhanced_content", {})
        initial_state["input_path"] = existing_state.get("input_path", "")
        initial_state["input_format"] = existing_state.get("input_format", "")
        initial_state["metadata"]["source_count"] = existing_state.get(
            "metadata", {}
        ).get("source_count", 1)
        logger.debug(f"Injected existing content into state for {output_type}")

    # Execute workflow with checkpoint config
    try:
        token = None
        if progress_callback is not None:
            from ..infrastructure.logging_utils import (
                reset_progress_callback,
                set_progress_callback,
            )

            token = set_progress_callback(progress_callback)

        try:
            result = workflow.invoke(initial_state, config=config)
        finally:
            if token is not None:
                reset_progress_callback(token)
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        result = initial_state
        result["errors"] = [str(e)]

    # Record that we generated this output type
    checkpoint_mgr.record_output_generated(session_id, output_type)

    duration = time.time() - start_time
    reused_str = " (reused content)" if has_existing_content else ""
    logger.info(
        f"Unified workflow completed in {duration:.2f}s, "
        f"type={output_type}, session={session_id}{reused_str}"
    )

    return result, session_id


async def run_unified_workflow_async_with_session(
    output_type: str,
    request_data: dict,
    api_key: str,
    gemini_api_key: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    reuse_content: bool = True,
    progress_callback: Optional[Callable] = None,
) -> tuple[UnifiedWorkflowState, str]:
    """
    Async version of run_unified_workflow_with_session.

    Args:
        output_type: Target output type
        request_data: Request data specific to the output type
        api_key: Primary API key for LLM provider
        gemini_api_key: Optional Gemini API key for TTS/images
        user_id: Optional user identifier
        session_id: Optional explicit session ID
        reuse_content: If True, attempt to reuse content from existing session

    Returns:
        Tuple of (final workflow state, session_id used)
    """
    import asyncio

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: run_unified_workflow_with_session(
            output_type=output_type,
            request_data=request_data,
            api_key=api_key,
            gemini_api_key=gemini_api_key,
            user_id=user_id,
            session_id=session_id,
            reuse_content=reuse_content,
            progress_callback=progress_callback,
        ),
    )


def get_session_info(session_id: str) -> dict:
    """
    Get information about a session.

    Args:
        session_id: Session identifier

    Returns:
        Session metadata including outputs generated
    """
    from .checkpoint_manager import get_checkpoint_manager

    checkpoint_mgr = get_checkpoint_manager()
    return checkpoint_mgr.get_session_metadata(session_id)


# ==========================================
# LEGACY FUNCTIONS (NO CHECKPOINTING)
# ==========================================


async def run_unified_workflow_async(
    output_type: str,
    request_data: dict,
    api_key: str,
    gemini_api_key: Optional[str] = None,
    user_id: Optional[str] = None,
    progress_callback: Optional[Callable] = None,
) -> UnifiedWorkflowState:
    """
    Run the unified workflow asynchronously (without checkpointing).

    For checkpointing support, use run_unified_workflow_async_with_session.

    Args:
        output_type: Target output type
        request_data: Request data specific to the output type
        api_key: Primary API key for LLM provider
        gemini_api_key: Optional Gemini API key for TTS/images
        user_id: Optional user identifier
        progress_callback: Optional callback for progress updates

    Returns:
        Final workflow state
    """
    import asyncio

    start_time = time.time()

    # Build workflow without checkpointer
    workflow = build_unified_workflow()

    # Initial state
    step_numbers, total_steps = _build_step_metadata(output_type)
    initial_state: UnifiedWorkflowState = {
        "output_type": output_type,
        "request_data": request_data,
        "api_key": api_key,
        "gemini_api_key": gemini_api_key or api_key,
        "user_id": user_id or "",
        "input_path": "",
        "input_format": "",
        "raw_content": "",
        "structured_content": {},
        "enhanced_content": {},
        "output_path": "",
        "errors": [],
        "metadata": {"step_numbers": step_numbers, "total_steps": total_steps},
        "completed": False,
    }

    # Execute workflow
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, workflow.invoke, initial_state)
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        result = initial_state
        result["errors"] = [str(e)]

    duration = time.time() - start_time
    logger.info(f"Unified workflow completed in {duration:.2f}s, type={output_type}")

    return result


def run_unified_workflow(
    output_type: str,
    request_data: dict,
    api_key: str,
    gemini_api_key: Optional[str] = None,
    user_id: Optional[str] = None,
) -> UnifiedWorkflowState:
    """
    Run the unified workflow synchronously (without checkpointing).

    For checkpointing support, use run_unified_workflow_with_session.

    Args:
        output_type: Target output type
        request_data: Request data specific to the output type
        api_key: Primary API key for LLM provider
        gemini_api_key: Optional Gemini API key for TTS/images
        user_id: Optional user identifier

    Returns:
        Final workflow state
    """
    start_time = time.time()

    # Build workflow without checkpointer
    workflow = build_unified_workflow()

    # Initial state
    step_numbers, total_steps = _build_step_metadata(output_type)
    initial_state: UnifiedWorkflowState = {
        "output_type": output_type,
        "request_data": request_data,
        "api_key": api_key,
        "gemini_api_key": gemini_api_key or api_key,
        "user_id": user_id or "",
        "input_path": "",
        "input_format": "",
        "raw_content": "",
        "structured_content": {},
        "enhanced_content": {},
        "output_path": "",
        "errors": [],
        "metadata": {"step_numbers": step_numbers, "total_steps": total_steps},
        "completed": False,
    }

    # Execute workflow
    try:
        result = workflow.invoke(initial_state)
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        result = initial_state
        result["errors"] = [str(e)]

    duration = time.time() - start_time
    logger.info(f"Unified workflow completed in {duration:.2f}s, type={output_type}")

    return result
