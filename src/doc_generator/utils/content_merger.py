"""
Content merger utility for combining multiple parsed documents into a single output.

This module provides functions to merge content from multiple files in a folder
into a cohesive blog-style document using LLM-powered transformation with
chunked processing for comprehensive coverage.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger

from ..infrastructure.llm_content_generator import get_content_generator
from ..infrastructure.llm_service import LLMService
from ..infrastructure.settings import get_settings
from .content_cleaner import clean_content_for_output


def _detect_content_types(parsed_contents: list[dict]) -> str:
    """
    Detect the primary content type from parsed files.
    
    Args:
        parsed_contents: List of parsed content dicts
        
    Returns:
        Content type: "transcript", "slides", "mixed", or "document"
    Invoked by: src/doc_generator/utils/content_merger.py
    """
    import re
    
    has_transcript = False
    has_slides = False
    
    for content in parsed_contents:
        filename = content.get("filename", "").lower()
        raw_content = content.get("raw_content", "")
        
        # Check filename for hints
        if "transcript" in filename or "lecture" in filename:
            has_transcript = True
        if filename.endswith(".pdf") or filename.endswith(".pptx"):
            has_slides = True
        
        # Check content for timestamps (transcript indicator)
        timestamp_pattern = r'^\d{1,2}:\d{2}(:\d{2})?\s*$'
        timestamp_count = len(re.findall(timestamp_pattern, raw_content, re.MULTILINE))
        if timestamp_count > 10:
            has_transcript = True
    
    if has_transcript and has_slides:
        return "mixed"
    elif has_transcript:
        return "transcript"
    elif has_slides:
        return "slides"
    return "document"


def merge_folder_content(
    parsed_contents: list[dict],
    folder_name: str,
    llm_service: Optional[LLMService] = None
) -> dict:
    """
    Merge content from multiple parsed files into a single comprehensive blog-style document.

    Uses LLM with chunked processing to transform and merge ALL content from multiple 
    sources (transcripts, slides, documents) into a cohesive educational blog post with
    visual markers for diagram generation.

    Args:
        parsed_contents: List of parsed content dicts with keys:
            - filename: Original filename
            - raw_content: Raw parsed content
            - structured_content: Structured content
            - metadata: File metadata
        folder_name: Name of the folder (used as topic/title hint)
        llm_service: Optional LLM service for additional enhancements

    Returns:
        Dict with:
            - temp_file: Path to temporary merged markdown file
            - metadata: Combined metadata including LLM-generated title
            - num_files: Number of files merged
    Invoked by: scripts/generate_from_folder.py
    """
    logger.info(f"Merging {len(parsed_contents)} files using chunked LLM transformation")

    # Format initial title from folder name (will be replaced by LLM-generated title)
    initial_title = folder_name.replace("-", " ").replace("_", " ").title()
    
    # Detect content type
    content_type = _detect_content_types(parsed_contents)
    logger.info(f"Detected content type: {content_type}")
    
    # Combine ALL raw content from ALL files
    all_raw_content = []
    total_chars = 0
    
    for content in parsed_contents:
        filename = content.get("filename", "")
        raw_content = content.get("raw_content", "")
        
        if raw_content:
            content_len = len(raw_content)
            total_chars += content_len
            logger.info(f"Adding content from {filename}: {content_len} chars")
            # Add source marker for context
            all_raw_content.append(f"--- Source: {filename} ---\n{raw_content}")
    
    combined_raw = "\n\n".join(all_raw_content)
    logger.info(f"Total combined content: {total_chars} chars from {len(all_raw_content)} files")
    
    # Get content generator for LLM transformation
    content_generator = get_content_generator()
    
    merged_content = ""
    final_title = initial_title
    visual_markers_count = 0
    
    if content_generator.is_available():
        logger.info("Using LLM Content Generator with chunked processing for full content")
        
        # Transform ALL combined content using LLM with chunking
        # No truncation - the generator handles chunked processing internally
        generated = content_generator.generate_blog_content(
            raw_content=combined_raw,
            content_type=content_type,
            topic=initial_title
        )
        
        # Use the LLM-generated content
        merged_content = generated.markdown
        final_title = generated.title
        visual_markers_count = len(generated.visual_markers)
        
        logger.success(
            f"LLM transformation complete: "
            f"{len(merged_content)} chars output from {total_chars} chars input, "
            f"{visual_markers_count} visual markers, "
            f"{len(generated.sections)} sections"
        )
    else:
        logger.info("LLM not available - using basic concatenation merge")
        merged_content = _basic_merge(parsed_contents, initial_title, llm_service)
    
    # Write merged content to topic-specific output folder
    settings = get_settings()
    topic_output_dir = settings.generator.output_dir / folder_name
    topic_output_dir.mkdir(parents=True, exist_ok=True)

    merged_file = topic_output_dir / f"{folder_name}_merged.md"
    merged_file.write_text(merged_content, encoding="utf-8")

    logger.success(f"Merged content written to: {merged_file} ({len(merged_content)} chars)")

    # Combine metadata from all files with LLM-generated title
    combined_metadata = {
        "title": final_title,
        "custom_filename": folder_name,  # Use folder name for output filename
        "topic": folder_name,
        "num_source_files": len(parsed_contents),
        "source_files": [content["filename"] for content in parsed_contents],
        "total_source_chars": total_chars,
        "generated_date": datetime.now().isoformat(),
        "author": "Document Generator",
        "content_type": content_type,
    }

    # Merge individual file metadata
    all_tags = set()
    all_authors = set()
    for content in parsed_contents:
        metadata = content.get("metadata", {})
        if "tags" in metadata:
            if isinstance(metadata["tags"], list):
                all_tags.update(metadata["tags"])
            else:
                all_tags.add(str(metadata["tags"]))
        if "author" in metadata and metadata["author"]:
            all_authors.add(metadata["author"])

    if all_tags:
        combined_metadata["tags"] = sorted(list(all_tags))
    if all_authors:
        combined_metadata["authors"] = sorted(list(all_authors))

    return {
        "temp_file": str(merged_file),  # Now stored in topic output folder
        "metadata": combined_metadata,
        "num_files": len(parsed_contents)
    }


def _basic_merge(
    parsed_contents: list[dict],
    title: str,
    llm_service: Optional[LLMService] = None
) -> str:
    """
    Basic merge fallback when LLM is not available.
    
    Args:
        parsed_contents: List of parsed content dicts
        title: Document title
        llm_service: Optional LLM service for executive summary
        
    Returns:
        Merged markdown content
    Invoked by: src/doc_generator/utils/content_merger.py
    """
    sections = []

    # Add title
    sections.append(f"# {title}\n")

    # Add metadata section
    sections.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    sections.append(f"**Source Files:** {len(parsed_contents)}\n")
    sections.append("\n---\n\n")

    # Add table of contents if multiple files
    if len(parsed_contents) > 1:
        sections.append("## Table of Contents\n\n")
        for idx, content in enumerate(parsed_contents, 1):
            filename = content["filename"]
            section_title = Path(filename).stem.replace("-", " ").replace("_", " ").title()
            sections.append(f"{idx}. [{section_title}](#{section_title.lower().replace(' ', '-')})\n")
        sections.append("\n---\n\n")

    # Generate executive summary using LLM if available
    if llm_service and llm_service.is_available():
        try:
            logger.info("Generating executive summary...")
            all_text = "\n\n".join([
                content.get("raw_content", "")
                for content in parsed_contents
                if content.get("raw_content")
            ])

            if all_text:
                summary = llm_service.generate_executive_summary(all_text)
                if summary:
                    sections.append("## Executive Summary\n\n")
                    sections.append(summary)
                    sections.append("\n\n---\n\n")
        except Exception as e:
            logger.warning(f"Failed to generate executive summary: {e}")

    # Add content from each file
    for idx, content in enumerate(parsed_contents, 1):
        filename = content["filename"]

        content_text = content.get("raw_content", "")
        if not content_text:
            structured = content.get("structured_content", "")
            if isinstance(structured, str):
                content_text = structured
            else:
                continue

        # Clean the content
        content_text = clean_content_for_output(content_text)

        section_title = Path(filename).stem.replace("-", " ").replace("_", " ").title()

        if idx > 1:
            sections.append("\n---\n\n")

        sections.append(f"## {section_title}\n\n")
        sections.append(f"*Source: {filename}*\n\n")

        adjusted_content = _adjust_header_levels(content_text)
        sections.append(adjusted_content)
        sections.append("\n\n")

    return "".join(sections)


def _adjust_header_levels(content: str) -> str:
    """
    Adjust markdown header levels to fit within the merged document structure.

    Since the merged document uses # for title and ## for sections,
    we shift all headers in individual content down by 2 levels.

    Args:
        content: Markdown content

    Returns:
        Content with adjusted header levels
    Invoked by: src/doc_generator/utils/content_merger.py
    """
    lines = content.split("\n")
    adjusted_lines = []

    for line in lines:
        if line.strip().startswith("#"):
            header_match = line.lstrip()
            hash_count = 0
            for char in header_match:
                if char == "#":
                    hash_count += 1
                else:
                    break

            new_level = min(hash_count + 2, 6)
            header_text = header_match[hash_count:].lstrip()
            adjusted_line = "#" * new_level + " " + header_text
            adjusted_lines.append(adjusted_line)
        else:
            adjusted_lines.append(line)

    return "\n".join(adjusted_lines)
