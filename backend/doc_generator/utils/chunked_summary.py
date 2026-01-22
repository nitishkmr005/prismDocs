"""
Chunked summarization utilities.

Generate summaries without truncation by processing content in chunks
and optionally reducing chunk summaries into a single summary.
"""

from __future__ import annotations

from loguru import logger

from ..infrastructure.llm import LLMService
from ..infrastructure.settings import get_settings


def _split_into_chunks(content: str, max_chunk_size: int) -> list[str]:
    """
    Split content into chunks at natural boundaries without truncation.
    """
    if len(content) <= max_chunk_size:
        return [content]

    sections = content.split("\n\n")
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for section in sections:
        section_len = len(section)
        if current_len + section_len + 2 > max_chunk_size and current:
            chunks.append("\n\n".join(current).strip())
            current = []
            current_len = 0

        if section_len > max_chunk_size:
            lines = section.split("\n")
            line_bucket: list[str] = []
            line_len = 0
            for line in lines:
                line_size = len(line) + 1
                if line_len + line_size > max_chunk_size and line_bucket:
                    chunks.append("\n".join(line_bucket).strip())
                    line_bucket = []
                    line_len = 0
                line_bucket.append(line)
                line_len += line_size
            if line_bucket:
                chunks.append("\n".join(line_bucket).strip())
        else:
            current.append(section)
            current_len += section_len + 2

    if current:
        chunks.append("\n\n".join(current).strip())

    return [chunk for chunk in chunks if chunk]


def summarize_content_chunked(
    content: str,
    *,
    api_key: str,
    provider: str,
    model: str,
    max_points: int | None = None,
) -> str:
    """
    Summarize content using chunked map-reduce without truncation.

    Returns empty string if the LLM is unavailable or summarization fails.
    """
    if not content.strip():
        return ""

    settings = get_settings()
    chunk_limit = settings.llm.content_chunk_char_limit
    single_limit = settings.llm.content_single_chunk_char_limit

    provider_name = provider.lower()
    if provider_name == "google":
        provider_name = "gemini"

    llm = LLMService(
        api_key=api_key,
        provider=provider_name,
        model=model,
        max_summary_points=settings.llm.max_summary_points,
        max_slides=settings.llm.max_slides,
        max_tokens_summary=settings.llm.max_tokens_summary,
        max_tokens_slides=settings.llm.max_tokens_slides,
        temperature_summary=settings.llm.temperature_summary,
        temperature_slides=settings.llm.temperature_slides,
    )

    if not llm.is_available():
        logger.warning("LLM unavailable for chunked summarization")
        return ""

    if len(content) <= single_limit:
        return llm.generate_executive_summary(content, max_points=max_points) or ""

    chunks = _split_into_chunks(content, chunk_limit)
    logger.info(f"Summarizing content in {len(chunks)} chunks")

    summaries: list[str] = []
    for idx, chunk in enumerate(chunks, 1):
        summary = llm.generate_executive_summary(chunk, max_points=max_points)
        if summary:
            summaries.append(summary)
        else:
            logger.warning(f"Chunk {idx}/{len(chunks)} summary empty")

    if not summaries:
        return ""

    if len(summaries) == 1:
        return summaries[0]

    merged = "\n".join(summaries)
    reduced = llm.generate_executive_summary(merged, max_points=max_points)
    return reduced or merged
