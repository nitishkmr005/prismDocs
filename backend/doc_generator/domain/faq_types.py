"""
FAQ document type definitions.

Defines the structure for FAQ generation output.
"""

from pydantic import BaseModel, Field


class FAQItem(BaseModel):
    """A single FAQ question-answer pair."""

    id: str = Field(..., description="Unique identifier for the FAQ item")
    question: str = Field(..., description="The question text")
    answer: str = Field(..., description="The answer text (supports markdown)")
    tags: list[str] = Field(default_factory=list, description="Topic tags")


class FAQMetadata(BaseModel):
    """Metadata for an FAQ document."""

    source_count: int = Field(default=0, description="Number of sources used")
    generated_at: str = Field(..., description="ISO timestamp of generation")
    tag_colors: dict[str, str] = Field(
        default_factory=dict, description="Tag to gradient color mapping"
    )


class FAQDocument(BaseModel):
    """Complete FAQ document structure."""

    title: str = Field(..., description="Document title")
    description: str | None = Field(None, description="Optional summary")
    items: list[FAQItem] = Field(default_factory=list, description="FAQ items")
    metadata: FAQMetadata = Field(..., description="Document metadata")
