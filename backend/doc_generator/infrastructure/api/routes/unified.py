"""
Unified generation route with session-based checkpointing.

This route provides a unified endpoint for all content types with
automatic session management for content reuse across formats.
"""

import datetime
import os
from pathlib import Path
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from sse_starlette.sse import EventSourceResponse

from ..dependencies import APIKeys, extract_api_keys, get_api_key_for_provider
from ..schemas.requests import GenerateRequest
from ..schemas.responses import (
    CacheHitEvent,
    CompleteEvent,
    ErrorEvent,
    ProgressEvent,
)
from ..schemas.podcast import (
    PodcastCompleteEvent,
    PodcastErrorEvent,
    PodcastProgressEvent,
    PodcastRequest,
)
from ..schemas.mindmap import (
    MindMapCompleteEvent,
    MindMapErrorEvent,
    MindMapProgressEvent,
    MindMapRequest,
)
from ..schemas.faq import (
    FAQCompleteEvent,
    FAQErrorEvent,
    FAQProgressEvent,
    FAQRequest,
)
from ..services.cache import CacheService
from ..services.unified_generation import get_unified_service

router = APIRouter(prefix="/unified", tags=["unified"])

_cache_service: CacheService | None = None
DEFAULT_INLINE_PREVIEW_BYTES = 8 * 1024 * 1024


def _get_max_inline_preview_bytes() -> int:
    """Return max bytes to include inline previews in responses."""
    raw_value = os.getenv("DOCGEN_MAX_INLINE_PREVIEW_BYTES")
    if raw_value is None:
        return DEFAULT_INLINE_PREVIEW_BYTES
    try:
        return max(0, int(raw_value))
    except ValueError:
        logger.warning(
            "Invalid DOCGEN_MAX_INLINE_PREVIEW_BYTES='%s', using default",
            raw_value,
        )
        return DEFAULT_INLINE_PREVIEW_BYTES


