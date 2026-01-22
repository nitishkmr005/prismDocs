"""
Content extraction node for unified workflow.

Extracts and processes content from various source types (files, URLs, text)
for use in document, podcast, and mindmap generation.
"""

import uuid
from pathlib import Path

from loguru import logger

from ...domain.content_types import ContentFormat
from ...infrastructure.logging_utils import (
    log_node_start,
    log_node_end,
    log_metric,
    resolve_step_number,
    resolve_total_steps,
)
from ...infrastructure.settings import get_settings
from ...utils.image_understanding import extract_image_content, is_image_file
from ..unified_state import UnifiedWorkflowState, is_document_type, requires_content_extraction


def ingest_sources_node(state: UnifiedWorkflowState) -> UnifiedWorkflowState:
    """
    Extract content from sources specified in the request.

    This node handles:
    - File uploads (PDF, DOCX, TXT, etc.)
    - URLs (web pages)
    - Direct text content

    Args:
        state: Current workflow state with request_data containing sources

    Returns:
        Updated state with raw_content populated
    """
    output_type = state.get("output_type", "")

    # Skip content extraction for image generation (uses prompt directly)
    if not requires_content_extraction(output_type):
        logger.debug(f"Skipping content extraction for {output_type}")
        return state

    if state.get("metadata", {}).get("reused_content") and state.get("raw_content"):
        if is_document_type(output_type):
            input_path = state.get("input_path", "")
            if input_path and Path(input_path).exists():
                log_node_start(
                    "ingest_sources",
                    step_number=resolve_step_number(state, "ingest_sources", 1),
                    total_steps=resolve_total_steps(state, 9),
                )
                logger.info("Reusing extracted content from checkpoint")
                log_node_end("ingest_sources", success=True, details="Reused checkpoint")
                return state
        else:
            log_node_start(
                "ingest_sources",
                step_number=resolve_step_number(state, "ingest_sources", 1),
                total_steps=resolve_total_steps(state, 9),
            )
            logger.info("Reusing extracted content from checkpoint")
            log_node_end("ingest_sources", success=True, details="Reused checkpoint")
            return state

    request_data = state.get("request_data", {})
    sources = request_data.get("sources", [])
    api_key = state.get("api_key", "")
    provider = request_data.get("provider", "gemini")
    model = request_data.get("model", "gemini-2.5-flash")

    log_node_start(
        "ingest_sources",
        step_number=resolve_step_number(state, "ingest_sources", 1),
        total_steps=resolve_total_steps(state, 9),
    )

    if not sources:
        state["errors"] = state.get("errors", []) + ["No sources provided"]
        log_node_end("ingest_sources", success=False, details="No sources")
        return state

    logger.info(f"Extracting content from {len(sources)} sources")
    log_metric("Sources", len(sources))

    try:
        from ..parsers import WebParser, get_parser
        from ...infrastructure.api.services.storage import StorageService

        storage = StorageService()
        content_blocks: list[dict] = []
        content_parts: list[str] = []
        source_count = 0
        file_id: str | None = None

        provider_name = provider.lower()
        if provider_name == "google":
            provider_name = "gemini"

        for source in sources:
            source_type = source.get("type", "")

            if source_type == "file":
                current_file_id = source.get("file_id", "")
                if not current_file_id:
                    continue

                if not file_id:
                    file_id = current_file_id

                file_path = _resolve_upload_path(storage, current_file_id)
                if not file_path:
                    continue

                if file_path.suffix.lower() in {".xlsx", ".xls"}:
                    state["errors"] = state.get("errors", []) + [
                        "Excel files are not supported."
                    ]
                    log_node_end("ingest_sources", success=False, details="Excel not supported")
                    return state

                if is_image_file(file_path):
                    content, metadata = extract_image_content(
                        file_path,
                        provider_name,
                        model,
                        api_key,
                    )
                else:
                    parser = get_parser(_detect_format(file_path))
                    content, metadata = parser.parse(file_path)

                if content:
                    title = metadata.get("title") or file_path.name
                    content_blocks.append(
                        {
                            "title": title,
                            "source": str(file_path),
                            "content": content,
                        }
                    )
                    content_parts.append(content)
                    source_count += 1
                    logger.debug(f"Parsed file: {file_path}")

            elif source_type == "url":
                url = source.get("url", "")
                if not url:
                    continue

                parser_type = source.get("parser")
                parser = WebParser(parser=parser_type)
                content, metadata = parser.parse(url)
                if content:
                    title = metadata.get("title") or url
                    content_blocks.append(
                        {
                            "title": title,
                            "source": url,
                            "content": content,
                        }
                    )
                    content_parts.append(content)
                    source_count += 1
                    logger.debug(f"Parsed URL: {url}")

            elif source_type == "text":
                content = source.get("content", "")
                if content.strip():
                    content_blocks.append(
                        {
                            "title": "Copied Text",
                            "source": "text",
                            "content": content.strip(),
                        }
                    )
                    content_parts.append(content.strip())
                    source_count += 1
                    logger.debug("Added text content")

        if not content_parts:
            state["errors"] = state.get("errors", []) + ["No valid sources provided"]
            log_node_end("ingest_sources", success=False, details="No valid sources")
            return state

        is_doc = is_document_type(output_type)
        if is_doc:
            merged_content = _merge_markdown_sources(content_blocks)
        else:
            merged_content = "\n\n---\n\n".join(content_parts)

        state["raw_content"] = merged_content
        state["metadata"] = state.get("metadata", {})
        state["metadata"]["source_count"] = source_count
        if file_id:
            state["metadata"]["file_id"] = file_id

        if is_doc:
            temp_path = _write_temp_markdown(merged_content)
            state["input_path"] = str(temp_path)

        logger.info(
            f"Extracted {len(merged_content)} chars from {source_count} sources"
        )
        log_metric("Content Length", f"{len(merged_content)} chars")
        log_metric("Parsed Sources", source_count)
        log_node_end(
            "ingest_sources",
            success=True,
            details=f"{source_count} sources, {len(merged_content)} chars",
        )

    except Exception as e:
        logger.error(f"Content extraction failed: {e}")
        state["errors"] = state.get("errors", []) + [
            f"Content extraction failed: {str(e)}"
        ]
        log_node_end("ingest_sources", success=False, details=str(e))

    return state


