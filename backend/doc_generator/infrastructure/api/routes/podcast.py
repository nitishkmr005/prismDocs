"""Podcast generation route with SSE streaming."""

from typing import AsyncIterator

from fastapi import APIRouter, Depends
from loguru import logger
from sse_starlette.sse import EventSourceResponse

from ..dependencies import APIKeys, extract_api_keys, get_api_key_for_provider
from ..schemas.podcast import (
    PodcastCompleteEvent,
    PodcastErrorEvent,
    PodcastProgressEvent,
    PodcastRequest,
)
from ..services.podcast import get_podcast_service

router = APIRouter(tags=["podcast"])


async def event_generator(
    request: PodcastRequest,
    api_key: str,
    user_id: str | None = None,
) -> AsyncIterator[dict]:
    """Generate SSE events for podcast creation.

    Args:
        request: Podcast generation request
        api_key: API key for LLM/TTS provider
        user_id: Optional user ID for logging

    Yields:
        SSE event dicts
    """
    service = get_podcast_service()

    async for event in service.generate(request, api_key, user_id):
        if isinstance(event, PodcastCompleteEvent):
            yield {"event": "complete", "data": event.model_dump_json()}
        elif isinstance(event, PodcastErrorEvent):
            yield {"event": "error", "data": event.model_dump_json()}
        elif isinstance(event, PodcastProgressEvent):
            yield {"event": "progress", "data": event.model_dump_json()}
        else:
            yield {"data": event.model_dump_json()}


@router.post(
    "/generate/podcast",
    summary="Generate a podcast (SSE stream)",
    description=(
        "Stream podcast generation progress via Server-Sent Events (SSE). "
        "Provide one or more sources (file_id, url, or text) and choose "
        "a podcast style (conversational, interview, educational, debate, storytelling). "
        "Returns audio as base64-encoded WAV with the generated script."
    ),
    response_description="SSE stream of progress events ending in complete/error.",
)
async def generate_podcast(
    request: PodcastRequest,
    api_keys: APIKeys = Depends(extract_api_keys),
) -> EventSourceResponse:
    """Generate a podcast from sources.

    Streams progress events via SSE, ending with completion or error.

    Args:
        request: Podcast generation request
        api_keys: API keys from headers

    Returns:
        SSE event stream
    """
    logger.info(
        f"=== Podcast generation: provider={request.provider}, "
        f"style={request.style}, sources={len(request.sources)}, "
        f"speakers={len(request.speakers)}, duration={request.duration_minutes}min ==="
    )

    # Validate API key for provider
    api_key = get_api_key_for_provider(request.provider, api_keys)
    logger.debug(f"API key validated for provider {request.provider}")

    return EventSourceResponse(
        event_generator(
            request=request,
            api_key=api_key,
            user_id=api_keys.user_id,
        )
    )
