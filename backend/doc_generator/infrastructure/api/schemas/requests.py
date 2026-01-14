"""Pydantic request models for the API."""

from enum import Enum
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field


class OutputFormat(str, Enum):
    PDF = "pdf"
    PPTX = "pptx"


class Provider(str, Enum):
    GEMINI = "gemini"
    GOOGLE = "google"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class Audience(str, Enum):
    TECHNICAL = "technical"
    EXECUTIVE = "executive"
    CLIENT = "client"
    EDUCATIONAL = "educational"


class ImageStyle(str, Enum):
    AUTO = "auto"
    INFOGRAPHIC = "infographic"
    HANDWRITTEN = "handwritten"
    MINIMALIST = "minimalist"
    CORPORATE = "corporate"
    EDUCATIONAL = "educational"
    DIAGRAM = "diagram"
    CHART = "chart"
    MERMAID = "mermaid"
    DECORATIVE = "decorative"


class FileSource(BaseModel):
    type: Literal["file"] = "file"
    file_id: str


class UrlSource(BaseModel):
    type: Literal["url"] = "url"
    url: str


class TextSource(BaseModel):
    type: Literal["text"] = "text"
    content: str


SourceItem = Annotated[
    Union[FileSource, UrlSource, TextSource],
    Field(discriminator="type"),
]


class Preferences(BaseModel):
    audience: Audience = Audience.TECHNICAL
    image_style: ImageStyle = ImageStyle.AUTO
    temperature: float = Field(default=0.4, ge=0.0, le=1.0)
    max_tokens: int = Field(default=8000, ge=100, le=32000)
    max_slides: int = Field(default=10, ge=1, le=50)
    max_summary_points: int = Field(default=5, ge=1, le=20)
    image_alignment_retries: int = Field(default=2, ge=1, le=5)


class CacheOptions(BaseModel):
    reuse: bool = True


class GenerateRequest(BaseModel):
    """Request model for document generation.
    
    Example:
        {
            "output_format": "pdf",
            "sources": [
                {"type": "file", "file_id": "f_abc123"},
                {"type": "url", "url": "https://example.com/doc"},
                {"type": "text", "content": "Some text content..."}
            ],
            "provider": "gemini"
        }
    """
    output_format: OutputFormat
    sources: list[SourceItem] = Field(
        description="List of sources (file, url, or text)",
        min_length=1,
    )
    provider: Provider = Provider.GEMINI
    model: str = "gemini-2.5-flash"
    image_model: str = "gemini-2.5-flash-image"
    preferences: Preferences = Field(default_factory=Preferences)
    cache: CacheOptions = Field(default_factory=CacheOptions)

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "output_format": "pdf",
                    "sources": [
                        {"type": "file", "file_id": "f_abc123"},
                        {"type": "url", "url": "https://example.com/article"},
                        {"type": "text", "content": "Raw text to include"},
                    ],
                    "provider": "gemini",
                    "model": "gemini-2.5-flash",
                    "image_model": "gemini-2.5-flash-image",
                    "preferences": {
                        "audience": "technical",
                        "image_style": "auto",
                        "temperature": 0.4,
                        "max_tokens": 8000,
                        "max_slides": 10,
                        "max_summary_points": 5,
                        "image_alignment_retries": 2,
                    },
                    "cache": {"reuse": True},
                }
            ]
        }
    )
