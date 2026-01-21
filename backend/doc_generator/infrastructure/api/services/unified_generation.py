"""
Unified generation service using LangGraph workflow with checkpointing.

This service provides a unified interface for all content generation types
while enabling session-based state reuse across output formats.
"""

import base64
import os
import uuid
from pathlib import Path
from typing import AsyncIterator, Callable, Optional

from loguru import logger

from ....application import (
    get_checkpoint_manager,
    run_unified_workflow_with_session,
)
from ....application.unified_state import UnifiedWorkflowState
from ..schemas.responses import (
    CompleteEvent,
    ErrorEvent,
    ProgressEvent,
    CompletionMetadata,
    GenerationStatus,
)
from ..schemas.podcast import (
    PodcastCompleteEvent,
    PodcastErrorEvent,
    PodcastProgressEvent,
)
from ..schemas.mindmap import (
    MindMapCompleteEvent,
    MindMapErrorEvent,
    MindMapProgressEvent,
    MindMapTree,
    MindMapNode,
    MindMapMode,
)
from .storage import StorageService

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


class UnifiedGenerationService:
    """
    Unified service for all content generation types with checkpointing.

    Features:
    - Session-based state reuse across output formats
    - Automatic content deduplication
    - Faster multi-format generation
    """

    def __init__(self, storage_service: Optional[StorageService] = None):
        """Initialize unified generation service."""
        self.storage = storage_service or StorageService()
        self.checkpoint_manager = get_checkpoint_manager()

    async def generate_document(
        self,
        sources: list[dict],
        output_format: str,
        preferences: dict,
        api_key: str,
        image_api_key: Optional[str] = None,
        provider: str = "gemini",
        model: str = "gemini-2.5-flash",
        image_model: str = "gemini-2.5-flash-image",
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> AsyncIterator:
        """
        Generate a document with checkpointing support.

        Args:
            sources: List of source items (file, url, text)
            output_format: Target format (pdf, pptx, markdown)
            preferences: Generation preferences
            api_key: Primary API key
            image_api_key: Optional Gemini key for images
            provider: LLM provider
            model: Model name
            user_id: Optional user ID
            session_id: Optional session ID for content reuse

        Yields:
            Progress and completion events
        """
        # Map output_format to unified output_type
        format_mapping = {
            "pdf": "article_pdf",
            "pptx": "presentation_pptx",
            "markdown": "article_markdown",
            "pdf_from_pptx": "slide_deck_pdf",
        }
        output_type = format_mapping.get(output_format, "article_pdf")

        # Build request data
        request_data = {
            "sources": sources,
            "preferences": preferences,
            "provider": provider,
            "model": model,
            "image_model": image_model,
        }

        # Yield initial progress
        yield ProgressEvent(
            status=GenerationStatus.PARSING,
            progress=5,
            message="Starting document generation...",
        )

        try:
            # Run unified workflow with checkpointing
            yield ProgressEvent(
                status=GenerationStatus.TRANSFORMING,
                progress=10,
                message="Processing content...",
            )
            import asyncio

            loop = asyncio.get_running_loop()
            progress_queue: asyncio.Queue[ProgressEvent] = asyncio.Queue()
            workflow_status_map = {
                "detect_format": GenerationStatus.PARSING,
                "parse_content": GenerationStatus.PARSING,
                "transform_content": GenerationStatus.TRANSFORMING,
                "enhance_content": GenerationStatus.TRANSFORMING,
                "generate_images": GenerationStatus.GENERATING_IMAGES,
                "describe_images": GenerationStatus.GENERATING_IMAGES,
                "persist_image_manifest": GenerationStatus.GENERATING_IMAGES,
                "generate_output": GenerationStatus.GENERATING_OUTPUT,
                "validate_output": GenerationStatus.GENERATING_OUTPUT,
            }
            workflow_progress_base = 30
            workflow_progress_span = 60

            def workflow_progress(
                step_number: int,
                total_steps: int,
                node_name: str,
                display_name: str,
            ) -> None:
                status = workflow_status_map.get(
                    node_name, GenerationStatus.TRANSFORMING
                )
                progress = workflow_progress_base + int(
                    (step_number / max(total_steps, 1)) * workflow_progress_span
                )
                message = f"STEP {step_number}/{total_steps}: {display_name}"
                event = ProgressEvent(
                    status=status,
                    progress=progress,
                    message=message,
                )
                loop.call_soon_threadsafe(progress_queue.put_nowait, event)

            workflow_future = loop.run_in_executor(
                None,
                lambda: run_unified_workflow_with_session(
                    output_type=output_type,
                    request_data=request_data,
                    api_key=api_key,
                    gemini_api_key=image_api_key,
                    user_id=user_id,
                    session_id=session_id,
                    progress_callback=workflow_progress,
                ),
            )

            while True:
                if workflow_future.done() and progress_queue.empty():
                    break
                try:
                    event = await asyncio.wait_for(
                        progress_queue.get(), timeout=0.2
                    )
                    yield event
                except asyncio.TimeoutError:
                    continue

            result, session_id = await workflow_future

            # Check for errors
            if result.get("errors"):
                yield ErrorEvent(
                    error="\n".join(result["errors"]),
                    code="generation_error",
                )
                return

            # Get output path
            output_path = result.get("output_path", "")
            if not output_path:
                yield ErrorEvent(
                    error="No output file generated",
                    code="no_output",
                )
                return

            yield ProgressEvent(
                status=GenerationStatus.GENERATING_OUTPUT,
                progress=90,
                message="Finalizing...",
            )

            # Read file for inline preview
            pdf_base64 = None
            markdown_content = None

            path = Path(output_path)
            if path.exists():
                max_preview_bytes = _get_max_inline_preview_bytes()
                file_size = path.stat().st_size
                suffix = path.suffix.lower()
                if suffix == ".pdf":
                    if max_preview_bytes > 0 and file_size <= max_preview_bytes:
                        with open(path, "rb") as f:
                            pdf_base64 = base64.b64encode(f.read()).decode("utf-8")
                    else:
                        logger.info(
                            "Skipping inline PDF preview (%s bytes > %s)",
                            file_size,
                            max_preview_bytes,
                        )
                elif suffix == ".md":
                    if max_preview_bytes > 0 and file_size <= max_preview_bytes:
                        markdown_content = path.read_text(encoding="utf-8")
                    else:
                        logger.info(
                            "Skipping inline markdown preview (%s bytes > %s)",
                            file_size,
                            max_preview_bytes,
                        )

            # Build response
            download_url = self.storage.get_download_url(Path(output_path))
            file_path = str(Path(output_path).relative_to(self.storage.base_output_dir))

            metadata = result.get("metadata", {})

            yield CompleteEvent(
                download_url=download_url,
                file_path=file_path,
                metadata=CompletionMetadata(
                    title=metadata.get("title", "Document"),
                    pages=metadata.get("pages", 1),
                    slides=metadata.get("slides", 0),
                    images_generated=metadata.get("images", 0),
                ),
                session_id=session_id,
                pdf_base64=pdf_base64,
                markdown_content=markdown_content,
            )

        except Exception as e:
            logger.error(f"Document generation failed: {e}")
            yield ErrorEvent(
                error=str(e),
                code="internal_error",
            )

    async def generate_podcast(
        self,
        sources: list[dict],
        style: str,
        speakers: list[dict],
        duration_minutes: int,
        api_key: str,
        gemini_api_key: str,
        provider: str = "gemini",
        model: str = "gemini-2.5-flash",
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> AsyncIterator:
        """
        Generate a podcast with checkpointing support.

        Args:
            sources: List of source items
            style: Podcast style
            speakers: Speaker configurations
            duration_minutes: Target duration
            api_key: Primary API key
            gemini_api_key: Gemini API key for TTS
            provider: LLM provider
            model: Model name
            user_id: Optional user ID
            session_id: Optional session ID for content reuse

        Yields:
            Progress and completion events
        """
        request_data = {
            "sources": sources,
            "style": style,
            "speakers": speakers,
            "duration_minutes": duration_minutes,
            "provider": provider,
            "model": model,
        }

        yield PodcastProgressEvent(
            stage="extracting",
            percent=5,
            message="Starting podcast generation...",
        )

        try:
            # Check if we can reuse content from existing session
            if session_id:
                info = self.checkpoint_manager.get_session_metadata(session_id)
                if info.get("outputs_generated"):
                    yield PodcastProgressEvent(
                        stage="extracting",
                        percent=10,
                        message=f"Reusing content from session (previously: {', '.join(info['outputs_generated'])})",
                    )

            result, session_id = await self._run_workflow_async(
                output_type="podcast",
                request_data=request_data,
                api_key=api_key,
                gemini_api_key=gemini_api_key,
                user_id=user_id,
                session_id=session_id,
            )

            if result.get("errors"):
                yield PodcastErrorEvent(
                    message=result["errors"][0],
                    code="generation_error",
                )
                return

            # Get audio data
            audio_base64 = result.get("podcast_audio_base64", "")
            if not audio_base64:
                yield PodcastErrorEvent(
                    message="Podcast generation failed - no audio generated",
                    code="no_audio",
                )
                return

            yield PodcastCompleteEvent(
                audio_base64=audio_base64,
                title=result.get("podcast_title", "Podcast Episode"),
                description=result.get("podcast_description", ""),
                duration_seconds=result.get("podcast_duration_seconds", 0.0),
                script=result.get("podcast_dialogue", []),
                session_id=session_id,
            )

        except Exception as e:
            logger.error(f"Podcast generation failed: {e}")
            yield PodcastErrorEvent(
                message=str(e),
                code="internal_error",
            )

    async def generate_mindmap(
        self,
        sources: list[dict],
        mode: str,
        api_key: str,
        provider: str = "gemini",
        model: str = "gemini-2.5-flash",
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> AsyncIterator:
        """
        Generate a mind map with checkpointing support.

        Args:
            sources: List of source items
            mode: Generation mode
            api_key: Primary API key
            provider: LLM provider
            model: Model name
            user_id: Optional user ID
            session_id: Optional session ID for content reuse

        Yields:
            Progress and completion events
        """
        request_data = {
            "sources": sources,
            "mode": mode,
            "provider": provider,
            "model": model,
        }

        yield MindMapProgressEvent(
            stage="extracting",
            percent=5,
            message="Starting mind map generation...",
        )

        try:
            result, session_id = await self._run_workflow_async(
                output_type="mindmap",
                request_data=request_data,
                api_key=api_key,
                user_id=user_id,
                session_id=session_id,
            )

            if result.get("errors"):
                yield MindMapErrorEvent(
                    message=result["errors"][0],
                    code="generation_error",
                )
                return

            # Get mind map tree
            tree_data = result.get("mindmap_tree", {})
            if not tree_data:
                yield MindMapErrorEvent(
                    message="Mind map generation failed - no tree generated",
                    code="no_tree",
                )
                return

            # Convert to response format - generate IDs for nodes
            nodes = self._parse_mindmap_node(tree_data.get("nodes", {}))

            # Map mode string to enum
            try:
                mode_enum = MindMapMode(mode)
            except ValueError:
                mode_enum = MindMapMode.SUMMARIZE

            yield MindMapCompleteEvent(
                tree=MindMapTree(
                    title=tree_data.get("title", "Mind Map"),
                    summary=tree_data.get("summary", ""),
                    source_count=result.get("metadata", {}).get("source_count", 1),
                    mode=mode_enum,
                    nodes=nodes,
                ),
                session_id=session_id,
            )

        except Exception as e:
            logger.error(f"Mind map generation failed: {e}")
            yield MindMapErrorEvent(
                message=str(e),
                code="internal_error",
            )

    async def _run_workflow_async(
        self,
        output_type: str,
        request_data: dict,
        api_key: str,
        gemini_api_key: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        progress_callback: Optional[Callable] = None,
    ) -> tuple[UnifiedWorkflowState, str]:
        """Run the unified workflow asynchronously."""
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
                progress_callback=progress_callback,
            ),
        )

    def _parse_mindmap_node(self, node_data: dict, prefix: str = "node") -> MindMapNode:
        """Parse node data into MindMapNode with generated IDs."""
        node_id = f"{prefix}_{uuid.uuid4().hex[:8]}"
        label = node_data.get("label", "Node")
        children = node_data.get("children", [])

        parsed_children = [
            self._parse_mindmap_node(child, prefix=f"{node_id}")
            for child in children
            if isinstance(child, dict)
        ]

        return MindMapNode(
            id=node_id,
            label=label,
            children=parsed_children if parsed_children else [],
        )


# Singleton instance
_unified_service: Optional[UnifiedGenerationService] = None


def get_unified_service() -> UnifiedGenerationService:
    """Get or create the unified generation service."""
    global _unified_service
    if _unified_service is None:
        _unified_service = UnifiedGenerationService()
    return _unified_service
