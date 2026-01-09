"""
LLM-powered content generator for transforming raw documents into structured blog content.

Transforms raw transcripts, documents, and slides into well-structured educational
content with visual markers for diagram generation. Supports chunked processing
for long documents.
"""

import json
import re
from dataclasses import dataclass, field
from typing import Optional

from loguru import logger

from .settings import get_settings

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
    data: dict = field(default_factory=dict)  # Structured data for generation


@dataclass
class GeneratedContent:
    """Result of LLM content generation."""
    
    markdown: str  # The generated blog-style markdown
    visual_markers: list[VisualMarker]  # Extracted visual markers
    title: str
    sections: list[str]  # Section headings for TOC


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
    
    # Section markers to split content on
    SECTION_MARKERS = [
        r'^Introduction\s*$',
        r'^Recap\s',
        r'^Overview\s',
        r'^[A-Z][a-z]+\s+[A-Z][a-z]+\s*$',  # Two word section titles
        r'^\d{1,2}:\d{2}\s*$',  # Timestamps as section breaks
    ]
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the content generator with separate clients for content and visuals.
        
        - Content generation: Uses OpenAI GPT-4o (better structured output)
        - Visual data generation: Uses Claude (better reasoning for diagrams)
        
        Args:
            api_key: API key override. If not provided, uses env vars.
        """
        import os
        
        self.settings = get_settings()
        self.claude_api_key = api_key or os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
        self.openai_api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        # Content generation client (prefer OpenAI GPT-4o)
        self.content_client = None
        self.content_provider = None
        self.content_model = None
        
        # Visual data client (prefer Claude)
        self.visual_client = None
        self.visual_provider = None
        self.visual_model = None
        
        # Setup content generation client (OpenAI preferred)
        if self.openai_api_key and OPENAI_AVAILABLE:
            self.content_client = OpenAI(api_key=self.openai_api_key)
            self.content_provider = "openai"
            self.content_model = self.settings.llm.content_model
            logger.info(f"Content Generator initialized with OpenAI: {self.content_model}")
        elif self.claude_api_key and ANTHROPIC_AVAILABLE:
            self.content_client = Anthropic(api_key=self.claude_api_key)
            self.content_provider = "claude"
            self.content_model = self.settings.llm.svg_model
            logger.info(f"Content Generator initialized with Claude (fallback): {self.content_model}")
        else:
            logger.warning("No API key available for content generation")
        
        # Setup visual data client (Claude preferred)
        if self.claude_api_key and ANTHROPIC_AVAILABLE:
            self.visual_client = Anthropic(api_key=self.claude_api_key)
            self.visual_provider = "claude"
            self.visual_model = self.settings.llm.svg_model
            logger.debug(f"Visual data client using Claude: {self.visual_model}")
        elif self.openai_api_key and OPENAI_AVAILABLE:
            self.visual_client = OpenAI(api_key=self.openai_api_key)
            self.visual_provider = "openai"
            self.visual_model = self.settings.llm.content_model
            logger.debug(f"Visual data client using OpenAI (fallback): {self.visual_model}")
        
        # Legacy compatibility
        self.client = self.content_client
        self.provider = self.content_provider
        self.model = self.content_model
    
    def is_available(self) -> bool:
        """Check if LLM content generation is available."""
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
        """
        if not self.is_available():
            logger.warning("LLM not available, returning cleaned raw content")
            return self._fallback_generation(raw_content, topic)
        
        content_length = len(raw_content)
        logger.info(f"Processing {content_length} characters of {content_type} content")
        
        # For short content, process directly
        if content_length <= 12000:
            return self._process_single_chunk(raw_content, content_type, topic, max_tokens)
        
        # For long content, use chunked processing
        logger.info(f"Content too long ({content_length} chars), using chunked processing")
        return self._process_chunked(raw_content, content_type, topic, max_tokens)
    
    def _process_single_chunk(
        self,
        content: str,
        content_type: str,
        topic: str,
        max_tokens: int
    ) -> GeneratedContent:
        """Process a single chunk of content."""
        prompt = self._build_generation_prompt(content, content_type, topic, is_chunk=False)
        
        try:
            generated_text = self._call_llm(prompt, max_tokens)
            return self._parse_generated_content(generated_text, topic)
        except Exception as e:
            logger.error(f"LLM content generation failed: {e}")
            return self._fallback_generation(content, topic)
    
    def _process_chunked(
        self,
        raw_content: str,
        content_type: str,
        topic: str,
        max_tokens: int
    ) -> GeneratedContent:
        """Process long content in chunks and merge results."""
        
        # Split content into manageable chunks
        chunks = self._split_into_chunks(raw_content, max_chunk_size=10000)
        logger.info(f"Split content into {len(chunks)} chunks")
        
        # First, generate a title based on content overview
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
                section_start=section_counter
            )
            
            try:
                generated_text = self._call_llm(prompt, max_tokens)
                
                # Parse visual markers from this chunk
                chunk_markers = self._extract_visual_markers(generated_text, len(all_markers))
                all_markers.extend(chunk_markers)
                
                # Extract sections for counting
                chunk_sections = re.findall(r'^##\s+\d+\.\s+(.+)$', generated_text, re.MULTILINE)
                section_counter += len(chunk_sections)
                
                # Clean the generated text (remove title if present in non-first chunk)
                if i > 0:
                    generated_text = re.sub(r'^#\s+.+\n+', '', generated_text)
                
                all_sections.append(generated_text.strip())
                
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
            sections=final_sections
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
        """
        if not self.is_available():
            return topic_hint.replace("-", " ").replace("_", " ").title() if topic_hint else "Document"
        
        prompt = f"""Based on this educational content, generate a professional blog post title.

