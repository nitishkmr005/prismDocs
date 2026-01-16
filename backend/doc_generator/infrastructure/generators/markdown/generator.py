"""
Markdown generator.

Writes structured markdown content to a .md file.
"""

from pathlib import Path

from loguru import logger

from ....domain.exceptions import GenerationError


class MarkdownGenerator:
    """Generate Markdown output from structured content."""

    def generate(self, content: dict, metadata: dict, output_dir: Path) -> Path:
        """
        Generate Markdown from structured content.

        Args:
            content: Structured content dictionary with 'markdown'
            metadata: Document metadata
            output_dir: Output directory

        Returns:
            Path to generated Markdown file

        Raises:
            GenerationError: If markdown generation fails
        Invoked by: src/doc_generator/application/nodes/generate_output.py, src/doc_generator/application/workflow/nodes/generate_output.py
        """
        try:
            output_dir.mkdir(parents=True, exist_ok=True)

            title = metadata.get("title", "document")
            filename = metadata.get("custom_filename", title)
            safe_name = filename.replace(" ", "_").replace("/", "_")
            output_path = output_dir / f"{safe_name}.md"

            markdown_content = content.get("markdown", content.get("raw_content", ""))
            if not markdown_content:
                raise GenerationError("No content provided for Markdown generation")

            output_path.write_text(markdown_content, encoding="utf-8")
            logger.info(f"Markdown generated successfully: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Markdown generation failed: {e}")
            raise GenerationError(f"Failed to generate Markdown: {e}")
