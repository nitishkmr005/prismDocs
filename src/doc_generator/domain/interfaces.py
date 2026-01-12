"""
Protocol interfaces for parsers and generators.

Defines abstract interfaces that implementations must follow.
"""

from pathlib import Path
from typing import Protocol, Tuple


class ContentParser(Protocol):
    """
    Protocol for content parsers.

    All parsers must implement the parse() method to extract content
    and metadata from input sources.
    """

    def parse(self, input_path: str | Path) -> Tuple[str, dict]:
        """
        Parse input and extract content.

        Args:
            input_path: Path to input file or URL

        Returns:
            Tuple of (content_text, metadata_dict)

        Raises:
            ParseError: If parsing fails
        Invoked by: .claude/skills/pptx/ooxml/scripts/pack.py, .claude/skills/pptx/ooxml/scripts/validation/base.py, .claude/skills/pptx/ooxml/scripts/validation/docx.py, .claude/skills/pptx/ooxml/scripts/validation/pptx.py, .claude/skills/pptx/ooxml/scripts/validation/redlining.py, scripts/generate_from_folder.py, src/doc_generator/application/nodes/parse_content.py, src/doc_generator/application/workflow/nodes/parse_content.py, src/doc_generator/infrastructure/api/services/generation.py
        """
        ...


class OutputGenerator(Protocol):
    """
    Protocol for output generators.

    All generators must implement the generate() method to create
    output documents from structured content.
    """

    def generate(self, content: dict, metadata: dict, output_dir: Path) -> Path:
        """
        Generate output document from structured content.

        Args:
            content: Structured content dictionary
            metadata: Document metadata
            output_dir: Output directory for generated file

        Returns:
            Path to generated document

        Raises:
            GenerationError: If generation fails
        Invoked by: scripts/generate_from_folder.py, src/doc_generator/application/nodes/generate_output.py, src/doc_generator/application/workflow/nodes/generate_output.py, src/doc_generator/infrastructure/api/routes/generate.py, tests/api/test_generation_service.py
        """
        ...
