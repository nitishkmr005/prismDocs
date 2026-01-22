"""
Podcast generation nodes for unified workflow.

Handles:
- Script generation from content
- Audio synthesis using Gemini TTS
"""

import asyncio
import base64
import json
import wave
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from typing import Any

from loguru import logger

from ..unified_state import UnifiedWorkflowState


def wave_bytes(
    pcm: bytes, channels: int = 1, rate: int = 24000, sample_width: int = 2
) -> bytes:
    """Convert PCM audio data to WAV format bytes."""
    with BytesIO() as wav_buffer:
        with wave.open(wav_buffer, "wb") as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(rate)
            wav_file.writeframes(pcm)
        return wav_buffer.getvalue()


def generate_podcast_script_node(state: UnifiedWorkflowState) -> UnifiedWorkflowState:
    """
    Generate podcast script from extracted content.

    Uses LLM to create a dialogue-based script suitable for TTS synthesis.

    Args:
        state: Current workflow state with raw_content

    Returns:
        Updated state with podcast_script and podcast_dialogue
    """
    request_data = state.get("request_data", {})
    raw_content = state.get("summary_content") or state.get("raw_content", "")
    api_key = state.get("api_key", "")

    if not raw_content:
        state["errors"] = state.get("errors", []) + ["No content for podcast script"]
        return state

    # Extract podcast configuration
    style = request_data.get("style", "conversational")
    speakers = request_data.get(
        "speakers",
        [
            {"name": "Alex", "voice": "Kore", "role": "host"},
            {"name": "Sam", "voice": "Puck", "role": "co-host"},
        ],
    )
    duration_minutes = request_data.get("duration_minutes", 3)
    provider = request_data.get("provider", "gemini")
    model = request_data.get("model", "gemini-2.5-flash")

    logger.info(
        f"Generating podcast script: style={style}, duration={duration_minutes}min"
    )

    try:
        # Configure LLM
        from ...infrastructure.llm import LLMService
        import os

        provider_name = provider if provider != "google" else "gemini"

        # Set API key in environment
        key_mapping = {
            "gemini": "GOOGLE_API_KEY",
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
        }
        env_var = key_mapping.get(provider_name)
        if env_var and api_key:
            os.environ[env_var] = api_key

        llm_service = LLMService(provider=provider_name, model=model)

        # Build prompt for script generation
        speaker_list = ", ".join([f"{s['name']} ({s['role']})" for s in speakers])
        source_count = state.get("metadata", {}).get("source_count", 1)

        prompt = f"""Generate a podcast script about the following content.

CONTENT:
{raw_content}

REQUIREMENTS:
- Style: {style}
- Target duration: {duration_minutes} minutes
- Speakers: {speaker_list}
- Based on {source_count} source document(s)

OUTPUT FORMAT (JSON):
{{
  "title": "Episode title",
  "description": "Brief episode description",
  "dialogue": [
    {{"speaker": "SpeakerName", "text": "What they say..."}},
    {{"speaker": "OtherSpeaker", "text": "Their response..."}}
  ]
}}

Create an engaging dialogue that covers the key points from the content.
The dialogue should feel natural and conversational."""

        # Generate script
        response = llm_service.generate(prompt)

        # Parse response
        script_json = _extract_json(response)
        if not script_json:
            state["errors"] = state.get("errors", []) + [
                "Failed to parse podcast script"
            ]
            return state

        state["podcast_script"] = response
        state["podcast_dialogue"] = script_json.get("dialogue", [])
        state["podcast_title"] = script_json.get("title", "Podcast Episode")
        state["podcast_description"] = script_json.get("description", "")

        logger.info(
            f"Generated script with {len(state['podcast_dialogue'])} dialogue entries"
        )

    except Exception as e:
        logger.error(f"Podcast script generation failed: {e}")
        state["errors"] = state.get("errors", []) + [
            f"Script generation failed: {str(e)}"
        ]

    return state


