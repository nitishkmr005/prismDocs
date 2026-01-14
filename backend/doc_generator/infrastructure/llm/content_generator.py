"""
LLM-powered content generator for transforming raw documents into structured blog content.

Transforms raw transcripts, documents, and slides into well-structured educational
content with visual markers for diagram generation. Supports chunked processing
for long documents.
"""

import json
import re
import time
from dataclasses import dataclass, field
from typing import Optional

from loguru import logger

from ..observability.opik import log_llm_call
from ..settings import get_settings
from ...domain.prompts.text.content_generator_prompts import (
    build_blog_from_outline_prompt,
    build_chunk_prompt,
    build_generation_prompt,
    build_outline_prompt,
    build_title_prompt,
    get_content_system_prompt,
)

try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logger.warning("google-genai not installed - Gemini content generation disabled")

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


@dataclass
class VisualMarker:
    """Represents a visual marker extracted from content."""
    
    marker_id: str
    visual_type: str  # architecture, flowchart, comparison, concept_map, mind_map, mermaid
    title: str
    description: str
    position: int  # Character position in content


@dataclass
class GeneratedContent:
    """Result of LLM content generation."""
    
    markdown: str  # The generated blog-style markdown
    visual_markers: list[VisualMarker]  # Extracted visual markers
    title: str
    sections: list[str]  # Section headings for TOC
    outline: str = ""


