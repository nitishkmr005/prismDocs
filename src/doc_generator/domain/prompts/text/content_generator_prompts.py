"""
Prompt templates for LLM content generation.
"""


def get_content_system_prompt() -> str:
    """
    System prompt for content generation.
    """
    return """You are an expert technical writer who transforms raw educational content 
(like lecture transcripts, slides, and documents) into polished, comprehensive blog posts.

Hard constraints:
- Use ONLY the provided content; do not add new facts, examples, metrics, or external context
- Do not guess or fill gaps with invented details
- If a detail is missing in the source, omit it

Your writing style:
- Clear, professional, and suitable for technical audiences
- Educational with detailed explanations
- Well-organized with numbered sections (1., 1.1, etc.)
- Use examples/comparisons only when they appear in the source

Your expertise:
- Removing timestamps, filler words, and conversational artifacts
- Organizing content into logical numbered sections
- Expanding brief points using only the source information
- Identifying where diagrams would clarify concepts
- Creating comprehensive coverage of all topics mentioned

Output format:
- Respond with valid JSON only (no extra text)
- Follow the JSON schema in the user prompt
- Preserve ALL technical content - do not skip topics"""


def build_generation_prompt(content: str, content_type: str, topic: str, is_chunk: bool = False) -> str:
    """
    Prompt for single-pass content generation.
    """
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
   - Include examples and comparisons only if present in the source
   - Cover EVERY topic mentioned in the source - do not skip anything
   - Typical section should be 200-400 words

3. **Source Fidelity**:
   - Use ONLY information present in the raw content
   - Do not add new facts, examples, metrics, or external context
   - Do not infer missing details; omit if not provided

4. **Visual Markers**: Where a diagram would help, insert:
   [VISUAL:type:Title:Brief description]
   
   ONLY use these types: architecture, flowchart, comparison, concept_map, mind_map
   - architecture: for system components and their connections
   - flowchart: for processes and decision flows  
   - comparison: for comparing features/approaches
   - concept_map: for related concepts and relationships
   - mind_map: for hierarchical topic breakdown
   
   Example: [VISUAL:architecture:Transformer Architecture:Show encoder-decoder with attention layers]

5. **Mermaid Diagrams**: For simple concepts, include inline mermaid:
   ```mermaid
   graph LR
       A[Input] --> B[Process] --> C[Output]
   ```

6. **Formatting**:
   - Use **bold** for key terms
   - Use `code` for technical terms
   - End with ## Key Takeaways section

## Output JSON Schema
Return JSON in this shape (string values may include markdown like **bold**, `code`, and mermaid blocks):
{{
  "title": "Title of the blog post",
  "introduction": "Introduction paragraph(s). Do not include a heading.",
  "sections": [
    {{
      "heading": "1. Section Name",
      "content": "Paragraphs for this section. May include inline [VISUAL:...] markers and mermaid blocks.",
      "subsections": [
        {{
          "heading": "1.1 Subsection Name",
          "content": "Paragraphs for this subsection."
        }}
      ]
    }}
  ],
  "key_takeaways": "Summary paragraph(s). Do not include a heading."
}}

## Raw Content:

{content}

---

Return ONLY the JSON object. No surrounding commentary."""


def build_outline_prompt(content: str, content_type: str, topic: str) -> str:
    """
    Prompt for outline generation.
    """
    type_instructions = {
        "transcript": "This is a lecture transcript. Remove timestamps and preserve the educational structure.",
        "document": "This is a document. Extract the logical section structure.",
        "slides": "These are slide contents. Derive a narrative outline from the bullet points.",
        "mixed": "This is mixed content from multiple sources. Combine into a cohesive outline."
    }
    instruction = type_instructions.get(content_type, type_instructions["document"])

    return f"""Create a blog outline from the content below.

**Content Type**: {content_type}
**Topic**: {topic or "Detect from content"}
**Special Instructions**: {instruction}

Requirements:
1. Use ONLY information present in the content. Do not add new topics or facts.
2. Return markdown in this exact structure:
   # Title
   ## Outline
   1. Section Title
      1.1 Subsection Title
      1.2 Subsection Title
   2. Next Section Title
3. Include an Introduction section and a Key Takeaways section in the outline.
4. Use short, clear titles (3-8 words).

Content:
{content}

Return ONLY the outline in markdown. No commentary."""


def build_blog_from_outline_prompt(
    content: str,
    content_type: str,
    topic: str,
    outline: str,
) -> str:
    """
    Prompt for blog generation using an outline.
    """
    type_instructions = {
        "transcript": "This is a lecture transcript. Remove all timestamps and conversational elements while preserving ALL educational content.",
        "document": "This is a document. Restructure it into a clear blog format with numbered sections.",
        "slides": "These are slide contents. Expand the bullet points into comprehensive explanations.",
        "mixed": "This is mixed content from multiple sources. Combine and structure into a cohesive blog post."
    }
    instruction = type_instructions.get(content_type, type_instructions["document"])

    return f"""Use the outline below to write the full blog post.

**Content Type**: {content_type}
**Topic**: {topic or "Detect from content"}
**Special Instructions**: {instruction}

## Outline
{outline}

## Requirements

1. **Structure**:
   - Follow the outline structure and section titles exactly.
   - Use numbered sections: ## 1. Section Name, ## 2. Next Section
   - Use numbered subsections: ### 1.1 Subsection Name
   - Start with an introduction paragraph

2. **Content Quality**:
   - Write complete, detailed paragraphs (not bullet points)
   - Explain ALL technical concepts thoroughly
   - Include examples and comparisons only if present in the source
   - Cover EVERY topic mentioned in the source - do not skip anything

