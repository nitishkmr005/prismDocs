"""Mind map generation service with progress streaming."""

import asyncio
import json
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import AsyncIterator

from loguru import logger

from ....application.parsers import WebParser, get_parser
from ....domain.prompts.mindmap import mindmap_system_prompt, mindmap_user_prompt
from ....infrastructure.llm import LLMService
from ....utils.image_understanding import extract_image_content, is_image_file
from ..schemas.mindmap import (
    MindMapCompleteEvent,
    MindMapErrorEvent,
    MindMapMode,
    MindMapNode,
    MindMapProgressEvent,
    MindMapRequest,
    MindMapTree,
)
from ..schemas.requests import FileSource, TextSource, UrlSource
from .storage import StorageService


class MindMapService:
    """Orchestrates mind map generation with progress streaming."""

    def __init__(self, storage_service: StorageService | None = None):
        """Initialize mind map service."""
        self.storage = storage_service or StorageService()
        self._executor = ThreadPoolExecutor(max_workers=2)

    async def generate(
        self,
        request: MindMapRequest,
        api_key: str,
        user_id: str | None = None,
    ) -> AsyncIterator[MindMapProgressEvent | MindMapCompleteEvent | MindMapErrorEvent]:
        """Generate mind map with progress streaming.

        Args:
            request: Mind map generation request
            api_key: API key for LLM provider
            user_id: Optional user ID for logging

        Yields:
            Progress events, then completion or error event
        """
        # Fallback models for retry when JSON parsing fails (best to fastest)
        GEMINI_FALLBACK_MODELS = [
            "gemini-3-pro-preview",
            "gemini-3-flash-preview",
            "gemini-2.5-pro",
            "gemini-2.5-flash",
        ]

        try:
            # Phase 1: Extracting content
            yield MindMapProgressEvent(
                stage="extracting",
                percent=10,
                message="Reading sources...",
            )

            content, source_count = await self._extract_content(request, api_key)

            yield MindMapProgressEvent(
                stage="extracting",
                percent=30,
                message=f"Extracted content from {source_count} source(s)",
            )

            # Phase 2: Analyzing structure
            yield MindMapProgressEvent(
                stage="analyzing",
                percent=40,
                message="Analyzing content structure...",
            )

            # Configure LLM
            provider_name = request.provider.value
            if provider_name == "google":
                provider_name = "gemini"
            self._configure_api_key(provider_name, api_key)

            # Build list of models to try (current model first, then fallbacks for Gemini)
            models_to_try = [request.model]
            if provider_name == "gemini":
                # Add fallback models that aren't the same as the current model
                for fallback in GEMINI_FALLBACK_MODELS:
                    if fallback != request.model and fallback not in models_to_try:
                        models_to_try.append(fallback)

            tree = None
            last_error = None

            for attempt, model in enumerate(models_to_try):
                try:
                    llm_service = LLMService(
                        provider=provider_name,
                        model=model,
                    )

                    if not llm_service.is_available():
                        logger.warning(f"Model {model} not available, trying next...")
                        continue

                    if attempt == 0:
                        yield MindMapProgressEvent(
                            stage="analyzing",
                            percent=50,
                            message=f"Using {model} to generate...",
                        )
                    else:
                        yield MindMapProgressEvent(
                            stage="generating",
                            percent=55 + (attempt * 10),
                            message=f"Retrying with {model}...",
                        )

                    # Phase 3: Generating mind map
                    yield MindMapProgressEvent(
                        stage="generating",
                        percent=60 + (attempt * 5),
                        message="Generating mind map structure...",
                    )

                    # Call LLM to generate mind map
                    mind_map_json = await self._generate_mindmap(
                        llm_service=llm_service,
                        content=content,
                        mode=request.mode.value,
                        source_count=source_count,
                    )

                    yield MindMapProgressEvent(
                        stage="generating",
                        percent=90,
                        message="Parsing response...",
                    )

                    # Parse and validate the response
                    tree = self._parse_response(
                        mind_map_json, request.mode, source_count
                    )

                    # If we get here, parsing succeeded
                    logger.info(f"Mind map generated successfully with model: {model}")
                    break

                except (json.JSONDecodeError, ValueError) as e:
                    last_error = e
                    if attempt < len(models_to_try) - 1:
                        logger.warning(
                            f"JSON parsing failed with {model}: {e}. Retrying with next model..."
                        )
                    else:
                        logger.error(
                            f"JSON parsing failed with all models. Last error: {e}"
                        )
                except Exception as e:
                    # Non-JSON errors should not trigger model fallback
                    raise e

            if tree is None:
                raise ValueError(
                    f"Failed to generate valid mind map JSON after trying {len(models_to_try)} models. Last error: {last_error}"
                )

            yield MindMapProgressEvent(
                stage="complete",
                percent=100,
                message="Mind map generated successfully!",
            )

            # Return completed mind map
            yield MindMapCompleteEvent(tree=tree)

        except Exception as e:
            logger.error(f"Mind map generation failed: {e}")
            yield MindMapErrorEvent(
                message=str(e),
                code="GENERATION_ERROR",
            )

    async def _extract_content(
        self, request: MindMapRequest, api_key: str
    ) -> tuple[str, int]:
        """Extract and merge content from all sources.

        Returns:
            Tuple of (merged content, source count)
        """
        contents: list[str] = []
        loop = asyncio.get_event_loop()

        provider_name = request.provider.value
        if provider_name == "google":
            provider_name = "gemini"

        for source in request.sources:
            if isinstance(source, FileSource):
                # Get file from storage
                file_path = self.storage.get_upload_path(source.file_id)
                if file_path.exists():
                    # Determine content format from file extension
                    if file_path.suffix.lower() in {".xlsx", ".xls"}:
                        raise ValueError("Excel files are not supported.")
                    if is_image_file(file_path):
                        content, _ = await loop.run_in_executor(
                            self._executor,
                            extract_image_content,
                            file_path,
                            provider_name,
                            request.model,
                            api_key,
                        )
                    else:
                        file_extension = file_path.suffix.lstrip(".").lower()
                        parser = get_parser(file_extension)
                        content, _ = await loop.run_in_executor(
                            self._executor, parser.parse, file_path
                        )
                    contents.append(content)
                else:
                    logger.warning(f"File not found: {source.file_id}")

            elif isinstance(source, UrlSource):
                # Parse URL content
                parser = WebParser()
                content, _ = await loop.run_in_executor(
                    self._executor, parser.parse, source.url
                )
                contents.append(content)

            elif isinstance(source, TextSource):
                contents.append(source.content)

        merged_content = "\n\n---\n\n".join(contents)

        # Truncate if too long (to avoid exceeding token limits)
        max_chars = 50000
        if len(merged_content) > max_chars:
            merged_content = merged_content[:max_chars] + "\n\n[Content truncated...]"
            logger.warning(f"Content truncated to {max_chars} characters")

        return merged_content, len(contents)

    def _configure_api_key(self, provider: str, api_key: str) -> None:
        """Configure API key in environment for the provider."""
        if provider == "gemini":
            os.environ["GEMINI_API_KEY"] = api_key
            os.environ["GOOGLE_API_KEY"] = api_key
        elif provider == "openai":
            os.environ["OPENAI_API_KEY"] = api_key
        elif provider == "anthropic":
            os.environ["ANTHROPIC_API_KEY"] = api_key

    async def _generate_mindmap(
        self,
        llm_service: LLMService,
        content: str,
        mode: str,
        source_count: int,
    ) -> str:
        """Call LLM to generate mind map JSON."""
        loop = asyncio.get_event_loop()

        system_prompt = mindmap_system_prompt(mode)
        user_prompt = mindmap_user_prompt(content, source_count)

        result = await loop.run_in_executor(
            self._executor,
            llm_service._call_llm,
            system_prompt,
            user_prompt,
            8000,  # max_tokens
            0.4,  # temperature
            True,  # json_mode
            "mindmap_generation",  # step
        )

        return result

    def _parse_response(
        self,
        response: str,
        mode: MindMapMode,
        source_count: int,
    ) -> MindMapTree:
        """Parse LLM response into MindMapTree structure."""
        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            data = self._extract_json(response)

        if data is None:
            raise ValueError("Failed to parse mind map JSON response")

        # Extract fields
        title = data.get("title", "Mind Map")
        summary = data.get("summary", "")
        nodes_data = data.get("nodes", {})

        # Parse nodes recursively
        nodes = self._parse_node(nodes_data)

        return MindMapTree(
            title=title,
            summary=summary,
            source_count=source_count,
            mode=mode,
            nodes=nodes,
        )

    def _parse_node(self, node_data: dict) -> MindMapNode:
        """Recursively parse node data into MindMapNode."""
        children = []
        for child_data in node_data.get("children", []):
            children.append(self._parse_node(child_data))

        return MindMapNode(
            id=str(node_data.get("id", uuid.uuid4().hex[:8])),
            label=str(node_data.get("label", ""))[:100],  # Limit label length
            children=children,
        )

    def _extract_json(self, text: str) -> dict | None:
        """Try to extract JSON object from text."""
        if not text:
            return None

        # Find first { and matching }
        start_idx = None
        for i, ch in enumerate(text):
            if ch == "{":
                start_idx = i
                break

        if start_idx is None:
            return None

        stack = []
        for i in range(start_idx, len(text)):
            ch = text[i]
            if ch == "{":
                stack.append(ch)
            elif ch == "}":
                if stack:
                    stack.pop()
                    if not stack:
                        try:
                            return json.loads(text[start_idx : i + 1])
                        except json.JSONDecodeError:
                            return None

        return None


# Singleton instance
_mindmap_service: MindMapService | None = None


def get_mindmap_service() -> MindMapService:
    """Get or create mind map service instance."""
    global _mindmap_service
    if _mindmap_service is None:
        _mindmap_service = MindMapService()
    return _mindmap_service
