"""Opik observability helpers for LLM call tracking."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

try:
    from opik import Opik
except ImportError:  # pragma: no cover - optional dependency
    Opik = None

_client: Any | None = None
_enabled: bool | None = None
_log_dir = Path("src/data/logging")


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
    _write_llm_call_log(
        name=name,
        provider=provider,
        model=model,
        prompt=prompt,
        response=response,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        duration_ms=duration_ms,
    )
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


def _write_llm_call_log(
    *,
    name: str,
    provider: str | None,
    model: str | None,
    prompt: str,
    response: str,
    input_tokens: int | None,
    output_tokens: int | None,
    duration_ms: int | None,
) -> None:
    """
    Persist LLM call metadata to a JSON file under src/data/logging.
    Invoked by: src/doc_generator/infrastructure/observability/opik.py
    """
    try:
        _log_dir.mkdir(parents=True, exist_ok=True)
        now = datetime.now()
        base_name = now.strftime("%Y-%m-%d_%H-%M-%S_llm_calls.json")
        path = _log_dir / base_name
        if path.exists():
            counter = 1
            while True:
                candidate = _log_dir / now.strftime(
                    f"%Y-%m-%d_%H-%M-%S_llm_calls_{counter}.json"
                )
                if not candidate.exists():
                    path = candidate
                    break
                counter += 1

        payload = {
            "timestamp": now.isoformat(timespec="seconds"),
            "purpose": name,
            "model": model or "",
            "prompt": _truncate(prompt),
            "response": _truncate(response),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "latency_seconds": (duration_ms / 1000.0) if duration_ms is not None else None,
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except Exception as exc:
        logger.debug(f"Failed to write LLM call log: {exc}")