The title should:
- Be descriptive and engaging (5-10 words)
- Follow pattern: "Main Topic: Descriptive Subtitle" 
- NOT include course names, lecture numbers, or file names
- Capture the main educational theme

Content preview:
{content[:4000]}

Topic hint: {topic_hint if topic_hint else "Not provided"}

Return ONLY the title, nothing else. No quotes, no explanation."""

        try:
            if self.content_provider == "claude":
                response = self.content_client.messages.create(
                    model=self.content_model,
                    max_tokens=100,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}]
                )
                title = response.content[0].text.strip()
            else:  # OpenAI
                response = self.content_client.chat.completions.create(
                    model=self.content_model,
                    max_completion_tokens=100,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}]
                )
                title = response.choices[0].message.content.strip()

            # Clean up title (remove quotes if present)
            title = title.strip('"\'')
            return title

        except Exception as e:
            logger.error(f"Failed to generate title: {e}")
            return topic_hint.replace("-", " ").replace("_", " ").title() if topic_hint else "Document"

    def _call_llm(self, prompt: str, max_tokens: int) -> str:
        """Make an LLM API call for content generation."""
        if self.content_provider == "claude":
            response = self.content_client.messages.create(
                model=self.content_model,
                max_tokens=max_tokens,
                temperature=self.settings.llm.content_temperature,
                system=self._get_system_prompt(),
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        else:  # OpenAI
            response = self.content_client.chat.completions.create(
                model=self.content_model,
                max_completion_tokens=max_tokens,
                temperature=self.settings.llm.content_temperature,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for content generation."""
        return """You are an expert technical writer who transforms raw educational content 
(like lecture transcripts, slides, and documents) into polished, comprehensive blog posts.

Your writing style:
- Clear, professional, and suitable for technical audiences
- Educational with detailed explanations
- Well-organized with numbered sections (1., 1.1, etc.)
- Rich with examples, comparisons, and visual references

Your expertise:
- Removing timestamps, filler words, and conversational artifacts
- Organizing content into logical numbered sections
- Expanding brief points into full explanations
- Identifying where diagrams would clarify concepts
- Creating comprehensive coverage of all topics mentioned

Output format:
- Use ## for main sections with numbers (## 1. Section Name)
- Use ### for subsections with numbers (### 1.1 Subsection)
- Write full paragraphs, not bullet points
- Include visual markers where helpful
- Preserve ALL technical content - do not skip topics"""
    
    def _build_generation_prompt(self, content: str, content_type: str, topic: str, is_chunk: bool = False) -> str:
        """Build the prompt for single content generation."""
        
        type_instructions = {
            "transcript": "This is a lecture transcript. Remove all timestamps and conversational elements while preserving ALL educational content.",
            "document": "This is a document. Restructure it into a clear blog format with numbered sections.",
            "slides": "These are slide contents. Expand the bullet points into comprehensive explanations.",
            "mixed": "This is mixed content from multiple sources. Combine and structure into a cohesive blog post."
        }
        
        instruction = type_instructions.get(content_type, type_instructions["document"])
        
        return f"""Transform the following content into a comprehensive, well-structured educational blog post.

**Content Type**: {content_type}
**Topic**: {topic or "Detect from content"}
**Special Instructions**: {instruction}

## Requirements

1. **Structure**: 
   - Use numbered sections: ## 1. Section Name, ## 2. Next Section
   - Use numbered subsections: ### 1.1 Subsection Name
   - Start with an introduction paragraph

2. **Content Quality**:
   - Write complete, detailed paragraphs (not bullet points)
   - Explain ALL technical concepts thoroughly
   - Include examples and comparisons where helpful
   - Cover EVERY topic mentioned in the source - do not skip anything
   - Typical section should be 200-400 words

3. **Visual Markers**: Where a diagram would help, insert:
   [VISUAL:type:Title:Brief description]
   
   ONLY use these types: architecture, flowchart, comparison, concept_map, mind_map
   - architecture: for system components and their connections
   - flowchart: for processes and decision flows  
   - comparison: for comparing features/approaches
   - concept_map: for related concepts and relationships
   - mind_map: for hierarchical topic breakdown
   
   Example: [VISUAL:architecture:Transformer Architecture:Show encoder-decoder with attention layers]

4. **Mermaid Diagrams**: For simple concepts, include inline mermaid:
   ```mermaid
   graph LR
       A[Input] --> B[Process] --> C[Output]
   ```

5. **Formatting**:
   - Use **bold** for key terms
   - Use `code` for technical terms
   - End with ## Key Takeaways section

## Raw Content:

{content}

---

Generate the complete blog post. Start with # Title, then ## Introduction, then numbered sections:"""
    
    def _build_chunk_prompt(
        self,
        chunk: str,
        chunk_index: int,
        total_chunks: int,
        content_type: str,
        topic: str,
        section_start: int
    ) -> str:
        """Build prompt for processing a content chunk."""
        
        position = "beginning" if chunk_index == 0 else "middle" if chunk_index < total_chunks - 1 else "end"
        
        context = f"""You are processing part {chunk_index + 1} of {total_chunks} of a {content_type}.
This is the {position} of the document.
Topic: {topic}
Start section numbering from: {section_start}"""
        
        if chunk_index == 0:
            # First chunk - include title and introduction
            return f"""{context}

Transform this content into the BEGINNING of a comprehensive blog post.

Requirements:
- Start with # [Generate appropriate title]
- Include ## Introduction paragraph
- Use numbered sections starting from ## {section_start}. Section Name
- Write detailed paragraphs, not bullet points
- Include [VISUAL:type:title:description] markers where diagrams would help
  (ONLY use types: architecture, flowchart, comparison, concept_map, mind_map)
- Cover ALL topics in this chunk - do not skip anything

Content:

{chunk}

---

Generate the blog post beginning:"""
        
        elif chunk_index == total_chunks - 1:
            # Last chunk - include conclusion
            return f"""{context}

Transform this content into the FINAL sections of a blog post.

Requirements:
- Continue section numbering from {section_start}
- Use numbered sections: ## {section_start}. Section Name
- Write detailed paragraphs
- Include visual markers where helpful
- End with ## Key Takeaways section summarizing main points
- Cover ALL topics in this chunk

Content:

{chunk}

---

Generate the blog post conclusion sections:"""
        
        else:
            # Middle chunk
            return f"""{context}

Transform this content into MIDDLE sections of a blog post.

Requirements:
- Continue section numbering from {section_start}
- Use numbered sections: ## {section_start}. Section Name
- Write detailed paragraphs
- Include visual markers where helpful
- Cover ALL topics in this chunk - do not skip anything

Content:

{chunk}

---

Generate the blog post middle sections:"""
    
    def _extract_visual_markers(self, text: str, start_index: int = 0) -> list[VisualMarker]:
        """Extract visual markers from generated text."""
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
        """Merge processed sections into a cohesive document."""
        
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
        """Basic content cleaning without LLM."""
        # Remove timestamps
        cleaned = re.sub(r'^\d{1,2}:\d{2}(:\d{2})?\s*$', '', content, flags=re.MULTILINE)
        cleaned = re.sub(r'\n\d{1,2}:\d{2}(:\d{2})?\n', '\n', cleaned)
        # Remove excessive blank lines
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        return cleaned.strip()
    
    def _parse_generated_content(self, text: str, topic: str) -> GeneratedContent:
        """Parse generated text to extract markdown and visual markers."""
        
        # Extract visual markers
        visual_markers = self._extract_visual_markers(text)
        
        # Extract title from first heading
        title_match = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else topic or "Document"
        
        # Extract section headings for TOC
        sections = re.findall(r'^##\s+(.+)$', text, re.MULTILINE)
        
        logger.info(f"Generated content: {len(text)} chars, {len(visual_markers)} visual markers, {len(sections)} sections")
        
        return GeneratedContent(
            markdown=text,
            visual_markers=visual_markers,
            title=title,
            sections=sections
        )
    
    def _fallback_generation(self, raw_content: str, topic: str) -> GeneratedContent:
        """Fallback when LLM is not available - basic cleanup."""
        
        cleaned = self._clean_content(raw_content)
        
        # Add title if topic provided
        title = topic.replace("-", " ").replace("_", " ").title() if topic else "Document"
        if not cleaned.startswith("#"):
            cleaned = f"# {title}\n\n{cleaned}"
        
        return GeneratedContent(
            markdown=cleaned,
            visual_markers=[],
            title=title,
            sections=[]
        )
    
    def generate_visual_data(self, marker: VisualMarker, context: str = "") -> dict:
        """
        Generate structured data for a visual marker using Claude (preferred for diagrams).

        Args:
            marker: The visual marker to generate data for
            context: Surrounding content for context

        Returns:
            Structured data dictionary for SVG generation
        """
        # Use visual client (Claude preferred) for diagram data generation
        if self.visual_client is None:
            return {}

        prompt = self._build_visual_data_prompt(marker, context)

        try:
            if self.visual_provider == "claude":
                response = self.visual_client.messages.create(
                    model=self.visual_model,
                    max_tokens=2000,
                    temperature=self.settings.llm.svg_temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
                result = response.content[0].text
            else:  # OpenAI fallback
                response = self.visual_client.chat.completions.create(
                    model=self.visual_model,
                    max_completion_tokens=2000,
                    temperature=self.settings.llm.svg_temperature,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": "You are a diagram data generator. Always respond with valid JSON."},
                        {"role": "user", "content": prompt}
                    ]
                )
                result = response.choices[0].message.content

            # Parse JSON from response
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                result = result.split("```")[1].split("```")[0]

            data = json.loads(result.strip())
            logger.debug(f"Generated visual data for {marker.title}: {list(data.keys())}")
            return data

        except Exception as e:
            logger.error(f"Failed to generate visual data for {marker.title}: {e}")
            return {}
    
    def _build_visual_data_prompt(self, marker: VisualMarker, context: str) -> str:
        """Build prompt for generating visual data."""
        
        data_formats = {
            "architecture": """{
  "components": [{"id": "1", "name": "Component Name", "layer": "frontend|backend|database|external"}],
  "connections": [{"from": "1", "to": "2", "label": "connection type"}]
}""",
            "flowchart": """{
  "nodes": [{"id": "1", "type": "start|end|process|decision", "text": "Node text"}],
  "edges": [{"from": "1", "to": "2", "label": "optional label"}]
}""",
            "comparison": """{
  "items": ["Option A", "Option B"],
  "categories": [{"name": "Category", "scores": [8, 6]}]
}""",
            "concept_map": """{
  "concepts": [{"id": "1", "text": "Concept", "level": 0}],
  "relationships": [{"from": "1", "to": "2", "label": "relates to"}]
}""",
            "mind_map": """{
  "central": "Main Topic",
  "branches": [{"text": "Branch 1", "children": ["Sub 1.1", "Sub 1.2"]}]
}"""
        }
        
        format_example = data_formats.get(marker.visual_type, data_formats["flowchart"])
        
        return f"""Generate structured data for a {marker.visual_type} diagram.

**Title**: {marker.title}
**Description**: {marker.description}
**Context**: {context[:500] if context else "No additional context"}

Generate JSON data in this format:
{format_example}

Requirements:
- Keep text labels SHORT (max 20 characters) to prevent overlap
- Include 4-8 elements for clarity
- Make connections logical based on the description
- Use clear, concise names

Respond with ONLY valid JSON, no explanations:"""


def get_content_generator(api_key: Optional[str] = None) -> LLMContentGenerator:
    """
    Get or create content generator instance.
    
    Args:
        api_key: Optional API key
        
    Returns:
        LLMContentGenerator instance
    """
    return LLMContentGenerator(api_key=api_key)
