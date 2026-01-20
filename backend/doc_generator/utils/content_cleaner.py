"""
Content cleaner utility for preprocessing markdown content.

Cleans up web-scraped markdown content by removing HTML comments,
navigation elements, and other artifacts.
"""

import re

from loguru import logger


def clean_markdown_content(content: str) -> str:
    """
    Clean and normalize markdown content.

    Removes:
    - HTML comments (<!-- image -->, <!-- ... -->)
    - Navigation/UI elements (Subscribe, Sign in, Share counters)
    - Orphaned metadata (avatars, timestamps)
    - Empty lines and excessive whitespace

    Args:
        content: Raw markdown content

    Returns:
        Cleaned markdown content
    Invoked by: src/doc_generator/utils/content_cleaner.py
    """
    logger.debug(f"Cleaning markdown content ({len(content)} chars)...")

    # Split into lines for processing
    lines = content.split('\n')
    cleaned_lines = []

    # Patterns to skip
    skip_patterns = [
        r'^Subscribe\s*Sign\s*in$',  # Navigation
        r'^\d+,?\d*\s+\d+\s+\d+\s+Share$',  # Share counters like "1,645 78 149 Share"
        r'^Read full story$',  # Link text
        r"^.*?'s avatar$",  # Avatar references
        r'^·\s*\w+\s+\d+,\s+\d+$',  # Date fragments like "· February 5, 2025"
        r'^\*\*Tip:\*\*.*$',  # UI tips
        r'^\*\*Optional:\*\*.*$',  # Optional notes about videos
        r'^Last updated:.*$',  # Update timestamps
    ]

    in_code_block = False
    previous_line_empty = False

    for line in lines:
        # Track code blocks - don't modify content inside them
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            cleaned_lines.append(line)
            continue

        # Don't process content inside code blocks
        if in_code_block:
            cleaned_lines.append(line)
            continue

        # Remove HTML comments
        line = re.sub(r'<!--.*?-->', '', line).strip()

        # Skip navigation/UI elements
        if any(re.match(pattern, line.strip(), re.IGNORECASE) for pattern in skip_patterns):
            continue

        # Remove empty headings (# with no text)
        if re.match(r'^#+\s*$', line):
            continue

        # Skip lines that are just whitespace
        if not line.strip():
            # Avoid multiple consecutive empty lines
            if not previous_line_empty:
                cleaned_lines.append('')
                previous_line_empty = True
            continue

        previous_line_empty = False

        # Clean up excessive inline whitespace
        line = re.sub(r'\s+', ' ', line).strip()

        # Skip very short orphaned lines (likely artifacts) - but keep headings
        if len(line) <= 2 and not re.match(r'^#+', line):
            continue

        cleaned_lines.append(line)

    # Join lines back
    cleaned = '\n'.join(cleaned_lines)

    # Post-processing cleanups
    cleaned = _post_process_content(cleaned)

    reduction = len(content) - len(cleaned)
    logger.debug(f"Content cleaned: removed {reduction} chars ({reduction * 100 // len(content)}%)")

    return cleaned


def _post_process_content(content: str) -> str:
    """
    Apply post-processing cleanup rules.

    Args:
        content: Pre-cleaned content

    Returns:
        Post-processed content
    Invoked by: src/doc_generator/utils/content_cleaner.py
    """
    # Remove more than 2 consecutive newlines
    content = re.sub(r'\n{3,}', '\n\n', content)

    # Fix spacing around headings (ensure blank line before major headings)
    content = re.sub(r'\n(#{1,2}\s+)', r'\n\n\1', content)

    # Remove trailing whitespace from each line
    lines = [line.rstrip() for line in content.split('\n')]
    content = '\n'.join(lines)

    # Remove leading/trailing empty lines
    content = content.strip()

    return content


def remove_warning_lines(content: str) -> str:
    """
    Remove warning lines from parser output.

    Args:
        content: Markdown content

    Returns:
        Content without warning lines
    Invoked by: src/doc_generator/utils/content_cleaner.py
    """
    lines = content.split('\n')
    cleaned = [
        line for line in lines
        if not line.startswith('WARNING:')
    ]
    return '\n'.join(cleaned)


def clean_content_for_output(content: str) -> str:
    """
    Main entry point for content cleaning before PDF/PPTX generation.

    Args:
        content: Raw markdown content

    Returns:
        Cleaned markdown content ready for document generation
    Invoked by: src/doc_generator/application/nodes/transform_content.py, src/doc_generator/application/workflow/nodes/transform_content.py, src/doc_generator/utils/content_merger.py
    """
    logger.info("Cleaning content for document generation...")

    # Step 1: Remove warning lines
    content = remove_warning_lines(content)

    # Step 2: Clean markdown content (HTML comments, navigation, etc.)
    content = clean_markdown_content(content)

    logger.success("Content cleaning completed")

    return content
