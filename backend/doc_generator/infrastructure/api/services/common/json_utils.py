"""JSON parsing utilities.

This module provides robust JSON extraction from potentially malformed text,
which is useful when parsing LLM responses that may contain markdown or
additional text around JSON content.
"""

import json
from typing import Any


def extract_json_from_text(text: str) -> dict[str, Any] | None:
    """Extract a JSON object from text that may contain additional content.

    This function handles common LLM response patterns where JSON is wrapped
    in markdown code blocks or surrounded by explanatory text.

    The algorithm:
    1. Find the first '{' character
    2. Track nested braces to find the matching '}'
    3. Attempt to parse the extracted substring as JSON

    Args:
        text: Text that may contain a JSON object

    Returns:
        Parsed dictionary if valid JSON found, None otherwise

    Example:
        >>> extract_json_from_text('Here is the result: {"key": "value"} Done!')
        {'key': 'value'}

        >>> extract_json_from_text('```json\\n{"key": "value"}\\n```')
        {'key': 'value'}
    """
    if not text:
        return None

    # Find the first opening brace
    start_idx = text.find("{")
    if start_idx == -1:
        return None

    # Track braces to find matching closing brace
    brace_count = 0
    in_string = False
    escape_next = False

    for i in range(start_idx, len(text)):
        char = text[i]

        if escape_next:
            escape_next = False
            continue

        if char == "\\":
            escape_next = True
            continue

        if char == '"' and not escape_next:
            in_string = not in_string
            continue

        if in_string:
            continue

        if char == "{":
            brace_count += 1
        elif char == "}":
            brace_count -= 1
            if brace_count == 0:
                # Found matching brace, try to parse
                json_str = text[start_idx : i + 1]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    return None

    return None


def clean_markdown_json(text: str) -> str:
    """Remove markdown code block wrappers from JSON text.

    Args:
        text: Text that may have markdown code block wrappers

    Returns:
        Cleaned text with wrappers removed

    Example:
        >>> clean_markdown_json('```json\\n{"key": "value"}\\n```')
        '{"key": "value"}'
    """
    cleaned = text.strip()

    # Remove opening code block markers
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]

    # Remove closing code block markers
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    return cleaned.strip()


def safe_json_parse(text: str) -> dict[str, Any] | None:
    """Safely parse JSON with multiple fallback strategies.

    Tries:
    1. Direct JSON parsing
    2. Clean markdown wrappers and parse
    3. Extract JSON from arbitrary text

    Args:
        text: Text to parse as JSON

    Returns:
        Parsed dictionary or None if all strategies fail
    """
    if not text:
        return None

    # Strategy 1: Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Clean markdown and parse
    try:
        cleaned = clean_markdown_json(text)
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Strategy 3: Extract from arbitrary text
    return extract_json_from_text(text)