class LLMContentGenerator:
    """
    Transform raw content into structured blog-style markdown using LLM.
    
    Features:
    - Chunked processing for long documents (no truncation)
    - Removes timestamps and conversational artifacts from transcripts
    - Organizes content into logical sections with clear headings
    - Inserts visual markers where diagrams should appear
    - Generates inline mermaid code for simple diagrams
    - Numbered sections matching professional blog style
    """
    
    _total_calls: int = 0
    _models_used: set[str] = set()
    _providers_used: set[str] = set()
    _call_details: list[dict] = []
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the content generator with a content generation client.
        
        - Content generation: Uses configured provider (Gemini/OpenAI/Claude)
        
        Args:
            api_key: API key override. If not provided, uses env vars.
        Invoked by: (no references found)
        """
        import os
        
        self.settings = get_settings()
        self.claude_api_key = api_key or os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
        self.openai_api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.gemini_api_key = api_key or os.getenv("GEMINI_API_KEY")
        
        # Content generation client (prefer OpenAI GPT-4o)
        self.content_client = None
        self.content_provider = None
        self.content_model = None
        
        # Setup content generation client (provider-driven)
        self.content_provider = self.settings.llm.content_provider or "openai"
        self.content_model = self.settings.llm.content_model or self.settings.llm.model

        self._init_content_client()
        
        # Legacy compatibility
        self.client = self.content_client
        self.provider = self.content_provider
        self.model = self.content_model

    def _init_content_client(self) -> None:
        """
        Initialize the content generation client based on settings.
        Invoked by: src/doc_generator/infrastructure/llm/content_generator.py
        """
        if self.content_provider == "gemini":
            if self.gemini_api_key and GENAI_AVAILABLE:
                self.content_client = genai.Client(api_key=self.gemini_api_key)
                logger.info(f"Content Generator initialized with Gemini: {self.content_model}")
            else:
                logger.warning("Gemini requested but not available for content generation")
                self.content_client = None
            return

        if self.content_provider == "openai":
            if self.openai_api_key and OPENAI_AVAILABLE:
                self.content_client = OpenAI(api_key=self.openai_api_key)
                logger.info(f"Content Generator initialized with OpenAI: {self.content_model}")
            else:
                logger.warning("OpenAI requested but not available for content generation")
                self.content_client = None
            return

        if self.content_provider == "claude":
            if self.claude_api_key and ANTHROPIC_AVAILABLE:
                self.content_client = Anthropic(api_key=self.claude_api_key)
                logger.info(f"Content Generator initialized with Claude: {self.content_model}")
            else:
                logger.warning("Claude requested but not available for content generation")
                self.content_client = None
            return

        logger.warning("Unsupported content provider requested - content generation disabled")

    def is_available(self) -> bool:
        """
        Check if LLM content generation is available.
        Invoked by: scripts/run_generator.py, src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/nodes/transform_content.py, src/doc_generator/application/workflow/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/transform_content.py, src/doc_generator/infrastructure/generators/pdf/utils.py, src/doc_generator/infrastructure/image/claude_svg.py, src/doc_generator/infrastructure/image/gemini.py, src/doc_generator/infrastructure/llm/content_generator.py, src/doc_generator/infrastructure/llm/service.py, src/doc_generator/infrastructure/pdf_utils.py, src/doc_generator/utils/content_merger.py
        """
        return self.content_client is not None
    
    def generate_blog_content(
        self,
        raw_content: str,
        content_type: str = "transcript",
        topic: str = "",
        max_tokens: int = 8000
    ) -> GeneratedContent:
        """
        Transform raw content into structured blog-style markdown using chunked processing.
        
        Args:
            raw_content: Raw text content (transcript, document, etc.)
            content_type: Type of content ("transcript", "document", "slides", "mixed")
            topic: Optional topic/title hint
            max_tokens: Maximum tokens for LLM response per chunk
            
        Returns:
            GeneratedContent with markdown and visual markers
        Invoked by: src/doc_generator/application/nodes/transform_content.py, src/doc_generator/application/workflow/nodes/transform_content.py, src/doc_generator/utils/content_merger.py
        """
        if not self.is_available():
            logger.warning("LLM not available, returning cleaned raw content")
            return self._fallback_generation(raw_content, topic)
        
        content_length = len(raw_content)
        logger.info(f"Processing {content_length} characters of {content_type} content")

        outline = self.generate_blog_outline(raw_content, content_type, topic)
        
        # For short content, process directly
        if content_length <= self.settings.llm.content_single_chunk_char_limit:
            return self._process_single_chunk(
                raw_content,
                content_type,
                topic,
                max_tokens,
                outline=outline,
            )
        
        # For long content, use chunked processing
        logger.info(f"Content too long ({content_length} chars), using chunked processing")
        return self._process_chunked(
            raw_content,
            content_type,
            topic,
            max_tokens,
            outline=outline,
        )
    
    def _process_single_chunk(
        self,
        content: str,
        content_type: str,
        topic: str,
        max_tokens: int,
        outline: str = ""
    ) -> GeneratedContent:
        """
        Process a single chunk of content.
        Invoked by: src/doc_generator/infrastructure/llm/content_generator.py
        """
        if outline:
            prompt = self._build_blog_from_outline_prompt(content, content_type, topic, outline)
        else:
            prompt = self._build_generation_prompt(content, content_type, topic, is_chunk=False)
        
        try:
            generated_text = self._call_llm(prompt, max_tokens, step="content_generate")
            return self._parse_generated_content(generated_text, topic, outline=outline)
        except Exception as e:
            logger.error(f"LLM content generation failed: {e}")
            return self._fallback_generation(content, topic)
    
    def _process_chunked(
        self,
        raw_content: str,
        content_type: str,
        topic: str,
        max_tokens: int,
        outline: str = ""
    ) -> GeneratedContent:
        """
        Process long content in chunks and merge results.
        Invoked by: src/doc_generator/infrastructure/llm/content_generator.py
        """
        
        # Split content into manageable chunks
        chunks = self._split_into_chunks(
            raw_content,
            max_chunk_size=self.settings.llm.content_chunk_char_limit,
        )
        logger.info(f"Split content into {len(chunks)} chunks")
        
        # First, generate a title based on content overview
        title = self._extract_title_from_outline(outline, topic) if outline else ""
        if not title:
            title = self.generate_title(raw_content, topic)
        logger.info(f"Generated title: {title}")
        
        # Process each chunk
        all_sections = []
        all_markers = []
        section_counter = 1
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i + 1}/{len(chunks)} ({len(chunk)} chars)")
            
            # Build chunk-specific prompt
            prompt = self._build_chunk_prompt(
                chunk=chunk,
                chunk_index=i,
                total_chunks=len(chunks),
                content_type=content_type,
                topic=topic,
                section_start=section_counter,
                outline=outline,
            )
            
            try:
                generated_text = self._call_llm(prompt, max_tokens, step="content_generate")
                chunk_markdown, chunk_sections, chunk_markers = self._parse_chunk_response(
                    generated_text,
                    topic=topic,
                    outline=outline,
                    include_title=i == 0,
                    marker_start=len(all_markers),
                )
                all_markers.extend(chunk_markers)
                section_counter += len(chunk_sections)
                if i > 0:
                    chunk_markdown = re.sub(r'^#\s+.+\n+', '', chunk_markdown)
                all_sections.append(chunk_markdown.strip())
                
            except Exception as e:
                logger.error(f"Failed to process chunk {i + 1}: {e}")
                # Add fallback content for this chunk
                all_sections.append(f"## Section {section_counter}\n\n{self._clean_content(chunk[:2000])}")
                section_counter += 1
        
        # Merge all sections
        merged_content = self._merge_sections(all_sections, title)
        
        # Extract final sections list
        final_sections = re.findall(r'^##\s+(.+)$', merged_content, re.MULTILINE)
        
        logger.info(f"Merged content: {len(merged_content)} chars, {len(all_markers)} visual markers, {len(final_sections)} sections")
        
        return GeneratedContent(
            markdown=merged_content,
            visual_markers=all_markers,
            title=title,
            sections=final_sections,
            outline=outline,
        )
    
    def _split_into_chunks(self, content: str, max_chunk_size: int = 10000) -> list[str]:
        """
        Split content into chunks at natural boundaries.
        
        Tries to split at:
        1. Section headers in transcript (timestamps with topic names)
        2. Double newlines (paragraph breaks)
        3. Single newlines (if necessary)
        
        Args:
            content: Raw content to split
            max_chunk_size: Maximum characters per chunk
            
        Returns:
            List of content chunks
        Invoked by: src/doc_generator/infrastructure/llm/content_generator.py
        """
        # First, try to identify major section breaks
        # Look for patterns like "Topic Name\n0:00" or standalone section headers
        section_pattern = r'\n([A-Z][A-Za-z\s,]+)\n(\d{1,2}:\d{2}(?::\d{2})?)\n'
        
        # Find all section boundaries
        boundaries = [0]
        for match in re.finditer(section_pattern, content):
            boundaries.append(match.start())
        boundaries.append(len(content))
        
        # Create initial sections based on natural boundaries
        initial_sections = []
        for i in range(len(boundaries) - 1):
            section = content[boundaries[i]:boundaries[i + 1]].strip()
            if section:
                initial_sections.append(section)
        
        # If no natural sections found, split by paragraph
        if len(initial_sections) <= 1:
            initial_sections = content.split('\n\n')
        
        # Now merge small sections and split large ones to meet size requirements
        chunks = []
        current_chunk = ""
        
        for section in initial_sections:
            # If adding this section would exceed max size
            if len(current_chunk) + len(section) > max_chunk_size:
                # Save current chunk if it has content
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                
                # If section itself is too large, split it
                if len(section) > max_chunk_size:
                    # Split by newlines
                    lines = section.split('\n')
                    current_chunk = ""
                    for line in lines:
                        if len(current_chunk) + len(line) > max_chunk_size:
                            if current_chunk.strip():
                                chunks.append(current_chunk.strip())
                            current_chunk = line + '\n'
                        else:
                            current_chunk += line + '\n'
                else:
                    current_chunk = section + '\n\n'
            else:
                current_chunk += section + '\n\n'
        
        # Don't forget the last chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks if chunks else [content]
    
    def generate_title(self, content: str, topic_hint: str = "") -> str:
        """
        Generate a professional, descriptive title for the content.
        
        Args:
            content: Full content (uses first 3000 chars for analysis)
            topic_hint: Optional hint about the topic
            
        Returns:
            Generated title string
        Invoked by: src/doc_generator/infrastructure/llm/content_generator.py
        """
        if not self.is_available():
            return topic_hint.replace("-", " ").replace("_", " ").title() if topic_hint else "Document"
        
        prompt = build_title_prompt(content, topic_hint)

        try:
            self._record_usage(step="content_title")
            if self.content_provider == "gemini":
                start_time = time.perf_counter()
                prompt_text = prompt
                response = self.content_client.models.generate_content(
                    model=self.content_model,
                    contents=prompt_text
                )
                title = (response.text or "").strip()
                self._record_call_details(start_time, response, step="content_title")
                duration_ms = int((time.perf_counter() - start_time) * 1000)
                usage = getattr(response, "usage_metadata", None)
                input_tokens = getattr(usage, "prompt_token_count", None) if usage else None
                output_tokens = getattr(usage, "candidates_token_count", None) if usage else None
                log_llm_call(
                    name="content_title",
                    prompt=prompt_text,
                    response=title,
                    provider=self.content_provider,
                    model=self.content_model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    duration_ms=duration_ms,
                )
            elif self.content_provider == "claude":
                start_time = time.perf_counter()
                response = self.content_client.messages.create(
                    model=self.content_model,
                    max_tokens=100,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}]
                )
                title = response.content[0].text.strip()
                self._record_call_details(start_time, response, step="content_title")
                duration_ms = int((time.perf_counter() - start_time) * 1000)
                log_llm_call(
                    name="content_title",
                    prompt=prompt,
                    response=title,
                    provider=self.content_provider,
                    model=self.content_model,
                    duration_ms=duration_ms,
                )
            else:  # OpenAI
                start_time = time.perf_counter()
                response = self.content_client.chat.completions.create(
                    model=self.content_model,
                    max_completion_tokens=100,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}]
                )
                title = response.choices[0].message.content.strip()
                self._record_call_details(start_time, response, step="content_title")
                duration_ms = int((time.perf_counter() - start_time) * 1000)
                usage = getattr(response, "usage", None)
                input_tokens = getattr(usage, "prompt_tokens", None) if usage else None
                output_tokens = getattr(usage, "completion_tokens", None) if usage else None
                log_llm_call(
                    name="content_title",
                    prompt=prompt,
                    response=title,
                    provider=self.content_provider,
                    model=self.content_model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    duration_ms=duration_ms,
                )

            # Clean up title (remove quotes if present)
            title = title.strip('"\'')
            return title

        except Exception as e:
            logger.error(f"Failed to generate title: {e}")
            return topic_hint.replace("-", " ").replace("_", " ").title() if topic_hint else "Document"

    def generate_blog_outline(
        self,
        raw_content: str,
        content_type: str,
        topic: str,
        max_tokens: int = 1200,
    ) -> str:
        """
        Generate a blog outline from raw content.
        Invoked by: src/doc_generator/infrastructure/llm/content_generator.py
        """
        if not self.is_available():
            return ""

        prompt = self._build_outline_prompt(raw_content, content_type, topic)

        try:
            outline = self._call_llm(prompt, max_tokens, step="content_outline")
            return outline.strip()
        except Exception as e:
            logger.error(f"Failed to generate outline: {e}")
            return ""

    def _call_llm(self, prompt: str, max_tokens: int, step: str = "content_generate") -> str:
        """
        Make an LLM API call for content generation.
        Invoked by: src/doc_generator/infrastructure/llm/content_generator.py, src/doc_generator/infrastructure/llm/service.py
        """
        self._record_usage(step=step)
        if self.content_provider == "gemini":
            return self._call_llm_gemini(prompt, step=step)
        if self.content_provider == "claude":
            return self._call_llm_claude(prompt, max_tokens=max_tokens, step=step)
        return self._call_llm_openai(prompt, max_tokens=max_tokens, step=step)

    def _call_llm_gemini(self, prompt: str, step: str) -> str:
        """
        Call Gemini for content generation.
        Invoked by: src/doc_generator/infrastructure/llm/content_generator.py
        """
        start_time = time.perf_counter()
        full_prompt = f"{self._get_system_prompt()}\n\n{prompt}"
        response = self.content_client.models.generate_content(
            model=self.content_model,
            contents=full_prompt
        )
        self._record_call_details(start_time, response, step=step)
        response_text = (response.text or "").strip()
        self._log_llm_call(step, full_prompt, response_text, start_time, response)
        return response_text

    def _call_llm_claude(self, prompt: str, max_tokens: int, step: str) -> str:
        """
        Call Claude for content generation.
        Invoked by: src/doc_generator/infrastructure/llm/content_generator.py
        """
        start_time = time.perf_counter()
        response = self.content_client.messages.create(
            model=self.content_model,
            max_tokens=max_tokens,
            temperature=self.settings.llm.content_temperature,
            system=self._get_system_prompt(),
            messages=[{"role": "user", "content": prompt}]
        )
        self._record_call_details(start_time, response, step=step)
        response_text = response.content[0].text
        self._log_llm_call(step, f"{self._get_system_prompt()}\n\n{prompt}", response_text, start_time, response)
        return response_text

    def _call_llm_openai(self, prompt: str, max_tokens: int, step: str) -> str:
        """
        Call OpenAI for content generation.
        Invoked by: src/doc_generator/infrastructure/llm/content_generator.py
        """
        start_time = time.perf_counter()
        response = self.content_client.chat.completions.create(
            model=self.content_model,
            max_completion_tokens=max_tokens,
            temperature=self.settings.llm.content_temperature,
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ]
        )
        self._record_call_details(start_time, response, step=step)
        response_text = response.choices[0].message.content
        self._log_llm_call(step, f"{self._get_system_prompt()}\n\n{prompt}", response_text, start_time, response)
        return response_text

    def _log_llm_call(
        self,
        step: str,
        prompt: str,
        response_text: str,
        start_time: float,
        response,
    ) -> None:
        """
        Log an LLM call with best-effort token usage.
        Invoked by: src/doc_generator/infrastructure/llm/content_generator.py
        """
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        usage_metadata = getattr(response, "usage_metadata", None)
        usage = getattr(response, "usage", None)
        input_tokens = None
        output_tokens = None
        if usage_metadata:
            input_tokens = getattr(usage_metadata, "prompt_token_count", None)
            output_tokens = getattr(usage_metadata, "candidates_token_count", None)
        if usage:
            input_tokens = getattr(usage, "prompt_tokens", input_tokens)
            output_tokens = getattr(usage, "completion_tokens", output_tokens)
        log_llm_call(
            name=step,
            prompt=prompt,
            response=response_text,
            provider=self.content_provider,
            model=self.content_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_ms=duration_ms,
        )

    def _record_usage(self, step: str) -> None:
        """
        Invoked by: src/doc_generator/infrastructure/llm/content_generator.py
        """
        LLMContentGenerator._total_calls += 1
        if self.content_model:
            LLMContentGenerator._models_used.add(self.content_model)
        if self.content_provider:
            LLMContentGenerator._providers_used.add(self.content_provider)
        logger.opt(colors=True).info(
            "<cyan>LLM call</cyan> provider={} model={}",
            self.content_provider,
            self.content_model
        )

    def _record_call_details(self, start_time: float, response, step: str) -> None:
        """
        Invoked by: src/doc_generator/infrastructure/llm/content_generator.py
        """
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        input_tokens = None
        output_tokens = None

        if response is not None:
            usage = getattr(response, "usage_metadata", None)
            if usage:
                input_tokens = getattr(usage, "prompt_token_count", None)
                output_tokens = getattr(usage, "candidates_token_count", None)
            usage = getattr(response, "usage", None)
            if usage:
                input_tokens = getattr(usage, "prompt_tokens", input_tokens)
                output_tokens = getattr(usage, "completion_tokens", output_tokens)

        LLMContentGenerator._call_details.append({
            "kind": "llm",
            "step": step,
            "provider": self.content_provider,
            "model": self.content_model,
            "duration_ms": duration_ms,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        })

    @classmethod
    def usage_summary(cls) -> dict:
        """
        Invoked by: src/doc_generator/application/graph_workflow.py, src/doc_generator/application/workflow/graph.py
        """
        return {
            "total_calls": cls._total_calls,
            "models": sorted(cls._models_used),
            "providers": sorted(cls._providers_used),
        }

    @classmethod
    def usage_details(cls) -> list[dict]:
        """
        Invoked by: src/doc_generator/application/graph_workflow.py, src/doc_generator/application/workflow/graph.py
        """
        return list(cls._call_details)
    
    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for content generation.
        Invoked by: src/doc_generator/infrastructure/llm/content_generator.py
        """
        return get_content_system_prompt()
    
    def _build_generation_prompt(self, content: str, content_type: str, topic: str, is_chunk: bool = False) -> str:
        """
        Build the prompt for single content generation.
        Invoked by: src/doc_generator/infrastructure/llm/content_generator.py
        """
        return build_generation_prompt(content, content_type, topic, is_chunk=is_chunk)

    def _build_outline_prompt(self, content: str, content_type: str, topic: str) -> str:
        """
        Build the prompt for outline generation.
        Invoked by: src/doc_generator/infrastructure/llm/content_generator.py
        """
        return build_outline_prompt(content, content_type, topic)

    def _build_blog_from_outline_prompt(
        self,
        content: str,
        content_type: str,
        topic: str,
        outline: str,
    ) -> str:
        """
        Build the prompt for blog generation using an outline.
        Invoked by: src/doc_generator/infrastructure/llm/content_generator.py
        """
        return build_blog_from_outline_prompt(content, content_type, topic, outline)
    
    def _build_chunk_prompt(
        self,
        chunk: str,
        chunk_index: int,
        total_chunks: int,
        content_type: str,
        topic: str,
        section_start: int,
        outline: str = ""
    ) -> str:
        """
        Build prompt for processing a content chunk.
        Invoked by: src/doc_generator/infrastructure/llm/content_generator.py
        """
        return build_chunk_prompt(
            chunk=chunk,
            chunk_index=chunk_index,
            total_chunks=total_chunks,
            content_type=content_type,
            topic=topic,
            section_start=section_start,
            outline=outline,
        )

    def _safe_json_load(self, text: str) -> Optional[object]:
        """
        Best-effort JSON extraction from an LLM response.
        Invoked by: src/doc_generator/infrastructure/llm/content_generator.py
        """
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        start_idx = None
        for i, ch in enumerate(text):
            if ch in "{[":
                start_idx = i
                break
        if start_idx is None:
            return None

        stack = []
        for i in range(start_idx, len(text)):
            ch = text[i]
            if ch in "{[":
                stack.append(ch)
            elif ch in "}]":
                if not stack:
                    continue
                stack.pop()
                if not stack:
                    candidate = text[start_idx:i + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        return None
        return None

    def _normalize_heading(self, heading: str, level: int) -> str:
        """
        Normalize a heading into markdown at the given level.
        Invoked by: src/doc_generator/infrastructure/llm/content_generator.py
        """
        if not heading:
            heading = "Section"
        heading = heading.strip()
        heading = re.sub(r"^#+\s*", "", heading)
        return f"{'#' * level} {heading}"

    def _json_to_markdown(self, data: dict, topic: str, include_title: bool = True) -> tuple[str, str, list[str]]:
        """
        Convert a JSON response into markdown.
        Invoked by: src/doc_generator/infrastructure/llm/content_generator.py
        """
        title = (data or {}).get("title") or topic or "Document"
        intro = (data or {}).get("introduction") or ""
        key_takeaways = (data or {}).get("key_takeaways") or ""
        sections = (data or {}).get("sections") or []
        body_parts = []

        if include_title:
            body_parts.append(f"# {title}".strip())
        if intro:
            body_parts.append(self._normalize_heading("Introduction", 2))
            body_parts.append(intro.strip())

        section_titles = []
        for section in sections:
            if isinstance(section, str):
                heading = section
                content = ""
                subsections = []
            else:
                heading = section.get("heading") or section.get("title") or ""
                content = section.get("content") or ""
                subsections = section.get("subsections") or []

            if heading:
                section_titles.append(re.sub(r"^#+\s*", "", heading).strip())
                body_parts.append(self._normalize_heading(heading, 2))
            if content:
                body_parts.append(content.strip())

            for subsection in subsections:
                if isinstance(subsection, str):
                    sub_heading = subsection
                    sub_content = ""
                else:
                    sub_heading = subsection.get("heading") or subsection.get("title") or ""
                    sub_content = subsection.get("content") or ""
                if sub_heading:
                    body_parts.append(self._normalize_heading(sub_heading, 3))
                if sub_content:
                    body_parts.append(sub_content.strip())

        if key_takeaways:
            body_parts.append(self._normalize_heading("Key Takeaways", 2))
            body_parts.append(key_takeaways.strip())

        markdown = "\n\n".join([part for part in body_parts if part])
        return markdown.strip(), title, section_titles

    def _parse_chunk_response(
        self,
        text: str,
        topic: str,
        outline: str,
        include_title: bool,
        marker_start: int,
    ) -> tuple[str, list[str], list[VisualMarker]]:
        """
        Parse a chunk response into markdown and markers.
        Invoked by: src/doc_generator/infrastructure/llm/content_generator.py
        """
        if self.settings.llm.content_json_mode:
            data = self._safe_json_load(text)
            if isinstance(data, dict):
                markdown, title, sections = self._json_to_markdown(
                    data,
                    topic=topic,
                    include_title=include_title,
                )
                markers = self._extract_visual_markers(markdown, marker_start)
                if include_title and title:
                    return markdown, sections, markers
                return markdown, sections, markers

        # Fallback to markdown parsing
        markers = self._extract_visual_markers(text, marker_start)
        sections = re.findall(r'^##\s+(.+)$', text, re.MULTILINE)
        return text, sections, markers
    
    def _extract_visual_markers(self, text: str, start_index: int = 0) -> list[VisualMarker]:
        """
        Extract visual markers from generated text.
        Invoked by: src/doc_generator/infrastructure/llm/content_generator.py
        """
        markers = []
        marker_pattern = r'\[VISUAL:(\w+):([^:]+):([^\]]+)\]'
        
        # Map invalid types to valid ones
        type_mapping = {
            "diagram": "architecture",
            "chart": "comparison",
            "graph": "flowchart",
            "table": "comparison",
            "heatmap": "comparison",
        }
        valid_types = {"architecture", "flowchart", "comparison", "concept_map", "mind_map", "mermaid"}
        
        for i, match in enumerate(re.finditer(marker_pattern, text)):
            visual_type = match.group(1).lower()
            
            # Map to valid type if needed
            if visual_type not in valid_types:
                visual_type = type_mapping.get(visual_type, "architecture")
                logger.debug(f"Mapped visual type '{match.group(1)}' to '{visual_type}'")
            
            marker = VisualMarker(
                marker_id=f"visual_{start_index + i}",
                visual_type=visual_type,
                title=match.group(2).strip(),
                description=match.group(3).strip(),
                position=match.start()
            )
            markers.append(marker)
            logger.debug(f"Found visual marker: {marker.visual_type} - {marker.title}")
        
        return markers
    
    def _merge_sections(self, sections: list[str], title: str) -> str:
        """
        Merge processed sections into a cohesive document.
        Invoked by: src/doc_generator/infrastructure/llm/content_generator.py
        """
        
        # Start with the first section (which should have title and intro)
        merged = sections[0] if sections else ""
        
        # Add remaining sections with proper spacing
        for section in sections[1:]:
            merged += "\n\n" + section
        
        # Ensure document starts with proper title
        if not merged.startswith("#"):
            merged = f"# {title}\n\n{merged}"
        
        # Clean up multiple consecutive newlines
        merged = re.sub(r'\n{4,}', '\n\n\n', merged)
        
        return merged
    
    def _clean_content(self, content: str) -> str:
        """
        Basic content cleaning without LLM.
        Invoked by: src/doc_generator/infrastructure/llm/content_generator.py
        """
        # Remove timestamps
        cleaned = re.sub(r'^\d{1,2}:\d{2}(:\d{2})?\s*$', '', content, flags=re.MULTILINE)
        cleaned = re.sub(r'\n\d{1,2}:\d{2}(:\d{2})?\n', '\n', cleaned)
        # Remove excessive blank lines
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        return cleaned.strip()
    
    def _parse_generated_content(self, text: str, topic: str, outline: str = "") -> GeneratedContent:
        """
        Parse generated text to extract markdown and visual markers.
        Invoked by: src/doc_generator/infrastructure/llm/content_generator.py
        """
        if self.settings.llm.content_json_mode:
            data = self._safe_json_load(text)
            if isinstance(data, dict):
                markdown, title, sections = self._json_to_markdown(
                    data,
                    topic=topic,
                    include_title=True,
                )
                visual_markers = self._extract_visual_markers(markdown)
                logger.info(
                    f"Generated content: {len(markdown)} chars, "
                    f"{len(visual_markers)} visual markers, {len(sections)} sections"
                )
                return GeneratedContent(
                    markdown=markdown,
                    visual_markers=visual_markers,
                    title=title,
                    sections=sections,
                    outline=outline,
                )

        visual_markers = self._extract_visual_markers(text)
        title_match = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else topic or "Document"
        sections = re.findall(r'^##\s+(.+)$', text, re.MULTILINE)
        logger.info(f"Generated content: {len(text)} chars, {len(visual_markers)} visual markers, {len(sections)} sections")
        return GeneratedContent(
            markdown=text,
            visual_markers=visual_markers,
            title=title,
            sections=sections,
            outline=outline,
        )
    
    def _fallback_generation(self, raw_content: str, topic: str) -> GeneratedContent:
        """
        Fallback when LLM is not available - basic cleanup.
        Invoked by: src/doc_generator/infrastructure/llm/content_generator.py
        """
        
        cleaned = self._clean_content(raw_content)
        
        # Add title if topic provided
        title = topic.replace("-", " ").replace("_", " ").title() if topic else "Document"
        if not cleaned.startswith("#"):
            cleaned = f"# {title}\n\n{cleaned}"
        
        return GeneratedContent(
            markdown=cleaned,
            visual_markers=[],
            title=title,
            sections=[],
            outline="",
        )

    def _extract_title_from_outline(self, outline: str, fallback: str) -> str:
        """
        Extract title from outline heading if present.
        Invoked by: src/doc_generator/infrastructure/llm/content_generator.py
        """
        if not outline:
            return fallback
        match = re.search(r'^#\s+(.+)$', outline, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return fallback

def get_content_generator(api_key: Optional[str] = None) -> LLMContentGenerator:
    """
    Get or create content generator instance.
    
    Args:
        api_key: Optional API key
        
    Returns:
        LLMContentGenerator instance
    Invoked by: src/doc_generator/application/nodes/transform_content.py, src/doc_generator/application/workflow/nodes/transform_content.py, src/doc_generator/utils/content_merger.py
    """
    return LLMContentGenerator(api_key=api_key)