def get_cache_service() -> CacheService:
    """Get or create cache service."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


@router.post(
    "/generate",
    summary="Generate content with checkpointing (SSE stream)",
    description=(
        "Generate documents, podcasts, or mind maps with session-based checkpointing. "
        "When the same sources are used for different output types, the extracted content "
        "is reused automatically, significantly speeding up multi-format generation.\n\n"
        "**Session Management:**\n"
        "- If no `session_id` is provided, one is auto-generated based on source content hash\n"
        "- Same sources = same session = content reuse\n"
        "- The `session_id` is returned in the completion event\n\n"
        "**Workflow:**\n"
        "1. First request: Full content extraction and processing\n"
        "2. Subsequent requests (same sources): Reuse extracted content, only run format-specific logic"
    ),
)
async def generate_with_session(
    request: GenerateRequest,
    api_keys: APIKeys = Depends(extract_api_keys),
    session_id: str | None = Query(
        None, description="Optional session ID for content reuse"
    ),
) -> EventSourceResponse:
    """Generate content with session-based checkpointing.

    Returns:
        SSE event stream with progress and completion events
    """
    logger.info(
        f"=== Unified generate: provider={request.provider}, "
        f"format={request.output_format}, session={session_id} ==="
    )

    # 1. Get API keys
    # Determine the correct API key based on the provider (OpenAI/Anthropic/Gemini)
    api_key = get_api_key_for_provider(request.provider, api_keys)
    # Image generation might use a different key (or fallback to main provider key)
    image_api_key = api_keys.image or api_keys.google or api_key

    # 2. Initialize Services
    # - UnifiedService: Orchestrates the generation flow (Extract -> Draft -> Generate)
    # - CacheService: Checks if we've already generated this exact request before
    service = get_unified_service()
    cache_service = get_cache_service()

    # 3. Define Event Generator
    # This async generator will yield events (progress, complete, error) one by one.
    # It is wrapped in an EventSourceResponse for Server-Sent Events (SSE).
    async def event_generator() -> AsyncIterator[dict]:
        # 3a. Check Cache
        # If reuse=True, we check if a valid output already exists for this exact request hash.
        if request.cache.reuse:
            cached = cache_service.get(request)
            if cached:
                # ... (Cache hit logic: resolve paths, read file content for preview, yield CacheHitEvent) ...
                cached_download_url = cached.get("download_url") or cached.get(
                    "output_path", ""
                )
                cached_file_path = cached.get("file_path", "")
                if not cached_file_path and cached_download_url:
                    if "/api/download/" in cached_download_url:
                        cached_file_path = cached_download_url.split(
                            "/api/download/", 1
                        )[1]
                        cached_file_path = cached_file_path.split("?", 1)[0]
                    else:
                        cached_path = Path(cached_download_url)
                        if cached_path.is_absolute():
                            try:
                                cached_file_path = str(
                                    cached_path.relative_to(
                                        service.storage.base_output_dir
                                    )
                                )
                            except ValueError:
                                cached_file_path = cached_path.name
                        else:
                            cached_file_path = str(cached_path)

                if cached_file_path:
                    cached_output_path = (
                        service.storage.base_output_dir / cached_file_path
                    )
                    download_url = service.storage.get_download_url(cached_output_path)
                else:
                    download_url = cached_download_url

                pdf_base64 = None
                markdown_content = None
                if cached_file_path:
                    cached_path = service.storage.base_output_dir / cached_file_path
                    if cached_path.exists():
                        import base64

                        suffix = cached_path.suffix.lower()
                        max_preview_bytes = _get_max_inline_preview_bytes()
                        file_size = cached_path.stat().st_size
                        try:
                            if suffix == ".pdf":
                                if (
                                    max_preview_bytes > 0
                                    and file_size <= max_preview_bytes
                                ):
                                    with open(cached_path, "rb") as f:
                                        pdf_base64 = base64.b64encode(f.read()).decode(
                                            "utf-8"
                                        )
                                else:
                                    logger.info(
                                        "Skipping inline PDF preview (%s bytes > %s)",
                                        file_size,
                                        max_preview_bytes,
                                    )
                            elif suffix == ".md":
                                if (
                                    max_preview_bytes > 0
                                    and file_size <= max_preview_bytes
                                ):
                                    markdown_content = cached_path.read_text(
                                        encoding="utf-8"
                                    )
                                else:
                                    logger.info(
                                        "Skipping inline markdown preview (%s bytes > %s)",
                                        file_size,
                                        max_preview_bytes,
                                    )
                        except Exception as e:
                            logger.warning(
                                f"Could not read cached file for preview: {e}"
                            )

                event = CacheHitEvent(
                    download_url=download_url,
                    file_path=cached_file_path,
                    cached_at=datetime.datetime.fromtimestamp(
                        cached["created_at"]
                    ).isoformat(),
                    pdf_base64=pdf_base64,
                    markdown_content=markdown_content,
                )
                yield {"event": "cache_hit", "data": event.model_dump_json()}
                return

        # 3b. New Generation (Cache Miss or Force Regenerate)
        # Convert Pydantic models to dicts for the service layer
        sources = [s.model_dump() for s in request.sources]
        preferences = request.preferences.model_dump() if request.preferences else {}

        # Call the unified service which handles:
        # - Content Extraction (web scraping, PDF parsing, etc.)
        # - Checkpointing (saving extraction state to session)
        # - Content Drafting (LLM generation)
        # - Final Document Assembly (PDF/PPTX creation)
        async for event in service.generate_document(
            sources=sources,
            output_format=request.output_format.value,
            preferences=preferences,
            api_key=api_key,
            image_api_key=image_api_key,
            provider=request.provider.value,
            model=request.model,
            image_model=request.image_model,
            user_id=api_keys.user_id,
            session_id=session_id,
        ):
            if isinstance(event, CompleteEvent):
                output_path = service.storage.base_output_dir / event.file_path
                cache_service.set(
                    request=request,
                    output_path=output_path,
                    file_path=event.file_path,
                    metadata=event.metadata.model_dump(),
                )
                yield {"event": "complete", "data": event.model_dump_json()}
            elif isinstance(event, ErrorEvent):
                yield {"event": "error", "data": event.model_dump_json()}
            elif isinstance(event, ProgressEvent):
                yield {"event": "progress", "data": event.model_dump_json()}
            else:
                yield {"data": event.model_dump_json()}

    return EventSourceResponse(event_generator())


@router.post(
    "/generate/podcast",
    summary="Generate podcast with checkpointing (SSE stream)",
    description=(
        "Generate a podcast with session-based checkpointing. "
        "If the sources were previously used for document generation in the same session, "
        "the extracted content is reused."
    ),
)
async def generate_podcast_with_session(
    request: PodcastRequest,
    api_keys: APIKeys = Depends(extract_api_keys),
    session_id: str | None = Query(
        None, description="Optional session ID for content reuse"
    ),
) -> EventSourceResponse:
    """Generate podcast with session-based checkpointing."""
    logger.info(
        f"=== Unified podcast: provider={request.provider}, "
        f"style={request.style}, session={session_id} ==="
    )

    api_key = get_api_key_for_provider(request.provider, api_keys)
    gemini_api_key = api_keys.google

    if not gemini_api_key:
        raise HTTPException(
            status_code=401,
            detail="Podcast generation requires Gemini API key (X-Google-Key header) for TTS",
        )

    service = get_unified_service()

    async def event_generator() -> AsyncIterator[dict]:
        sources = [s.model_dump() for s in request.sources]
        speakers = [s.model_dump() for s in request.speakers]

        async for event in service.generate_podcast(
            sources=sources,
            style=request.style.value,
            speakers=speakers,
            duration_minutes=request.duration_minutes,
            api_key=api_key,
            gemini_api_key=gemini_api_key,
            provider=request.provider.value,
            model=request.model,
            user_id=api_keys.user_id,
            session_id=session_id,
        ):
            if isinstance(event, PodcastCompleteEvent):
                yield {"event": "complete", "data": event.model_dump_json()}
            elif isinstance(event, PodcastErrorEvent):
                yield {"event": "error", "data": event.model_dump_json()}
            elif isinstance(event, PodcastProgressEvent):
                yield {"event": "progress", "data": event.model_dump_json()}
            else:
                yield {"data": event.model_dump_json()}

    return EventSourceResponse(event_generator())


@router.post(
    "/generate/mindmap",
    summary="Generate mind map with checkpointing (SSE stream)",
    description=(
        "Generate a mind map with session-based checkpointing. "
        "If the sources were previously used for document or podcast generation in the same session, "
        "the extracted content is reused."
    ),
)
async def generate_mindmap_with_session(
    request: MindMapRequest,
    api_keys: APIKeys = Depends(extract_api_keys),
    session_id: str | None = Query(
        None, description="Optional session ID for content reuse"
    ),
) -> EventSourceResponse:
    """Generate mind map with session-based checkpointing."""
    logger.info(
        f"=== Unified mindmap: provider={request.provider}, "
        f"mode={request.mode}, session={session_id} ==="
    )

    api_key = get_api_key_for_provider(request.provider, api_keys)
    service = get_unified_service()

    async def event_generator() -> AsyncIterator[dict]:
        sources = [s.model_dump() for s in request.sources]

        async for event in service.generate_mindmap(
            sources=sources,
            mode=request.mode.value,
            api_key=api_key,
            provider=request.provider.value,
            model=request.model,
            user_id=api_keys.user_id,
            session_id=session_id,
        ):
            if isinstance(event, MindMapCompleteEvent):
                yield {"event": "complete", "data": event.model_dump_json()}
            elif isinstance(event, MindMapErrorEvent):
                yield {"event": "error", "data": event.model_dump_json()}
            elif isinstance(event, MindMapProgressEvent):
                yield {"event": "progress", "data": event.model_dump_json()}
            else:
                yield {"data": event.model_dump_json()}

    return EventSourceResponse(event_generator())


@router.post(
    "/generate/faq",
    summary="Generate FAQ cards with checkpointing (SSE stream)",
    description=(
        "Generate FAQ question-answer cards from source content. "
        "If the sources were previously used for other outputs in the same session, "
        "the extracted content is reused."
    ),
)
async def generate_faq_with_session(
    request: FAQRequest,
    api_keys: APIKeys = Depends(extract_api_keys),
    session_id: str | None = Query(
        None, description="Optional session ID for content reuse"
    ),
) -> EventSourceResponse:
    """Generate FAQ with session-based checkpointing."""
    logger.info(
        f"=== Unified FAQ: provider={request.provider}, session={session_id} ==="
    )

    api_key = get_api_key_for_provider(request.provider, api_keys)
    service = get_unified_service()

    async def event_generator() -> AsyncIterator[dict]:
        sources = [s.model_dump() for s in request.sources]

        async for event in service.generate_faq(
            sources=sources,
            api_key=api_key,
            provider=request.provider.value,
            model=request.model,
            user_id=api_keys.user_id,
            session_id=session_id,
        ):
            if isinstance(event, FAQCompleteEvent):
                yield {"event": "complete", "data": event.model_dump_json()}
            elif isinstance(event, FAQErrorEvent):
                yield {"event": "error", "data": event.model_dump_json()}
            elif isinstance(event, FAQProgressEvent):
                yield {"event": "progress", "data": event.model_dump_json()}
            else:
                yield {"data": event.model_dump_json()}

    return EventSourceResponse(event_generator())


@router.get(
    "/session/{session_id}",
    summary="Get session information",
    description="Get metadata about a generation session including what outputs were generated.",
)
async def get_session_info(session_id: str) -> dict:
    """Get information about a session.

    Args:
        session_id: The session ID

    Returns:
        Session metadata including outputs generated
    """
    from ....application import get_session_info as app_get_session_info

    info = app_get_session_info(session_id)
    return {
        "session_id": session_id,
        "created_at": info.get("created_at"),
        "outputs_generated": info.get("outputs_generated", []),
        "last_generated": info.get("last_generated"),
        "last_generated_at": info.get("last_generated_at"),
    }
