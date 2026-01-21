"""Mind map generation service with progress streaming.

Refactored version that uses common utilities for:
- API key configuration
- Content extraction
- JSON parsing
- Singleton management
"""

import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import AsyncIterator

from loguru import logger

from .....domain.prompts.mindmap import mindmap_system_prompt, mindmap_user_prompt
from .....infrastructure.llm import LLMService
from ..schemas.mindmap import (
    MindMapCompleteEvent,
    MindMapErrorEvent,
    MindMapMode,
    MindMapNode,
    MindMapProgressEvent,
    MindMapRequest,
    MindMapTree,
)
from .common import (
    BaseContentExtractor,
    configure_api_key,
    safe_json_parse,
)
from .storage import StorageService


# Model fallback configuration
GEMINI_FALLBACK_MODELS: list[str] = [
    "gemini-3-pro-preview",
    "gemini-3-flash-preview",
    "gemini-2.5-pro",
    "gemini-2.5-flash",
]


class MindMapContentExtractor(BaseContentExtractor):
    """Content extractor specialized for mind map generation."""

    MAX_CONTENT_CHARS: int = 50000


class MindMapService:
    """Orchestrates mind map generation with progress streaming.

    This refactored version delegates common functionality to shared utilities,
    improving maintainability and reducing code duplication.
    """

    def __init__(self, storage_service: StorageService | None = None):
        """Initialize mind map service.

        Args:
            storage_service: Storage service for file operations
        """
        self._executor = ThreadPoolExecutor(max_workers=2)
        self.storage = storage_service or StorageService()
        self._content_extractor = MindMapContentExtractor(
            storage_service=self.storage,
            executor=self._executor,
        )

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
        try:
            # Phase 1: Extracting content
            yield MindMapProgressEvent(
                stage="extracting",
                percent=10,
                message="Reading sources...",
            )

            provider_name = self._normalize_provider(request.provider.value)
            content, source_count = await self._content_extractor.extract_content(
                sources=request.sources,
                provider=provider_name,
                model=request.model,
                api_key=api_key,
            )

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
            configure_api_key(provider_name, api_key)

            # Build list of models to try
            models_to_try = self._build_model_list(request.model, provider_name)

            # Try models with fallback
            tree = await self._generate_with_fallback(
                models=models_to_try,
                provider=provider_name,
                content=content,
                mode=request.mode,
                source_count=source_count,
            )

            yield MindMapProgressEvent(
                stage="complete",
                percent=100,
                message="Mind map generated successfully!",
            )

            yield MindMapCompleteEvent(tree=tree)

        except Exception as e:
            logger.error(f"Mind map generation failed: {e}")
            yield MindMapErrorEvent(
                message=str(e),
                code="GENERATION_ERROR",
            )

    async def _generate_with_fallback(
        self,
        models: list[str],
        provider: str,
        content: str,
        mode: MindMapMode,
        source_count: int,
    ) -> MindMapTree:
        """Try generating mind map with multiple models.

        Args:
            models: List of models to try in order
            provider: LLM provider name
            content: Extracted content
            mode: Mind map generation mode
            source_count: Number of sources

        Returns:
            Generated MindMapTree

        Raises:
            ValueError: If all models fail
        """
        last_error: Exception | None = None

        for attempt, model in enumerate(models):
            try:
                llm_service = LLMService(provider=provider, model=model)

                if not llm_service.is_available():
                    logger.warning(f"Model {model} not available, trying next...")
                    continue

                logger.info(f"Attempting mind map generation with model: {model}")

                # Generate mind map JSON
                mind_map_json = await self._call_llm(
                    llm_service=llm_service,
                    content=content,
                    mode=mode.value,
                    source_count=source_count,
                )

                # Parse and validate response
                tree = self._parse_response(mind_map_json, mode, source_count)

                logger.info(f"Mind map generated successfully with model: {model}")
                return tree

            except (ValueError,) as e:
                last_error = e
                if attempt < len(models) - 1:
                    logger.warning(
                        f"JSON parsing failed with {model}: {e}. Retrying..."
                    )
                else:
                    logger.error(f"JSON parsing failed with all models: {e}")
            except Exception as e:
                # Non-JSON errors should not trigger model fallback
                raise e

        raise ValueError(
            f"Failed to generate valid mind map after trying {len(models)} models. "
            f"Last error: {last_error}"
        )

    async def _call_llm(
        self,
        llm_service: LLMService,
        content: str,
        mode: str,
        source_count: int,
    ) -> str:
        """Call LLM to generate mind map JSON.

        Args:
            llm_service: Configured LLM service
            content: Content to analyze
            mode: Generation mode (summarize, etc.)
            source_count: Number of content sources

        Returns:
            Raw JSON string from LLM
        """
        loop = asyncio.get_event_loop()

        system_prompt = mindmap_system_prompt(mode)
        user_prompt = mindmap_user_prompt(content, source_count)

        result = await loop.run_in_executor(
            self._executor,
            llm_service._call_llm,
            system_prompt,
            user_prompt,
            8000,  # max_tokens
            0.4,  # temperature - lower for structured output
            True,  # json_mode
            "mindmap_generation",
        )

        return result

    def _parse_response(
        self,
        response: str,
        mode: MindMapMode,
        source_count: int,
    ) -> MindMapTree:
        """Parse LLM response into MindMapTree structure.

        Args:
            response: Raw response from LLM
            mode: Generation mode
            source_count: Number of sources

        Returns:
            Validated MindMapTree

        Raises:
            ValueError: If response cannot be parsed as valid JSON
        """
        data = safe_json_parse(response)

        if data is None:
            raise ValueError("Failed to parse mind map JSON response")

        # Extract and validate fields
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
        """Recursively parse node data into MindMapNode.

        Args:
            node_data: Raw node dictionary from JSON

        Returns:
            Validated MindMapNode
        """
        children = [
            self._parse_node(child_data) for child_data in node_data.get("children", [])
        ]

        return MindMapNode(
            id=str(node_data.get("id", uuid.uuid4().hex[:8])),
            label=str(node_data.get("label", ""))[:100],  # Limit label length
            children=children,
        )

    def _build_model_list(self, current_model: str, provider: str) -> list[str]:
        """Build ordered list of models to try.

        Args:
            current_model: The initially requested model
            provider: LLM provider name

        Returns:
            List of model names, current model first
        """
        models = [current_model]

        if provider == "gemini":
            for fallback in GEMINI_FALLBACK_MODELS:
                if fallback != current_model and fallback not in models:
                    models.append(fallback)

        return models

    @staticmethod
    def _normalize_provider(provider: str) -> str:
        """Normalize provider name.

        Args:
            provider: Raw provider name

        Returns:
            Normalized provider name
        """
        if provider.lower() == "google":
            return "gemini"
        return provider.lower()


# Singleton instance management
_mindmap_service: MindMapService | None = None


def get_mindmap_service() -> MindMapService:
    """Get or create mind map service instance.

    Returns:
        Singleton MindMapService instance
    """
    global _mindmap_service
    if _mindmap_service is None:
        _mindmap_service = MindMapService()
    return _mindmap_service
