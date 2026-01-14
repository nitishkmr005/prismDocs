"""
Gemini client helpers shared across nodes.
"""

from __future__ import annotations


def get_gemini_api_key() -> str | None:
    """
    Resolve the Gemini API key from environment variables.
    Invoked by: src/doc_generator/application/utils/gemini_client.py
    """
    import os
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def create_gemini_client(api_key: str | None):
    """
    Create a Gemini client if possible.
    Invoked by: src/doc_generator/application/utils/gemini_client.py
    """
    if not api_key:
        return None
    try:
        from google import genai
    except ImportError:
        return None
    return genai.Client(api_key=api_key)
