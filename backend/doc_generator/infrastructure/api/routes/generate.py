"""Document generation route with SSE streaming."""

import datetime
from pathlib import Path
from typing import AsyncIterator

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from ..dependencies import APIKeys, extract_api_keys, get_api_key_for_provider
from ..schemas.requests import GenerateRequest
from ..schemas.responses import CacheHitEvent, CompleteEvent
from ..services.cache import CacheService
from ..services.generation import GenerationService

router = APIRouter(tags=["generate"])

# Shared service instances
_generation_service: GenerationService | None = None
_cache_service: CacheService | None = None


def get_generation_service() -> GenerationService:
    """
    Get or create generation service.
    Invoked by: src/doc_generator/infrastructure/api/routes/generate.py
    """
    global _generation_service
    if _generation_service is None:
        _generation_service = GenerationService()
    return _generation_service


def get_cache_service() -> CacheService:
    """
    Get or create cache service.
    Invoked by: src/doc_generator/infrastructure/api/routes/generate.py
    """
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


async def event_generator(
    request: GenerateRequest,
    api_key: str,
    image_api_key: str,
    generation_service: GenerationService,
    cache_service: CacheService,
) -> AsyncIterator[dict]:
    """Generate SSE events for document creation.

    Args:
        request: Generation request
        api_key: API key for LLM provider
        generation_service: Generation service
        cache_service: Cache service

    Yields:
        SSE event dicts
    Invoked by: src/doc_generator/infrastructure/api/routes/generate.py
    """
    from loguru import logger
    
    logger.info(f"Starting generation for {len(request.sources)} sources, cache.reuse={request.cache.reuse}")
    
    # Check cache first if reuse enabled
    if request.cache.reuse:
        cached = cache_service.get(request)
        if cached:
            logger.info(f"Cache hit! Returning cached result from {cached.get('created_at')}")
            cached_download_url = cached.get("download_url") or cached.get("output_path", "")
            cached_file_path = cached.get("file_path", "")
            if not cached_file_path and cached_download_url:
                if "/api/download/" in cached_download_url:
                    cached_file_path = cached_download_url.split("/api/download/", 1)[1]
                    cached_file_path = cached_file_path.split("?", 1)[0]
                else:
                    cached_path = Path(cached_download_url)
                    if cached_path.is_absolute():
                        try:
                            cached_file_path = str(
                                cached_path.relative_to(generation_service.storage.base_output_dir)
                            )
                        except ValueError:
                            cached_file_path = cached_path.name
                    else:
                        cached_file_path = str(cached_path)

            if cached_file_path:
                cached_output_path = generation_service.storage.base_output_dir / cached_file_path
                # StorageService.get_download_url: normalize cached output into a download link.
                download_url = generation_service.storage.get_download_url(cached_output_path)
            else:
                download_url = cached_download_url

            event = CacheHitEvent(
                download_url=download_url,
                file_path=cached_file_path,
                cached_at=datetime.datetime.fromtimestamp(
                    cached["created_at"]
                ).isoformat(),
            )
            yield {"data": event.model_dump_json()}
            return
        else:
            logger.info("Cache miss, proceeding with generation")

    # Generate document
    logger.info("Starting document generation...")
    async for event in generation_service.generate(
        request=request,
        api_key=api_key,
        image_api_key=image_api_key,
    ):
        logger.debug(f"Yielding event: {type(event).__name__}")
        yield {"data": event.model_dump_json()}

        # Cache successful completions
        if isinstance(event, CompleteEvent):
            logger.info(f"Generation complete, caching result: {event.download_url}")
            output_path = generation_service.storage.base_output_dir / event.file_path
            cache_service.set(
                request=request,
                output_path=output_path,
                file_path=event.file_path,
                metadata=event.metadata.model_dump(),
            )


@router.post(
    "/generate",
    summary="Generate a document (SSE stream)",
    description=(
        "Stream document generation progress via Server-Sent Events (SSE). "
        "Provide one or more sources (file_id, url, or text) and choose "
        "`output_format` of `pdf` or `pptx`. "
        "Use the returned `file_path` or `download_url` to fetch the output from "
        "`GET /api/download/{file_path}`."
    ),
    response_description="SSE stream of progress events ending in complete/cache_hit/error.",
)
async def generate_document(
    request: GenerateRequest,
    api_keys: APIKeys = Depends(extract_api_keys),
) -> EventSourceResponse:
    """Generate a document from sources.

    Streams progress events via SSE, ending with completion or error.

    Args:
        request: Generation request
        api_keys: API keys from headers

    Returns:
        SSE event stream
    Invoked by: (no references found)
    """
    from loguru import logger
    
    logger.info(f"=== Generate endpoint called: provider={request.provider}, format={request.output_format} ===")
    
    # Validate API key for provider
    api_key = get_api_key_for_provider(request.provider, api_keys)
    image_api_key = api_keys.image or api_key
    logger.debug(f"API key validated for provider {request.provider}")

    generation_service = get_generation_service()
    cache_service = get_cache_service()

    return EventSourceResponse(
        event_generator(
            request=request,
            api_key=api_key,
            image_api_key=image_api_key,
            generation_service=generation_service,
            cache_service=cache_service,
        )
    )