def synthesize_podcast_audio_node(state: UnifiedWorkflowState) -> UnifiedWorkflowState:
    """
    Synthesize audio from podcast script using Gemini TTS.

    Args:
        state: Current workflow state with podcast_dialogue

    Returns:
        Updated state with podcast_audio_base64
    """
    dialogue = state.get("podcast_dialogue", [])
    request_data = state.get("request_data", {})
    gemini_api_key = state.get("gemini_api_key") or state.get("api_key", "")

    if not dialogue:
        state["errors"] = state.get("errors", []) + ["No dialogue for audio synthesis"]
        return state

    if not gemini_api_key:
        state["errors"] = state.get("errors", []) + ["Gemini API key required for TTS"]
        return state

    speakers = request_data.get(
        "speakers",
        [
            {"name": "Alex", "voice": "Kore", "role": "host"},
            {"name": "Sam", "voice": "Puck", "role": "co-host"},
        ],
    )

    logger.info(f"Synthesizing audio for {len(dialogue)} dialogue entries")

    try:
        # Build TTS prompt
        tts_prompt = _build_tts_prompt(dialogue, speakers)

        # Generate audio using Gemini TTS (with retry)
        audio_data = _synthesize_with_retry(tts_prompt, speakers, gemini_api_key)

        # Convert to WAV
        wav_data = wave_bytes(audio_data)
        audio_base64 = base64.b64encode(wav_data).decode()

        state["podcast_audio_data"] = audio_data
        state["podcast_audio_base64"] = audio_base64
        state["podcast_duration_seconds"] = len(audio_data) / (
            24000 * 2
        )  # 24kHz, 16-bit
        state["completed"] = True

        logger.info(f"Synthesized {state['podcast_duration_seconds']:.1f}s of audio")

    except Exception as e:
        logger.error(f"Audio synthesis failed: {e}")
        state["errors"] = state.get("errors", []) + [
            f"Audio synthesis failed: {str(e)}"
        ]

    return state


def _build_tts_prompt(dialogue: list[dict], speakers: list[dict]) -> str:
    """Build the TTS prompt from dialogue."""
    lines = []
    for entry in dialogue:
        speaker = entry.get("speaker", "Speaker")
        text = entry.get("text", "")
        if text.strip():
            lines.append(f"{speaker}: {text}")
    return "\n".join(lines)


def _synthesize_with_retry(
    tts_prompt: str,
    speakers: list[dict],
    api_key: str,
    max_retries: int = 3,
) -> bytes:
    """Generate audio using Gemini TTS with retry logic."""
    import time
    import random

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    # Build speaker voice configs
    speaker_voice_configs = []
    for speaker in speakers:
        voice_name = speaker.get("voice", "Kore")
        speaker_voice_configs.append(
            types.SpeakerVoiceConfig(
                speaker=speaker["name"],
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice_name,
                    )
                ),
            )
        )

    last_error = None
    for attempt in range(max_retries):
        try:
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

            audio_data = response.candidates[0].content.parts[0].inline_data.data
            if attempt > 0:
                logger.info(f"TTS succeeded on attempt {attempt + 1}")
            return audio_data

        except Exception as e:
            last_error = e
            error_str = str(e).lower()

            retryable = any(
                p in error_str for p in ["500", "internal", "overload", "unavailable"]
            )

            if retryable and attempt < max_retries - 1:
                delay = (2**attempt) * (1 + random.uniform(0, 0.5))
                logger.warning(
                    f"TTS error (attempt {attempt + 1}/{max_retries}): {str(e)[:100]}. Retrying in {delay:.1f}s..."
                )
                time.sleep(delay)
            else:
                raise

    if last_error:
        raise last_error
    raise RuntimeError("TTS generation failed unexpectedly")


def _extract_json(text: str) -> dict | None:
    """Extract JSON from text."""
    import re

    if not text:
        return None
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON in code blocks
    patterns = [
        r"```json\s*([\s\S]*?)\s*```",
        r"```\s*([\s\S]*?)\s*```",
        r"\{[\s\S]*\}",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                json_str = match.group(1) if "```" in pattern else match.group(0)
                return json.loads(json_str)
            except (json.JSONDecodeError, IndexError):
                continue

    return None
