"""
FAQ generator.

Writes FAQ document as JSON file.
"""

import re
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger

from ....domain.exceptions import GenerationError
from ....domain.faq_types import FAQDocument, FAQItem, FAQMetadata

# Gradient palette for tags
TAG_GRADIENTS = [
    "blue-cyan",
    "purple-pink",
    "orange-amber",
    "green-teal",
    "rose-red",
    "indigo-violet",
    "yellow-lime",
    "slate-gray",
]


class FAQGenerator:
    """Generate FAQ JSON output from structured content."""

    def generate(self, content: dict, metadata: dict, output_dir: Path) -> Path:
        """
        Generate FAQ JSON from structured content.

        Args:
            content: Structured content with 'faq_data' containing extracted FAQs
            metadata: Document metadata
            output_dir: Output directory

        Returns:
            Path to generated JSON file

        Raises:
            GenerationError: If FAQ generation fails
        """
        try:
            output_dir.mkdir(parents=True, exist_ok=True)

            title = metadata.get("title", "FAQ Document")
            filename = metadata.get("custom_filename", title)
            safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", filename).strip("_")
            if not safe_name:
                safe_name = "faq"
            output_path = output_dir / f"{safe_name}.json"

            # Get FAQ data from content
            faq_data = content.get("faq_data", {})
            if not faq_data:
                raise GenerationError("No FAQ data provided for generation")

            # Build FAQ items with IDs
            items = []
            for i, item in enumerate(faq_data.get("items", [])):
                items.append(FAQItem(
                    id=item.get("id", f"faq-{i+1}"),
                    question=item.get("question", ""),
                    answer=item.get("answer", ""),
                    tags=item.get("tags", []),
                ))

            # Collect unique tags and assign colors
            unique_tags = set()
            for item in items:
                unique_tags.update(item.tags)

            tag_colors = {}
            for i, tag in enumerate(sorted(unique_tags)):
                tag_colors[tag] = TAG_GRADIENTS[i % len(TAG_GRADIENTS)]

            # Build document
            faq_doc = FAQDocument(
                title=faq_data.get("title", title),
                description=faq_data.get("description"),
                items=items,
                metadata=FAQMetadata(
                    source_count=metadata.get("source_count", 0),
                    generated_at=datetime.now(timezone.utc).isoformat(),
                    tag_colors=tag_colors,
                ),
            )

            # Write JSON
            output_path.write_text(
                faq_doc.model_dump_json(indent=2),
                encoding="utf-8",
            )
            logger.info(f"FAQ generated successfully: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"FAQ generation failed: {e}")
            raise GenerationError(f"Failed to generate FAQ: {e}")
