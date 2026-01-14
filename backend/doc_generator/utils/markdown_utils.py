"""
Shared markdown utilities for document generator.

Contains common markdown processing functions used across parsers and generators.
"""

import re


def strip_frontmatter(text: str) -> str:
    """
    Remove YAML frontmatter from markdown text.

    Frontmatter is content between --- delimiters at the start of a file.

    Args:
        text: Markdown text potentially containing frontmatter

    Returns:
        Text with frontmatter removed
    Invoked by: src/doc_generator/application/parsers/markdown_parser.py
    """
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            return parts[2].lstrip()
    return text


def extract_frontmatter(text: str) -> dict:
    """
    Extract YAML frontmatter metadata from markdown text.

    Args:
        text: Markdown text potentially containing frontmatter

    Returns:
        Dictionary of metadata from frontmatter
    Invoked by: src/doc_generator/application/parsers/markdown_parser.py
    """
    metadata = {}

    # Check for frontmatter
    frontmatter_match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)

    if frontmatter_match:
        fm_text = frontmatter_match.group(1)

        # Simple YAML parsing (title, author, date)
        title_match = re.search(r"title:\s*(.+)", fm_text)
        if title_match:
            metadata["title"] = title_match.group(1).strip('"\'')

        author_match = re.search(r"author:\s*(.+)", fm_text)
        if author_match:
            metadata["author"] = author_match.group(1).strip('"\'')

        date_match = re.search(r"date:\s*(.+)", fm_text)
        if date_match:
            metadata["date"] = date_match.group(1).strip('"\'')

    return metadata
