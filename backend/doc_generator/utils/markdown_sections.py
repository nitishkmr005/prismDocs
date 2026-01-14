"""
Markdown section parsing helpers.
"""

import re


def extract_section_number(title: str) -> tuple[int | None, str]:
    """
    Extract section number from title if present.

    Args:
        title: Section title (e.g., "1. Introduction" or "Introduction")

    Returns:
        Tuple of (section_number or None, clean_title)
    Invoked by: src/doc_generator/application/utils/markdown_sections.py
    """
    number_pattern = r"^(\d+)[\.:)\s]+\s*(.+)$"
    match = re.match(number_pattern, title)
    if match:
        return int(match.group(1)), match.group(2).strip()
    return None, title


def extract_sections(markdown: str) -> list[dict]:
    """
    Extract sections from markdown content.

    Section IDs are synced with title numbering when present (e.g., "1. Introduction" -> id 1).
    If no number in title, uses sequential numbering starting from 1.

    Args:
        markdown: Full markdown content

    Returns:
        List of section dicts with id, title, content, and position
    Invoked by: src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/generate_images.py
    """
    sections = []
    section_pattern = r"^##\s+(.+?)\s*$"
    matches = list(re.finditer(section_pattern, markdown, re.MULTILINE))
    if not matches:
        section_pattern = r"^#\s+(.+?)\s*$"
        matches = list(re.finditer(section_pattern, markdown, re.MULTILINE))
    if not matches:
        return [{
            "id": 1,
            "title": "Document",
            "content": markdown.strip(),
            "position": 0,
        }]

    next_sequential_id = 1
    for i, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(markdown)
        content = markdown[start:end].strip()

        section_num, _ = extract_section_number(title)
        if section_num is not None:
            section_id = section_num
            next_sequential_id = max(next_sequential_id, section_num + 1)
        else:
            section_id = next_sequential_id
            next_sequential_id += 1

        sections.append({
            "id": section_id,
            "title": title,
            "content": content,
            "position": match.start(),
        })

    return sections
