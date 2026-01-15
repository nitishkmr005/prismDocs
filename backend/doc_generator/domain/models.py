"""
Domain models for document generator.

Defines Pydantic models for workflow state, configuration, and content structures.
"""

from pathlib import Path
from typing import TypedDict

from pydantic import BaseModel, Field

from .content_types import ImageType, OutputFormat


class WorkflowState(TypedDict, total=False):
    """
    State object passed between nodes in the LangGraph workflow.

    Attributes:
        input_path: Path to input file or URL
        input_format: Detected input format
        output_format: Target output format
        raw_content: Extracted raw content
        structured_content: Parsed and structured content
        output_path: Path to generated file
        errors: List of errors encountered
        metadata: Additional metadata (title, author, etc.)
        llm_service: Optional LLM service for content enhancement
    """

    input_path: str
    input_format: str
    output_format: str
    raw_content: str
    structured_content: dict
    output_path: str
    errors: list[str]
    metadata: dict
    llm_service: object


class GeneratorConfig(BaseModel):
    """
    Configuration for document generator.

    Attributes:
        input_dir: Directory containing input files
        output_dir: Directory for generated files
        default_output_format: Default output format
        max_retries: Maximum generation retries
    """

    input_dir: Path = Field(default=Path("data/input"))
    output_dir: Path = Field(default=Path("data/output"))
    default_output_format: OutputFormat = Field(default=OutputFormat.PDF)
    max_retries: int = Field(default=3, ge=1, le=5)

    class Config:
        frozen = True


class ContentSection(BaseModel):
    """
    Represents a section of structured content.

    Attributes:
        type: Section type (heading, paragraph, code, image, etc.)
        text: Text content
        metadata: Additional metadata for the section
    """

    type: str
    text: str
    metadata: dict = Field(default_factory=dict)


class ImageDecision(BaseModel):
    """
    Decision from auto-detection about what image type to generate.

    Attributes:
        image_type: The type of image to generate
        prompt: Description/prompt for image generation
        section_title: Title of the section this image is for
        confidence: Confidence score (0-1) for the decision
    """

    image_type: ImageType
    prompt: str
    section_title: str = ""
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)


class SectionImage(BaseModel):
    """
    Represents a generated image for a section.

    Attributes:
        path: Path to the image file
        image_type: Type of image that was generated
        section_id: ID/index of the section
        embed_base64: Base64 encoded image data for PDF embedding
    """

    path: str
    image_type: ImageType
    section_id: int
    embed_base64: str = ""
