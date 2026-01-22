"""
Unified workflow state for all content generation types.

This state model supports:
- Documents (PDF, Markdown, PPTX slides)
- Podcasts (audio generation)
- Mind Maps (hierarchical visualization)
- Images (generation and editing)
"""

from typing import Any, Literal, TypedDict


# Output type literals
OutputType = Literal[
    "article_pdf",
    "article_markdown",
    "slide_deck_pdf",
    "presentation_pptx",
    "podcast",
    "mindmap",
    "image_generate",
    "image_edit",
]


class UnifiedWorkflowState(TypedDict, total=False):
    """
    Unified state object passed between nodes in the LangGraph workflow.

    This state supports all content generation types while maintaining
    backward compatibility with existing document generation.

    Attributes:
        # --- Request Context ---
        output_type: Target output type (determines workflow branch)
        request_data: Original request data (format depends on output_type)
        api_key: Primary API key for LLM provider
        gemini_api_key: Gemini API key (for TTS/image generation)
        user_id: Optional user identifier for logging

        # --- Common Processing ---
        input_path: Path to input file or URL (for documents)
        input_format: Detected input format
        raw_content: Extracted raw content from sources
        summary_content: Chunked summary of raw content
        structured_content: Parsed and structured content
        enhanced_content: LLM-enhanced content (summaries, topics, etc.)

        # --- Document Generation ---
        output_format: Target document format (pdf, pptx, markdown)
        output_path: Path to generated document file
        images: Generated images for document sections

        # --- Podcast Generation ---
        podcast_script: Generated dialogue script
        podcast_dialogue: Parsed dialogue entries
        podcast_audio_data: Raw PCM audio data
        podcast_audio_base64: Base64-encoded WAV audio

        # --- Mind Map Generation ---
        mindmap_mode: Generation mode (summarize, detailed, hierarchical)
        mindmap_tree: Generated mind map tree structure

        # --- Image Generation ---
        image_prompt: Prompt for image generation
        image_style: Style configuration for image
        image_output_format: raster or svg
        image_data: Generated image data (base64 or SVG)
        image_source: Source image for editing
        image_edit_mode: Type of edit (basic, style_transfer, region)

        # --- Workflow Control ---
        errors: List of errors encountered
        metadata: Additional metadata (title, author, etc.)
        llm_service: LLM service instance
        progress_percent: Current progress percentage (0-100)
        progress_message: Current progress message
        completed: Whether workflow completed successfully
    """

    # --- Request Context ---
    output_type: OutputType
    request_data: dict
    api_key: str
    gemini_api_key: str
    user_id: str

    # --- Common Processing ---
    input_path: str
    input_format: str
    raw_content: str
    summary_content: str
    structured_content: dict
    enhanced_content: dict

    # --- Document Generation ---
    output_format: str
    output_path: str
    images: list[dict]

    # --- Podcast Generation ---
    podcast_script: str
    podcast_dialogue: list[dict]
    podcast_audio_data: bytes
    podcast_audio_base64: str
    podcast_duration_seconds: float
    podcast_title: str
    podcast_description: str

    # --- Mind Map Generation ---
    mindmap_mode: str
    mindmap_tree: dict

    # --- Image Generation ---
    image_prompt: str
    image_style: dict
    image_output_format: str
    image_data: str
    image_source: str
    image_edit_mode: str
    image_prompt_used: str

    # --- Workflow Control ---
    errors: list[str]
    metadata: dict
    llm_service: Any
    progress_percent: float
    progress_message: str
    completed: bool


def get_output_branch(state: UnifiedWorkflowState) -> str:
    """
    Determine which workflow branch to execute based on output_type.

    Args:
        state: Current workflow state

    Returns:
        Branch name: "document", "podcast", "mindmap", "image_generate", "image_edit"
    """
    output_type = state.get("output_type", "")

    if output_type in (
        "article_pdf",
        "article_markdown",
        "slide_deck_pdf",
        "presentation_pptx",
    ):
        return "document"
    elif output_type == "podcast":
        return "podcast"
    elif output_type == "mindmap":
        return "mindmap"
    elif output_type == "image_generate":
        return "image_generate"
    elif output_type == "image_edit":
        return "image_edit"
    else:
        return "document"  # Default fallback


def is_document_type(output_type: str) -> bool:
    """Check if output type is a document."""
    return output_type in (
        "article_pdf",
        "article_markdown",
        "slide_deck_pdf",
        "presentation_pptx",
    )


def requires_content_extraction(output_type: str) -> bool:
    """Check if output type requires content extraction from sources."""
    return output_type in (
        "article_pdf",
        "article_markdown",
        "slide_deck_pdf",
        "presentation_pptx",
        "podcast",
        "mindmap",
    )


def requires_gemini_key(output_type: str) -> bool:
    """Check if output type requires Gemini API key."""
    return output_type in ("podcast", "image_generate", "image_edit")
