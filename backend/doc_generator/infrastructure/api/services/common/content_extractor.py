"""Base content extractor for processing multiple source types.

This module provides a reusable base class for extracting content from
FileSource, UrlSource, and TextSource objects. It eliminates the duplicated
`_extract_content` methods in MindMapService, PodcastService, and other services.
"""

import asyncio
from abc import ABC
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import TypeVar

from loguru import logger

from .....application.parsers import WebParser, get_parser
from .....utils.image_understanding import extract_image_content, is_image_file
from ...schemas.requests import FileSource, TextSource, UrlSource
from ..storage import StorageService

# Type variable for request types that have sources, provider, and model
TRequest = TypeVar("TRequest")


class BaseContentExtractor(ABC):
    """Base class for extracting and merging content from multiple sources.

    This class provides the common content extraction logic that was previously
    duplicated across MindMapService, PodcastService, and GenerationService.

    Subclasses should inherit from this and can override specific behaviors
    if needed.
    """

    # Maximum characters before truncation (configurable per subclass)
    MAX_CONTENT_CHARS: int = 50000

    def __init__(
        self,
        storage_service: StorageService | None = None,
        executor: ThreadPoolExecutor | None = None,
    ):
        """Initialize the content extractor.

        Args:
            storage_service: Storage service for file operations
            executor: Thread pool executor for blocking operations
        """
        self.storage = storage_service or StorageService()
        self._executor = executor or ThreadPoolExecutor(max_workers=2)

    async def extract_content(
        self,
        sources: list[FileSource | UrlSource | TextSource],
        provider: str,
        model: str,
        api_key: str,
    ) -> tuple[str, int]:
        """Extract and merge content from all sources.

        Args:
            sources: List of source objects (FileSource, UrlSource, TextSource)
            provider: LLM provider name
            model: Model name for image understanding
            api_key: API key for provider

        Returns:
            Tuple of (merged content string, number of sources processed)

        Raises:
            ValueError: If unsupported file type is encountered
        """
        contents: list[str] = []
        loop = asyncio.get_event_loop()

        # Normalize provider name
        provider_name = provider.lower()
        if provider_name == "google":
            provider_name = "gemini"

        for source in sources:
            content = await self._extract_single_source(
                source=source,
                provider_name=provider_name,
                model=model,
                api_key=api_key,
                loop=loop,
            )
            if content:
                contents.append(content)

        merged_content = self._merge_contents(contents)
        return merged_content, len(contents)

    async def _extract_single_source(
        self,
        source: FileSource | UrlSource | TextSource,
        provider_name: str,
        model: str,
        api_key: str,
        loop: asyncio.AbstractEventLoop,
    ) -> str | None:
        """Extract content from a single source.

        Args:
            source: Source object
            provider_name: Normalized provider name
            model: Model name
            api_key: API key
            loop: Event loop for executor

        Returns:
            Extracted content string or None if extraction failed
        """
        if isinstance(source, FileSource):
            return await self._extract_from_file(
                source, provider_name, model, api_key, loop
            )
        elif isinstance(source, UrlSource):
            return await self._extract_from_url(source, loop)
        elif isinstance(source, TextSource):
            return source.content
        return None

    async def _extract_from_file(
        self,
        source: FileSource,
        provider_name: str,
        model: str,
        api_key: str,
        loop: asyncio.AbstractEventLoop,
    ) -> str | None:
        """Extract content from a file source.

        Args:
            source: File source with file_id
            provider_name: LLM provider name
            model: Model name for image understanding
            api_key: API key
            loop: Event loop

        Returns:
            Extracted content or None

        Raises:
            ValueError: If file type is not supported
        """
        file_path = self.storage.get_upload_path(source.file_id)

        if not file_path.exists():
            logger.warning(f"File not found: {source.file_id}")
            return None

        # Check for unsupported file types
        if file_path.suffix.lower() in {".xlsx", ".xls"}:
            raise ValueError("Excel files are not supported.")

        # Handle image files
        if is_image_file(file_path):
            content, _ = await loop.run_in_executor(
                self._executor,
                extract_image_content,
                file_path,
                provider_name,
                model,
                api_key,
            )
            return content

        # Handle other file types
        file_extension = file_path.suffix.lstrip(".").lower()
        parser = get_parser(file_extension)
        content, _ = await loop.run_in_executor(self._executor, parser.parse, file_path)
        return content

    async def _extract_from_url(
        self,
        source: UrlSource,
        loop: asyncio.AbstractEventLoop,
    ) -> str | None:
        """Extract content from a URL source.

        Args:
            source: URL source
            loop: Event loop

        Returns:
            Extracted content or None
        """
        parser_type = source.parser.value if source.parser else None
        parser = WebParser(parser=parser_type)
        content, _ = await loop.run_in_executor(
            self._executor, parser.parse, source.url
        )
        return content

    def _merge_contents(self, contents: list[str]) -> str:
        """Merge multiple content strings into one.

        Each content block is separated by a horizontal rule.
        Content is truncated if it exceeds MAX_CONTENT_CHARS.

        Args:
            contents: List of content strings

        Returns:
            Merged and possibly truncated content
        """
        merged = "\n\n---\n\n".join(contents)

        if len(merged) > self.MAX_CONTENT_CHARS:
            merged = merged[: self.MAX_CONTENT_CHARS] + "\n\n[Content truncated...]"
            logger.warning(f"Content truncated to {self.MAX_CONTENT_CHARS} characters")

        return merged