3. **Source Fidelity**:
   - Use ONLY information present in the raw content
   - Do not add new facts, examples, metrics, or external context
   - Do not infer missing details; omit if not provided

4. **Visual Markers**: Where a diagram would help, insert:
   [VISUAL:type:Title:Brief description]
   ONLY use these types: architecture, flowchart, comparison, concept_map, mind_map

5. **Mermaid Diagrams**: For simple concepts, include inline mermaid:
   ```mermaid
   graph LR
       A[Input] --> B[Process] --> C[Output]
   ```

6. **Formatting**:
   - Use **bold** for key terms
   - Use `code` for technical terms
   - End with ## Key Takeaways section

## Output JSON Schema
Return JSON in this shape (string values may include markdown like **bold**, `code`, and mermaid blocks):
{{
  "title": "Title of the blog post",
  "introduction": "Introduction paragraph(s). Do not include a heading.",
  "sections": [
    {{
      "heading": "1. Section Name",
      "content": "Paragraphs for this section. May include inline [VISUAL:...] markers and mermaid blocks.",
      "subsections": [
        {{
          "heading": "1.1 Subsection Name",
          "content": "Paragraphs for this subsection."
        }}
      ]
    }}
  ],
  "key_takeaways": "Summary paragraph(s). Do not include a heading."
}}

## Raw Content:

{content}

---

Return ONLY the JSON object. No surrounding commentary."""


def build_chunk_prompt(
    chunk: str,
    chunk_index: int,
    total_chunks: int,
    content_type: str,
    topic: str,
    section_start: int,
    outline: str = "",
) -> str:
    """
    Prompt for processing a content chunk.
    """
    position = "beginning" if chunk_index == 0 else "middle" if chunk_index < total_chunks - 1 else "end"
    outline_block = f"\nOutline:\n{outline}\n" if outline else ""
    context = (
        f"You are processing part {chunk_index + 1} of {total_chunks} of a {content_type}.\n"
        f"This is the {position} of the document.\n"
        f"Topic: {topic}\n"
        f"Start section numbering from: {section_start}\n"
        f"Use the outline to keep section titles consistent; only write sections supported by this chunk."
        f"{outline_block}"
    )

    if chunk_index == 0:
        return f"""{context}

Transform this content into the BEGINNING of a comprehensive blog post.

Requirements:
- Use numbered sections starting from ## {section_start}. Section Name
- Write detailed paragraphs, not bullet points
- Include [VISUAL:type:title:description] markers where diagrams would help
  (ONLY use types: architecture, flowchart, comparison, concept_map, mind_map)
- Cover ALL topics in this chunk - do not skip anything
- Use ONLY information in this chunk; do not add new details

Output JSON Schema:
{{
  "title": "Title of the blog post",
  "introduction": "Introduction paragraph(s). Do not include a heading.",
  "sections": [
    {{
      "heading": "{section_start}. Section Name",
      "content": "Paragraphs for this section. May include inline [VISUAL:...] markers and mermaid blocks.",
      "subsections": [
        {{
          "heading": "{section_start}.1 Subsection Name",
          "content": "Paragraphs for this subsection."
        }}
      ]
    }}
  ],
  "key_takeaways": ""
}}

Content:

{chunk}

---

Return ONLY the JSON object. No commentary."""

    if chunk_index == total_chunks - 1:
        return f"""{context}

Transform this content into the FINAL sections of a blog post.

Requirements:
- Continue section numbering from {section_start}
- Use numbered sections: ## {section_start}. Section Name
- Write detailed paragraphs
- Include visual markers where helpful
- End with ## Key Takeaways section summarizing main points
- Cover ALL topics in this chunk
- Use ONLY information in this chunk; do not add new details

Output JSON Schema:
{{
  "title": "",
  "introduction": "",
  "sections": [
    {{
      "heading": "{section_start}. Section Name",
      "content": "Paragraphs for this section. May include inline [VISUAL:...] markers and mermaid blocks.",
      "subsections": []
    }}
  ],
  "key_takeaways": "Summary paragraph(s). Do not include a heading."
}}

Content:

{chunk}

---

Return ONLY the JSON object. No commentary."""

    return f"""{context}

Transform this content into MIDDLE sections of a blog post.

Requirements:
- Continue section numbering from {section_start}
- Use numbered sections: ## {section_start}. Section Name
- Write detailed paragraphs
- Include visual markers where helpful
- Cover ALL topics in this chunk - do not skip anything
- Use ONLY information in this chunk; do not add new details

Output JSON Schema:
{{
  "title": "",
  "introduction": "",
  "sections": [
    {{
      "heading": "{section_start}. Section Name",
      "content": "Paragraphs for this section. May include inline [VISUAL:...] markers and mermaid blocks.",
      "subsections": []
    }}
  ],
  "key_takeaways": ""
}}

Content:

{chunk}

---

Return ONLY the JSON object. No commentary."""


def build_title_prompt(content: str, topic_hint: str) -> str:
    """
    Prompt for title generation.
    """
    return f"""Based on this educational content, generate a professional blog post title.

The title should:
- Be descriptive and engaging (5-10 words)
- Follow pattern: "Main Topic: Descriptive Subtitle" 
- NOT include course names, lecture numbers, or file names
- Capture the main educational theme
- Use ONLY topics and terms that appear in the content (no new topics)

Content preview:
{content[:4000]}

Topic hint: {topic_hint if topic_hint else "Not provided"}

Return ONLY the title, nothing else. No quotes, no explanation."""
