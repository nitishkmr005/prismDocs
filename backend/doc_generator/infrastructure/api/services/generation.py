"""Generation service for document creation with progress streaming."""

import asyncio
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import AsyncIterator, Optional

from loguru import logger

from ....application.graph_workflow import run_workflow
from ....application.parsers import get_parser
from ....domain.content_types import ContentFormat
from ....infrastructure.llm import LLMService
from ....infrastructure.logging_config import (
    log_phase,
    log_separator,
    log_stats,
    log_success,
)
from ....infrastructure.settings import get_settings
from ..schemas.requests import (
    FileSource,
    GenerateRequest,
    TextSource,
    UrlSource,
)
from ..schemas.responses import (
    CompleteEvent,
    CompletionMetadata,
    ErrorEvent,
    GenerationStatus,
    ProgressEvent,
)
from .storage import StorageService


class GenerationService:
    """Orchestrates document generation with progress streaming."""

    def __init__(
        self,
        storage_service: Optional[StorageService] = None,
    ):
        """Initialize generation service.

        Args:
            storage_service: Storage service for file operations
        Invoked by: (no references found)
        """
        self.storage = storage_service or StorageService()
        self._executor = ThreadPoolExecutor(max_workers=2)

    async def generate(
        self,
        request: GenerateRequest,
        api_key: str,
        image_api_key: str | None = None,
    ) -> AsyncIterator[ProgressEvent | CompleteEvent | ErrorEvent]:
        """Generate document with progress streaming.

        Args:
            request: Generation request
            api_key: API key for LLM provider
            image_api_key: API key for image generation (falls back to api_key)

        Yields:
            Progress events, then completion or error event
        Invoked by: scripts/generate_from_folder.py, src/doc_generator/application/nodes/generate_output.py, src/doc_generator/application/workflow/nodes/generate_output.py, src/doc_generator/infrastructure/api/routes/generate.py, tests/api/test_generation_service.py
        """
        import time

        start_time = time.time()

        try:
            # Log start
            log_separator(
                f"Document Generation: {request.output_format.value.upper()}", "═", 60
            )

            # Phase 1: Parse sources
            log_phase(1, 5, "Parsing Sources")
            yield ProgressEvent(
                status=GenerationStatus.PARSING,
                progress=5,
                message="Preparing sources...",
            )

            input_path, file_id = await self._collect_sources(request)
            source_count = len(request.sources)

            log_success(f"Parsed {source_count} source(s) → {input_path.name}")
            yield ProgressEvent(
                status=GenerationStatus.PARSING,
                progress=15,
                message=f"Parsed {source_count} sources",
            )

            # Phase 2: Configure LLM
            log_phase(2, 5, "Configuring LLM")
            yield ProgressEvent(
                status=GenerationStatus.TRANSFORMING,
                progress=20,
                message="Configuring LLM...",
            )

            # Set API key for the provider
            provider_name = request.provider.value
            if provider_name == "google":
                provider_name = "gemini"
            self._configure_api_key(provider_name, api_key)

            # Create LLM service with the configured provider
            llm_service = LLMService(
                provider=provider_name,
                model=request.model,
                max_summary_points=request.preferences.max_summary_points,
                max_slides=request.preferences.max_slides,
                max_tokens_summary=request.preferences.max_tokens,
                max_tokens_slides=request.preferences.max_tokens,
                temperature_summary=request.preferences.temperature,
                temperature_slides=request.preferences.temperature,
            )

            log_success(f"LLM configured: {provider_name}/{request.model}")
            yield ProgressEvent(
                status=GenerationStatus.TRANSFORMING,
                progress=25,
                message="LLM configured",
            )

            # Phase 3: Run the actual workflow
            log_phase(3, 5, "Running Generation Workflow")

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
                event = ProgressEvent(status=status, progress=progress, message=message)
                loop.call_soon_threadsafe(progress_queue.put_nowait, event)

            # Run workflow in thread pool to not block event loop
            workflow_future = loop.run_in_executor(
                self._executor,
                lambda: run_workflow(
                    input_path=str(input_path),
                    output_format=request.output_format.value,
                    llm_service=llm_service,
                    metadata={
                        "provider": request.provider.value,
                        "model": request.model,
                        "image_model": request.image_model,
                        "image_style": request.preferences.image_style.value,
                        "max_tokens": request.preferences.max_tokens,
                        "file_id": file_id,
                        "enable_image_generation": request.preferences.enable_image_generation,
                        "api_keys": {
                            "content": api_key,
                            "image": image_api_key or api_key,
                        },
                    },
                    progress_callback=workflow_progress,
                ),
            )

            while True:
                if workflow_future.done() and progress_queue.empty():
                    break
                try:
                    event = await asyncio.wait_for(progress_queue.get(), timeout=0.2)
                    yield event
                except asyncio.TimeoutError:
                    continue

            result = await workflow_future

            output_path = result.get("output_path", "")
            log_success(
                f"Workflow complete → {Path(output_path).name if output_path else 'N/A'}"
            )

            # Phase 4: Check for errors
            errors = result.get("errors", [])
            if errors:
                logger.error(f"Workflow errors: {errors}")
                yield ErrorEvent(
                    error="; ".join(errors),
                    code="WORKFLOW_ERROR",
                )
                return

            # Phase 5: Finalize
            log_phase(5, 5, "Finalizing")
            yield ProgressEvent(
                status=GenerationStatus.UPLOADING,
                progress=95,
                message="Finalizing...",
            )

            if output_path and Path(output_path).exists():
                # StorageService.get_download_url: build a download link for the output.
                download_url = self.storage.get_download_url(Path(output_path))
            else:
                logger.warning(f"Output path not found: {output_path}")
                download_url = f"/api/download/{Path(output_path).name if output_path else 'error.pdf'}"
            file_path = ""
            if output_path:
                output_path_obj = Path(output_path)
                try:
                    file_path = str(
                        output_path_obj.relative_to(self.storage.base_output_dir)
                    )
                except ValueError:
                    file_path = output_path_obj.name
            else:
                file_path = "error.pdf"

            # Extract metadata from result
            structured_content = result.get("structured_content", {})
            metadata = result.get("metadata", {})

            # Count pages/slides from structured content
            pages = 0
            slides = 0
            if request.output_format.value == "pdf":
                sections = structured_content.get("sections", [])
                pages = max(1, len(sections))
            else:
                slides = len(structured_content.get("sections", []))

            images_generated = len(structured_content.get("section_images", {}))
            title = structured_content.get(
                "title", metadata.get("title", "Generated Document")
            )

            # Calculate duration
            duration = time.time() - start_time
            duration_str = (
                f"{duration:.1f}s"
                if duration < 60
                else f"{int(duration//60)}m {duration%60:.1f}s"
            )

            # Log final stats
            log_stats(
                {
                    "Title": title[:30] + "..." if len(title) > 30 else title,
                    "Format": request.output_format.value.upper(),
                    "Pages": pages if pages else slides,
                    "Images": images_generated,
                    "Duration": duration_str,
                },
                "✅ Generation Complete",
            )

            # Complete
            yield CompleteEvent(
                download_url=download_url,
                file_path=file_path,
                expires_in=3600,
                metadata=CompletionMetadata(
                    title=title,
                    pages=pages,
                    slides=slides,
                    images_generated=images_generated,
                ),
            )

        except Exception as e:
            logger.exception(f"Generation failed: {e}")
            yield ErrorEvent(
                error=str(e),
                code="GENERATION_ERROR",
            )

    def _configure_api_key(self, provider: str, api_key: str) -> None:
        """Configure API key for the provider.

        Args:
            provider: Provider name (google, openai, anthropic)
            api_key: API key value
        Invoked by: src/doc_generator/infrastructure/api/services/generation.py
        """
        key_map = {
            "google": "GOOGLE_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
        }
        env_var = key_map.get(provider)
        if env_var:
            os.environ[env_var] = api_key
            logger.debug(f"Configured {env_var} for provider {provider}")

    async def _collect_sources(
        self, request: GenerateRequest
    ) -> tuple[Path, str | None]:
        """Collect content from all sources and return input path.

        Converts every source to markdown, then merges into a single input file.

        Args:
            request: Generation request

        Returns:
            Path to input file for workflow
        Invoked by: src/doc_generator/infrastructure/api/services/generation.py
        """
        all_sources = request.sources
        parsed_blocks = []
        file_id: str | None = None

        for source in all_sources:
            if isinstance(source, FileSource):
                file_path = self._resolve_upload_path(source.file_id)
                if not file_id:
                    file_id = source.file_id
                parser = get_parser(self._detect_format(file_path))
                content, metadata = parser.parse(file_path)
                title = metadata.get("title") or Path(file_path).name
                parsed_blocks.append(
                    {
                        "title": title,
                        "content": content,
                        "source": str(file_path),
                    }
                )
            elif isinstance(source, UrlSource):
                parser = get_parser(ContentFormat.URL.value)
                content, metadata = parser.parse(source.url)
                title = metadata.get("title") or source.url
                parsed_blocks.append(
                    {
                        "title": title,
                        "content": content,
                        "source": source.url,
                    }
                )
            elif isinstance(source, TextSource):
                parsed_blocks.append(
                    {
                        "title": "Copied Text",
                        "content": source.content,
                        "source": "text",
                    }
                )

        if not parsed_blocks:
            raise ValueError("No valid sources provided")

        combined = self._merge_markdown_sources(parsed_blocks)
        settings = get_settings()
        temp_dir = settings.generator.temp_dir
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_path = temp_dir / f"temp_input_{uuid.uuid4().hex}.md"
        temp_path.write_text(combined, encoding="utf-8")
        logger.info(f"Created temp input file: {temp_path}")
        return temp_path, file_id

    def _resolve_upload_path(self, file_id: str) -> Path:
        """
        Resolve file_id to a path in storage.
        Invoked by: src/doc_generator/infrastructure/api/services/generation.py
        """
        try:
            # StorageService.get_upload_path: resolve file_id to a stored source path.
            file_path = self.storage.get_upload_path(file_id)
            logger.info(f"Using uploaded file: {file_path}")
            return file_path
        except FileNotFoundError:
            pattern = f"{file_id}*"
            # StorageService.upload_dir: scan for matching files in storage root.
            matches = list(self.storage.upload_dir.glob(pattern))
            if matches:
                logger.info(f"Found file by pattern: {matches[0]}")
                return matches[0]
            logger.warning(f"File not found: {file_id}")
            raise

    def _detect_format(self, file_path: Path) -> str:
        """
        Detect content format from file extension.
        Invoked by: src/doc_generator/infrastructure/api/services/generation.py
        """
        suffix = file_path.suffix.lower()
        format_map = {
            ".pdf": ContentFormat.PDF.value,
            ".md": ContentFormat.MARKDOWN.value,
            ".markdown": ContentFormat.MARKDOWN.value,
            ".txt": ContentFormat.TEXT.value,
            ".docx": ContentFormat.DOCX.value,
            ".pptx": ContentFormat.PPTX.value,
            ".html": ContentFormat.HTML.value,
        }
        return format_map.get(suffix, ContentFormat.TEXT.value)

    def _merge_markdown_sources(self, parsed_blocks: list[dict]) -> str:
        """
        Merge parsed markdown sources into a single document.
        Invoked by: src/doc_generator/infrastructure/api/services/generation.py
        """
        sections = []
        for block in parsed_blocks:
            title = block.get("title", "Source")
            source = block.get("source", "")
            content = block.get("content", "")
            header = f"## Source: {title}"
            if source and source != "text":
                header += f"\n\nSource: {source}"
            sections.append(f"{header}\n\n{content}")
        return "\n\n---\n\n".join(sections)
