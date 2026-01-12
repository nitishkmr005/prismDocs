"""
Prompt templates for LLM-powered document generation.

Exports prompt templates used by LLM content, image generation, and services.
"""

from .image import (
    CONCEPT_EXTRACTION_PROMPT,
    CONCEPT_EXTRACTION_SYSTEM_PROMPT,
    CONTENT_AWARE_IMAGE_PROMPT,
    IMAGE_DESCRIPTION_PROMPT,
    IMAGE_STYLE_TEMPLATES,
    build_gemini_image_prompt,
    build_image_description_prompt,
    build_prompt_generator_prompt,
)
from .text import (
    build_blog_from_outline_prompt,
    build_chunk_prompt,
    build_generation_prompt,
    build_outline_prompt,
    build_title_prompt,
    enhance_bullets_prompt,
    enhance_bullets_system_prompt,
    executive_summary_prompt,
    executive_summary_system_prompt,
    get_content_system_prompt,
    section_slide_structure_prompt,
    section_slide_structure_system_prompt,
    slide_structure_prompt,
    slide_structure_system_prompt,
    speaker_notes_prompt,
    speaker_notes_system_prompt,
    visualization_suggestions_prompt,
    visualization_suggestions_system_prompt,
)

__all__ = [
    "build_blog_from_outline_prompt",
    "build_chunk_prompt",
    "build_generation_prompt",
    "build_gemini_image_prompt",
    "build_image_description_prompt",
    "build_outline_prompt",
    "build_prompt_generator_prompt",
    "build_title_prompt",
    "CONCEPT_EXTRACTION_PROMPT",
    "CONCEPT_EXTRACTION_SYSTEM_PROMPT",
    "CONTENT_AWARE_IMAGE_PROMPT",
    "IMAGE_DESCRIPTION_PROMPT",
    "IMAGE_STYLE_TEMPLATES",
    "enhance_bullets_prompt",
    "enhance_bullets_system_prompt",
    "executive_summary_prompt",
    "executive_summary_system_prompt",
    "get_content_system_prompt",
    "section_slide_structure_prompt",
    "section_slide_structure_system_prompt",
    "slide_structure_prompt",
    "slide_structure_system_prompt",
    "speaker_notes_prompt",
    "speaker_notes_system_prompt",
    "visualization_suggestions_prompt",
    "visualization_suggestions_system_prompt",
]