def _detect_format(file_path: Path) -> str:
    """Detect content format from file extension."""
    suffix = file_path.suffix.lower()
    format_map = {
        ".pdf": ContentFormat.PDF.value,
        ".md": ContentFormat.MARKDOWN.value,
        ".markdown": ContentFormat.MARKDOWN.value,
        ".txt": ContentFormat.TEXT.value,
        ".docx": ContentFormat.DOCX.value,
        ".pptx": ContentFormat.PPTX.value,
        ".html": ContentFormat.HTML.value,
    }
    return format_map.get(suffix, ContentFormat.TEXT.value)


def _merge_markdown_sources(parsed_blocks: list[dict]) -> str:
    """Merge parsed markdown sources into a single document."""
    sections = []
    for block in parsed_blocks:
        title = block.get("title", "Source")
        source = block.get("source", "")
        content = block.get("content", "")
        header = f"## Source: {title}"
        if source and source != "text":
            header += f"\n\nSource: {source}"
        sections.append(f"{header}\n\n{content}")
    return "\n\n---\n\n".join(sections)


def _resolve_upload_path(storage, file_id: str) -> Path | None:
    """Resolve file_id to a stored file path."""
    try:
        return storage.get_upload_path(file_id)
    except FileNotFoundError:
        pattern = f"{file_id}*"
        matches = list(storage.upload_dir.glob(pattern))
        if matches:
            return matches[0]
        logger.warning(f"File not found: {file_id}")
        return None


def _write_temp_markdown(content: str) -> Path:
    """Write merged markdown to a temp file and return its path."""
    settings = get_settings()
    temp_dir = settings.generator.temp_dir
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = temp_dir / f"temp_input_{uuid.uuid4().hex}.md"
    temp_path.write_text(content, encoding="utf-8")
    logger.info(f"Created temp input file: {temp_path}")
    return temp_path


def route_by_output_type(state: UnifiedWorkflowState) -> str:
    """
    Router function to determine which workflow branch to execute.

    Args:
        state: Current workflow state

    Returns:
        Branch name for conditional edge routing
    """
    from ..unified_state import get_output_branch

    return get_output_branch(state)
