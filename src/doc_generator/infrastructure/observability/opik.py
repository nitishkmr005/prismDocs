"""Opik observability helpers for LLM call tracking."""

from __future__ import annotations

import os
from typing import Any

from loguru import logger

try:
    from opik import Opik
except ImportError:  # pragma: no cover - optional dependency
    Opik = None

_client: Any | None = None
_enabled: bool | None = None


def _truncate(text: str | None, limit: int = 4000) -> str:
    """
    Invoked by: src/doc_generator/infrastructure/observability/opik.py
    """
    if not text:
        return ""
    text = str(text)
    if len(text) <= limit:
        return text
    return f"{text[:limit]}...[truncated]"


def _get_client() -> Any | None:
    """
    Invoked by: src/doc_generator/infrastructure/observability/opik.py
    """
    global _client, _enabled
    if _enabled is False:
        return None

    if _enabled is None:
        api_key = os.getenv("COMET_API_KEY")
        if not api_key:
            _enabled = False
            return None
        if Opik is None:
            logger.debug("Opik not installed; skipping LLM tracing")
            _enabled = False
            return None
        _enabled = True

    if _client is None:
        try:
            _client = Opik(
                api_key=os.getenv("COMET_API_KEY"),
                project_name=os.getenv("OPIK_PROJECT_NAME", "document-generator"),
            )
        except TypeError:
            try:
                _client = Opik()
            except Exception as exc:
                logger.debug(f"Failed to initialize Opik client: {exc}")
                _enabled = False
                return None
    return _client


def log_llm_call(
    name: str,
    prompt: str,
    response: str,
    *,
    provider: str | None = None,
    model: str | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    duration_ms: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """
    Log a single LLM call to Opik, if configured.
    Invoked by: src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/generate_images.py, src/doc_generator/infrastructure/image/claude_svg.py, src/doc_generator/infrastructure/image/gemini.py, src/doc_generator/infrastructure/llm/content_generator.py, src/doc_generator/infrastructure/llm/service.py, src/doc_generator/infrastructure/observability/opik.py
    """
    client = _get_client()
    if client is None:
        return

    meta: dict[str, Any] = {}
    if provider:
        meta["provider"] = provider
    if model:
        meta["model"] = model
    if input_tokens is not None:
        meta["input_tokens"] = input_tokens
    if output_tokens is not None:
        meta["output_tokens"] = output_tokens
    if duration_ms is not None:
        meta["duration_ms"] = duration_ms
    if metadata:
        meta.update(metadata)

    prompt_text = _truncate(prompt)
    response_text = _truncate(response)

    # Try native helper if available.
    try:
        if hasattr(client, "log_llm_call"):
            client.log_llm_call(
                name=name,
                input=prompt_text,
                output=response_text,
                metadata=meta,
            )
            return
    except Exception as exc:
        logger.debug(f"Opik log_llm_call failed: {exc}")

    # Fallback to trace-style API if present.
    try:
        if hasattr(client, "trace"):
            trace = client.trace(
                name=name,
                input=prompt_text,
                metadata=meta,
            )
            if hasattr(trace, "end"):
                trace.end(output=response_text, metadata=meta)
            elif hasattr(trace, "log"):
                trace.log(output=response_text, metadata=meta)
            return
    except Exception as exc:
        logger.debug(f"Opik trace failed: {exc}")
