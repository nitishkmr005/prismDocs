"""Podcast generation service with progress streaming."""

import asyncio
import base64
import json
import os
import wave
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from typing import AsyncIterator

from loguru import logger

from ....application.parsers import WebParser, get_parser
from ....domain.prompts.podcast import podcast_script_prompt, podcast_system_prompt
from ....infrastructure.llm import LLMService
from ....utils.image_understanding import extract_image_content, is_image_file
from ..schemas.podcast import (
    PodcastCompleteEvent,
    PodcastErrorEvent,
    PodcastProgressEvent,
    PodcastRequest,
    PodcastStyle,
    SpeakerConfig,
    VoiceName,
)
from ..schemas.requests import FileSource, TextSource, UrlSource
from .storage import StorageService


def wave_bytes(
    pcm: bytes, channels: int = 1, rate: int = 24000, sample_width: int = 2
) -> bytes:
    """Convert PCM audio data to WAV format bytes.

    Args:
        pcm: Raw PCM audio data
        channels: Number of audio channels
        rate: Sample rate in Hz
        sample_width: Sample width in bytes

    Returns:
        WAV file as bytes
    """
    buffer = BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)
    buffer.seek(0)
    return buffer.read()


class PodcastService:
    """Orchestrates podcast generation with progress streaming."""

    def __init__(self, storage_service: StorageService | None = None):
        """Initialize podcast service."""
        self.storage = storage_service or StorageService()
        self._executor = ThreadPoolExecutor(max_workers=2)

    async def generate(
        self,
        request: PodcastRequest,
        api_key: str,
        user_id: str | None = None,
    ) -> AsyncIterator[PodcastProgressEvent | PodcastCompleteEvent | PodcastErrorEvent]:
        """Generate podcast with progress streaming.

        Args:
            request: Podcast generation request
            api_key: API key for LLM/TTS provider
            user_id: Optional user ID for logging

        Yields:
            Progress events, then completion or error event
        """
        try:
            # Phase 1: Extracting content
            yield PodcastProgressEvent(
                stage="extracting",
                percent=5,
                message="Reading sources...",
            )

            content, source_count = await self._extract_content(request, api_key)

            yield PodcastProgressEvent(
                stage="extracting",
                percent=20,
                message=f"Extracted content from {source_count} source(s)",
            )

            # Phase 2: Generating script
            yield PodcastProgressEvent(
                stage="scripting",
                percent=25,
                message="Creating podcast script...",
            )

            # Configure LLM
            provider_name = request.provider.value
            if provider_name == "google":
                provider_name = "gemini"
            self._configure_api_key(provider_name, api_key)

            llm_service = LLMService(
                provider=provider_name,
                model=request.model,
            )

            if not llm_service.is_available():
                raise ValueError(f"Model {request.model} is not available")

            yield PodcastProgressEvent(
                stage="scripting",
                percent=30,
                message=f"Using {request.model} to write script...",
            )

            # Generate podcast script
            script_json = await self._generate_script(
                llm_service=llm_service,
                content=content,
                style=request.style.value,
                speakers=[
                    {"name": s.name, "role": s.role, "voice": s.voice.value}
                    for s in request.speakers
                ],
                duration_minutes=request.duration_minutes,
                source_count=source_count,
            )

            yield PodcastProgressEvent(
                stage="scripting",
                percent=50,
                message="Script generated, parsing...",
            )

            # Parse script
            script_data = self._parse_script(script_json)
            title = script_data.get("title", "Podcast Episode")
            description = script_data.get("description", "")
            dialogue = script_data.get("dialogue", [])

            logger.info(f"Generated podcast script with {len(dialogue)} exchanges")

            # Phase 3: Text-to-Speech synthesis
            yield PodcastProgressEvent(
                stage="synthesizing",
                percent=55,
                message="Generating audio with AI voices...",
            )

            # Build TTS prompt with speaker dialogue
            tts_prompt = self._build_tts_prompt(dialogue, request.speakers)

            yield PodcastProgressEvent(
                stage="synthesizing",
                percent=60,
                message="Synthesizing multi-speaker audio...",
            )

            # Generate audio using Gemini TTS
            audio_data = await self._synthesize_audio(
                tts_prompt=tts_prompt,
                speakers=request.speakers,
                api_key=api_key,
            )

            yield PodcastProgressEvent(
                stage="synthesizing",
                percent=95,
                message="Encoding audio...",
            )

            # Convert to WAV and base64 encode
            wav_bytes = wave_bytes(audio_data)
            audio_base64 = base64.b64encode(wav_bytes).decode("utf-8")

            # Estimate duration (24kHz, 16-bit mono)
            duration_seconds = len(audio_data) / (24000 * 2)

            yield PodcastProgressEvent(
                stage="complete",
                percent=100,
                message="Podcast generated successfully!",
            )

            # Return completed podcast
            yield PodcastCompleteEvent(
                title=title,
                description=description,
                audio_base64=audio_base64,
                script=dialogue,
                duration_seconds=duration_seconds,
            )

        except Exception as e:
            logger.error(f"Podcast generation failed: {e}")
            yield PodcastErrorEvent(
                message=str(e),
                code="GENERATION_ERROR",
            )

    async def _extract_content(
        self, request: PodcastRequest, api_key: str
    ) -> tuple[str, int]:
        """Extract and merge content from all sources.

        Returns:
            Tuple of (merged content, source count)
        """
        contents: list[str] = []
        loop = asyncio.get_event_loop()

        provider_name = request.provider.value
        if provider_name == "google":
            provider_name = "gemini"

        for source in request.sources:
            if isinstance(source, FileSource):
                # Get file from storage
                file_path = self.storage.get_upload_path(source.file_id)
                if file_path.exists():
                    # Determine content format from file extension
                    if file_path.suffix.lower() in {".xlsx", ".xls"}:
                        raise ValueError("Excel files are not supported.")
                    if is_image_file(file_path):
                        content, _ = await loop.run_in_executor(
                            self._executor,
                            extract_image_content,
                            file_path,
                            provider_name,
                            request.model,
                            api_key,
                        )
                    else:
                        file_extension = file_path.suffix.lstrip(".").lower()
                        parser = get_parser(file_extension)
                        content, _ = await loop.run_in_executor(
                            self._executor, parser.parse, file_path
                        )
                    contents.append(content)
                else:
                    logger.warning(f"File not found: {source.file_id}")

            elif isinstance(source, UrlSource):
                # Parse URL content
                parser = WebParser()
                content, _ = await loop.run_in_executor(
                    self._executor, parser.parse, source.url
                )
                contents.append(content)

            elif isinstance(source, TextSource):
                contents.append(source.content)

        merged_content = "\n\n---\n\n".join(contents)

        # Truncate if too long (to avoid exceeding token limits)
        max_chars = 50000
        if len(merged_content) > max_chars:
            merged_content = merged_content[:max_chars] + "\n\n[Content truncated...]"
            logger.warning(f"Content truncated to {max_chars} characters")

        return merged_content, len(contents)

    def _configure_api_key(self, provider: str, api_key: str) -> None:
        """Configure API key in environment for the provider."""
        if provider == "gemini":
            os.environ["GEMINI_API_KEY"] = api_key
            os.environ["GOOGLE_API_KEY"] = api_key
        elif provider == "openai":
            os.environ["OPENAI_API_KEY"] = api_key
        elif provider == "anthropic":
            os.environ["ANTHROPIC_API_KEY"] = api_key

    async def _generate_script(
        self,
        llm_service: LLMService,
        content: str,
        style: str,
        speakers: list[dict],
        duration_minutes: int,
        source_count: int,
    ) -> str:
        """Call LLM to generate podcast script JSON."""
        loop = asyncio.get_event_loop()

        system_prompt = podcast_system_prompt(style, speakers)
        user_prompt = podcast_script_prompt(content, duration_minutes, source_count)

        result = await loop.run_in_executor(
            self._executor,
            llm_service._call_llm,
            system_prompt,
            user_prompt,
            12000,  # max_tokens
            0.7,  # temperature - slightly higher for natural dialogue
            True,  # json_mode
            "podcast_script_generation",  # step
        )

        return result

    def _parse_script(self, response: str) -> dict:
        """Parse LLM response into script dictionary."""
        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            data = self._extract_json(response)

        if data is None:
            raise ValueError("Failed to parse podcast script JSON response")

        return data

    def _extract_json(self, text: str) -> dict | None:
        """Try to extract JSON object from text."""
        if not text:
            return None

        # Find first { and matching }
        start_idx = None
        for i, ch in enumerate(text):
            if ch == "{":
                start_idx = i
                break

        if start_idx is None:
            return None

        stack = []
        for i in range(start_idx, len(text)):
            ch = text[i]
            if ch == "{":
                stack.append(ch)
            elif ch == "}":
                if stack:
                    stack.pop()
                    if not stack:
                        try:
                            return json.loads(text[start_idx : i + 1])
                        except json.JSONDecodeError:
                            return None

        return None

    def _build_tts_prompt(
        self, dialogue: list[dict], speakers: list[SpeakerConfig]
    ) -> str:
        """Build the TTS prompt from dialogue.

        Args:
            dialogue: List of dialogue entries with speaker and text
            speakers: Speaker configurations

        Returns:
            Formatted TTS prompt
        """
        lines = [
            "TTS the following conversation between "
            + " and ".join(s.name for s in speakers)
            + ":\n"
        ]

        for entry in dialogue:
            speaker = entry.get("speaker", speakers[0].name)
            text = entry.get("text", "")
            lines.append(f"{speaker}: {text}")

        return "\n".join(lines)

    async def _synthesize_audio(
        self,
        tts_prompt: str,
        speakers: list[SpeakerConfig],
        api_key: str,
    ) -> bytes:
        """Generate audio using Gemini TTS.

        Args:
            tts_prompt: The formatted dialogue prompt
            speakers: Speaker configurations with voice assignments
            api_key: Gemini API key

        Returns:
            Raw PCM audio data
        """
        loop = asyncio.get_event_loop()

        def _generate_tts():
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)

            # Build speaker voice configs
            speaker_voice_configs = []
            for speaker in speakers:
                speaker_voice_configs.append(
                    types.SpeakerVoiceConfig(
                        speaker=speaker.name,
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=speaker.voice.value,
                            )
                        ),
                    )
                )

            response = client.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents=tts_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                            speaker_voice_configs=speaker_voice_configs
                        )
                    ),
                ),
            )

            # Extract audio data from response
            audio_data = response.candidates[0].content.parts[0].inline_data.data
            return audio_data

        return await loop.run_in_executor(self._executor, _generate_tts)


# Singleton instance
_podcast_service: PodcastService | None = None


def get_podcast_service() -> PodcastService:
    """Get or create podcast service instance."""
    global _podcast_service
    if _podcast_service is None:
        _podcast_service = PodcastService()
    return _podcast_service
