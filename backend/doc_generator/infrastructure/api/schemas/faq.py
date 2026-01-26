"""Pydantic request and response models for FAQ generation."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .requests import Provider, SourceItem


class FAQRequest(BaseModel):
    """Request model for FAQ generation."""

    sources: list[SourceItem] = Field(
        description="Single source (file, url, or text)",
        min_length=1,
        max_length=1,
    )
    provider: Provider = Provider.GEMINI
    model: str = "gemini-2.5-flash"

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "sources": [
                        {"type": "url", "url": "https://example.com/article"}
                    ],
                    "provider": "gemini",
                    "model": "gemini-2.5-flash",
                }
            ]
        }
    )


class FAQItemResponse(BaseModel):
    """A single FAQ item in the response."""

    id: str
    question: str
    answer: str
    tags: list[str] = Field(default_factory=list)


class FAQMetadataResponse(BaseModel):
    """Metadata in FAQ response."""

    source_count: int = 0
    generated_at: str
    tag_colors: dict[str, str] = Field(default_factory=dict)


class FAQDocumentResponse(BaseModel):
    """Complete FAQ document response."""

    title: str
    description: str | None = None
    items: list[FAQItemResponse] = Field(default_factory=list)
    metadata: FAQMetadataResponse


class FAQProgressEvent(BaseModel):
    """Progress event during FAQ generation."""

    type: Literal["progress"] = "progress"
    stage: str
    percent: float = Field(ge=0, le=100)
    message: str | None = None


class FAQCompleteEvent(BaseModel):
    """Completion event with FAQ data."""

    type: Literal["complete"] = "complete"
    document: FAQDocumentResponse
    download_url: str
    file_path: str
    session_id: str | None = None


class FAQErrorEvent(BaseModel):
    """Error event during FAQ generation."""

    type: Literal["error"] = "error"
    message: str
    code: str | None = None
