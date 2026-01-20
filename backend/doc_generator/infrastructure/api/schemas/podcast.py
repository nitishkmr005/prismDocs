"""Pydantic request and response models for podcast generation."""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .requests import Provider, SourceItem


class PodcastStyle(str, Enum):
    """Podcast generation styles."""

    CONVERSATIONAL = "conversational"  # Casual chat between hosts
    INTERVIEW = "interview"  # Host interviewing an expert
    EDUCATIONAL = "educational"  # Teaching/explaining content
    DEBATE = "debate"  # Two opposing viewpoints
    STORYTELLING = "storytelling"  # Narrative style


class VoiceName(str, Enum):
    """Available voice names for TTS."""

    KORE = "Kore"  # Male voice
    PUCK = "Puck"  # Female voice
    CHARON = "Charon"  # Deep male voice
    FENRIR = "Fenrir"  # Energetic male voice
    AOEDE = "Aoede"  # Warm female voice
    LEDA = "Leda"  # Professional female voice


class SpeakerConfig(BaseModel):
    """Configuration for a podcast speaker."""

    name: str = Field(description="Speaker name used in the script")
    voice: VoiceName = Field(description="TTS voice to use for this speaker")
    role: str = Field(default="host", description="Speaker role (host, guest, expert)")


class PodcastRequest(BaseModel):
    """Request model for podcast generation.

    Example:
        {
            "sources": [
                {"type": "file", "file_id": "f_abc123"},
                {"type": "url", "url": "https://example.com/article"},
                {"type": "text", "content": "Some text content..."}
            ],
            "style": "conversational",
            "provider": "gemini",
            "model": "gemini-2.5-flash",
            "speakers": [
                {"name": "Alex", "voice": "Kore", "role": "host"},
                {"name": "Sam", "voice": "Puck", "role": "co-host"}
            ],
            "duration_minutes": 5
        }
    """

    sources: list[SourceItem] = Field(
        description="List of sources (file, url, or text)",
        min_length=1,
    )
    style: PodcastStyle = PodcastStyle.CONVERSATIONAL
    provider: Provider = Provider.GEMINI
    model: str = "gemini-2.5-flash"
    speakers: list[SpeakerConfig] = Field(
        default_factory=lambda: [
            SpeakerConfig(name="Alex", voice=VoiceName.KORE, role="host"),
            SpeakerConfig(name="Sam", voice=VoiceName.PUCK, role="co-host"),
        ],
        min_length=2,
        max_length=4,
        description="Speaker configurations (2-4 speakers)",
    )
    duration_minutes: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Target podcast duration in minutes",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "sources": [
                        {"type": "url", "url": "https://example.com/article"},
                        {"type": "text", "content": "Additional context"},
                    ],
                    "style": "conversational",
                    "provider": "gemini",
                    "model": "gemini-2.5-flash",
                    "speakers": [
                        {"name": "Alex", "voice": "Kore", "role": "host"},
                        {"name": "Sam", "voice": "Puck", "role": "co-host"},
                    ],
                    "duration_minutes": 5,
                }
            ]
        }
    )


class PodcastScript(BaseModel):
    """Generated podcast script with dialogue."""

    title: str
    description: str
    dialogue: list[dict]  # List of {speaker: str, text: str}


# SSE Event Models


class PodcastProgressEvent(BaseModel):
    """Progress event during podcast generation."""

    type: Literal["progress"] = "progress"
    stage: str  # extracting, scripting, synthesizing
    percent: float = Field(ge=0, le=100)
    message: str | None = None


class PodcastCompleteEvent(BaseModel):
    """Completion event with podcast audio data."""

    type: Literal["complete"] = "complete"
    title: str
    description: str
    audio_base64: str  # Base64-encoded WAV audio
    script: list[dict]  # The generated dialogue script
    duration_seconds: float


class PodcastErrorEvent(BaseModel):
    """Error event during podcast generation."""

    type: Literal["error"] = "error"
    message: str
    code: str | None = None
