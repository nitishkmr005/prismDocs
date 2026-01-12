"""Cache service for generated documents."""

import hashlib
import json
import shutil
import time
from pathlib import Path
from typing import Optional

from loguru import logger

from ..schemas.requests import GenerateRequest


class CacheService:
    """Content-based cache for generated documents."""

    def __init__(
        self,
        cache_dir: Path = Path("src/output/cache"),
        ttl_seconds: int = 86400,  # 24 hours
    ):
        """Initialize cache service.

        Args:
            cache_dir: Directory for cache metadata
            ttl_seconds: Time-to-live for cache entries
        Invoked by: (no references found)
        """
        self.cache_dir = Path(cache_dir)
        self.ttl_seconds = ttl_seconds
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def generate_cache_key(self, request: GenerateRequest) -> str:
        """Generate cache key from request.

        The key is a SHA256 hash of the normalized request content.

        Args:
            request: Generate request

        Returns:
            64-character hex string cache key
        Invoked by: src/doc_generator/infrastructure/api/services/cache.py, tests/api/test_cache_service.py
        """
        # Build canonical representation
        canonical = {
            "output_format": request.output_format.value,
            "sources": self._normalize_sources(request.sources),
            "provider": request.provider.value,
            "model": request.model,
            "image_model": request.image_model,
            "preferences": {
                "audience": request.preferences.audience.value,
                "image_style": request.preferences.image_style.value,
                "temperature": request.preferences.temperature,
                "max_tokens": request.preferences.max_tokens,
                "max_slides": request.preferences.max_slides,
                "max_summary_points": request.preferences.max_summary_points,
                "image_alignment_retries": request.preferences.image_alignment_retries,
            },
        }

        # Generate hash
        canonical_json = json.dumps(canonical, sort_keys=True)
        return hashlib.sha256(canonical_json.encode()).hexdigest()

    def _normalize_sources(self, sources: list) -> list:
        """
        Normalize sources for hashing.
        Invoked by: src/doc_generator/infrastructure/api/services/cache.py
        """
        return [self._normalize_source(s) for s in sources]

    def _normalize_source(self, source) -> dict:
        """
        Normalize a single source for hashing.
        Invoked by: src/doc_generator/infrastructure/api/services/cache.py
        """
        if source.type == "text":
            return {"type": "text", "content": source.content}
        elif source.type == "url":
            return {"type": "url", "url": source.url}
        elif source.type == "file":
            return {"type": "file", "file_id": source.file_id}
        return {}

    def get(self, request: GenerateRequest) -> Optional[dict]:
        """Get cached result for request.

        Args:
            request: Generate request

        Returns:
            Cache entry dict or None if not found/expired
        Invoked by: .claude/skills/pdf/scripts/check_bounding_boxes.py, .claude/skills/pdf/scripts/extract_form_field_info.py, .claude/skills/pdf/scripts/fill_fillable_fields.py, .claude/skills/pdf/scripts/fill_pdf_form_with_annotations.py, .claude/skills/pptx/ooxml/scripts/validation/base.py, .claude/skills/pptx/ooxml/scripts/validation/pptx.py, .claude/skills/pptx/ooxml/scripts/validation/redlining.py, .claude/skills/pptx/scripts/inventory.py, .claude/skills/pptx/scripts/rearrange.py, .claude/skills/pptx/scripts/replace.py, .claude/skills/pptx/scripts/thumbnail.py, .claude/skills/skill-creator/scripts/quick_validate.py, scripts/generate_from_folder.py, scripts/generate_pdf_from_cache.py, scripts/quick_pdf_with_images.py, scripts/run_generator.py, src/doc_generator/application/graph_workflow.py, src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/nodes/generate_output.py, src/doc_generator/application/nodes/parse_content.py, src/doc_generator/application/nodes/transform_content.py, src/doc_generator/application/nodes/validate_output.py, src/doc_generator/application/parsers/markdown_parser.py, src/doc_generator/application/parsers/unified_parser.py, src/doc_generator/application/workflow/graph.py, src/doc_generator/application/workflow/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/generate_output.py, src/doc_generator/application/workflow/nodes/parse_content.py, src/doc_generator/application/workflow/nodes/transform_content.py, src/doc_generator/application/workflow/nodes/validate_output.py, src/doc_generator/infrastructure/api/routes/cache.py, src/doc_generator/infrastructure/api/routes/download.py, src/doc_generator/infrastructure/api/routes/generate.py, src/doc_generator/infrastructure/api/routes/health.py, src/doc_generator/infrastructure/api/services/generation.py, src/doc_generator/infrastructure/image/claude_svg.py, src/doc_generator/infrastructure/image/svg.py, src/doc_generator/infrastructure/image/validator.py, src/doc_generator/infrastructure/llm/content_generator.py, src/doc_generator/infrastructure/llm/service.py, src/doc_generator/infrastructure/parsers/docling.py, src/doc_generator/infrastructure/storage/file_storage.py, src/doc_generator/utils/content_merger.py, tests/api/test_cache_service.py, tests/api/test_generate_route.py, tests/api/test_health_route.py
        """
        key = self.generate_cache_key(request)
        cache_file = self.cache_dir / f"{key}.json"

        if not cache_file.exists():
            return None

        try:
            data = json.loads(cache_file.read_text())

            # Check if expired
            if time.time() - data["created_at"] > self.ttl_seconds:
                cache_file.unlink()
                return None

            return data
        except (json.JSONDecodeError, KeyError):
            return None

    def set(
        self,
        request: GenerateRequest,
        output_path: Path,
        metadata: dict,
        file_path: Optional[str] = None,
    ) -> str:
        """Store cache entry.

        Args:
            request: Generate request
            output_path: Path to generated output
            metadata: Generation metadata

        Returns:
            Cache key
        Invoked by: .claude/skills/pdf/scripts/extract_form_field_info.py, .claude/skills/pptx/ooxml/scripts/validation/base.py, .claude/skills/pptx/ooxml/scripts/validation/pptx.py, .claude/skills/pptx/scripts/rearrange.py, .claude/skills/pptx/scripts/replace.py, .claude/skills/skill-creator/scripts/quick_validate.py, src/doc_generator/application/graph_workflow.py, src/doc_generator/application/workflow/graph.py, src/doc_generator/infrastructure/api/routes/generate.py, src/doc_generator/infrastructure/image/gemini.py, src/doc_generator/infrastructure/image/svg.py, src/doc_generator/infrastructure/llm/content_generator.py, src/doc_generator/infrastructure/llm/service.py, src/doc_generator/utils/content_merger.py, tests/api/test_cache_service.py
        """
        key = self.generate_cache_key(request)
        cache_file = self.cache_dir / f"{key}.json"

        if file_path is None:
            file_path = str(output_path)

        data = {
            "key": key,
            "output_path": str(output_path),
            "file_path": file_path,
            "metadata": metadata,
            "created_at": time.time(),
        }

        cache_file.write_text(json.dumps(data))
        return key

    def invalidate(self, request: GenerateRequest) -> bool:
        """Invalidate cache entry.

        Args:
            request: Generate request

        Returns:
            True if entry was removed, False if not found
        Invoked by: (no references found)
        """
        key = self.generate_cache_key(request)
        cache_file = self.cache_dir / f"{key}.json"

        if cache_file.exists():
            cache_file.unlink()
            return True
        return False

    def clear_all(self) -> dict:
        """Clear all cache entries.

        Returns:
            Dict with count of cleared items
        Invoked by: (no references found)
        """
        cache_files = list(self.cache_dir.glob("*.json"))
        count = len(cache_files)

        for f in cache_files:
            try:
                f.unlink()
            except OSError:
                pass

        logger.info(f"Cleared {count} cache entries")
        return {"cleared_cache_entries": count}

    def get_stats(self) -> dict:
        """Get cache statistics.

        Returns:
            Dict with cache stats
        Invoked by: (no references found)
        """
        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files if f.exists())

        return {
            "cache_entries": len(cache_files),
            "cache_size_bytes": total_size,
            "cache_dir": str(self.cache_dir),
        }
