"""
Prompts for content transformation and blog generation.

These prompts are used by LLMContentGenerator to transform raw documents
(transcripts, slides, PDFs) into structured blog-style markdown.
"""

# System prompt for content generation
CONTENT_SYSTEM_PROMPT = """You are an expert technical writer who transforms raw educational content 
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
- Use ## for main sections with numbers (## 1. Section Name)
- Use ### for subsections with numbers (### 1.1 Subsection)
- Write full paragraphs, not bullet points
- Include visual markers where helpful
- Preserve ALL technical content - do not skip topics"""


# Type-specific instructions for content transformation
TYPE_INSTRUCTIONS = {
    "transcript": "This is a lecture transcript. Remove all timestamps and conversational elements while preserving ALL educational content.",
    "document": "This is a document. Restructure it into a clear blog format with numbered sections.",
    "slides": "These are slide contents. Expand the bullet points into comprehensive explanations.",
    "mixed": "This is mixed content from multiple sources. Combine and structure into a cohesive blog post."
}


# Main content generation prompt template
CONTENT_GENERATION_PROMPT = """Transform the following content into a comprehensive, well-structured educational blog post.

**Content Type**: {content_type}
**Topic**: {topic}
**Special Instructions**: {type_instruction}

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

## Raw Content:

{content}

---

Generate the complete blog post. Start with # Title, then ## Introduction, then numbered sections:"""


# Chunk processing prompt template
CONTENT_CHUNK_PROMPT = """You are processing part {chunk_index} of {total_chunks} of a {content_type}.
This is the {position} of the document.
Topic: {topic}
Start section numbering from: {section_start}

{chunk_instructions}

Content:

{chunk}

---

{output_instructions}"""


# Chunk-specific instructions by position
CHUNK_FIRST_INSTRUCTIONS = """Transform this content into the BEGINNING of a comprehensive blog post.

Requirements:
- Start with # [Generate appropriate title]
- Include ## Introduction paragraph
- Use numbered sections starting from ## {section_start}. Section Name
- Write detailed paragraphs, not bullet points
- Include [VISUAL:type:title:description] markers where diagrams would help
  (ONLY use types: architecture, flowchart, comparison, concept_map, mind_map)
- Cover ALL topics in this chunk - do not skip anything
- Use ONLY information in this chunk; do not add new details"""

CHUNK_MIDDLE_INSTRUCTIONS = """Transform this content into MIDDLE sections of a blog post.

Requirements:
- Continue section numbering from {section_start}
- Use numbered sections: ## {section_start}. Section Name
- Write detailed paragraphs
- Include visual markers where helpful
  (ONLY use types: architecture, flowchart, comparison, concept_map, mind_map)
- Cover ALL topics in this chunk - do not skip anything
- Use ONLY information in this chunk; do not add new details"""

CHUNK_LAST_INSTRUCTIONS = """Transform this content into the FINAL sections of a blog post.

Requirements:
- Continue section numbering from {section_start}
- Use numbered sections: ## {section_start}. Section Name
- Write detailed paragraphs
- Include visual markers where helpful
- End with ## Key Takeaways section summarizing main points
- Cover ALL topics in this chunk
- Use ONLY information in this chunk; do not add new details"""


# Title generation prompt
TITLE_GENERATION_PROMPT = """Based on this educational content, generate a professional blog post title.

The title should:
- Be descriptive and engaging (5-10 words)
- Follow pattern: "Main Topic: Descriptive Subtitle" 
- NOT include course names, lecture numbers, or file names
- Capture the main educational theme
- Use ONLY topics and terms that appear in the content

Content preview:
{content_preview}

Topic hint: {topic_hint}

Return ONLY the title, nothing else. No quotes, no explanation."""
