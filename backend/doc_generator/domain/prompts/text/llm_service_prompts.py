"""
Prompt templates for LLM service operations.
"""


def executive_summary_system_prompt() -> str:
    return "You are an executive communication specialist who creates clear, impactful summaries for senior leadership."


def executive_summary_prompt(content: str, max_points: int) -> str:
    return f"""Analyze the following content and create an executive summary suitable for senior leadership.

Requirements:
- Maximum {max_points} key points
- Focus on strategic insights, outcomes, and business impact
- Use clear, concise language
- Format as bullet points
- Each point should be 1-2 sentences max
- Use ONLY information present in the content; do not add new facts or assumptions

Content:
{content[:8000]}

Respond with ONLY the bullet points, no introduction or conclusion."""


def slide_structure_system_prompt() -> str:
    return "You are a presentation design expert who creates compelling executive presentations. Always respond with valid JSON."


def slide_structure_prompt(content: str, max_slides: int) -> str:
    return f"""Convert the following content into a corporate presentation structure.

Requirements:
- Maximum {max_slides} slides (excluding title slide)
- Each slide should have:
  - A clear, action-oriented title (5-8 words)
  - 3-4 bullet points (concise, 7-10 words max each)
  - Speaker notes (2-3 sentences for context)
- Focus on key messages that matter to senior leadership
- Use professional business language
- Structure for logical flow
 - Ensure bullet points are parallel in structure and style
- Use ONLY information from the content; do not introduce new facts or examples

Content:
{content[:8000]}

Respond in JSON format:
{{
  "slides": [
    {{
      "title": "Slide Title",
      "bullets": ["Point 1", "Point 2", "Point 3"],
      "speaker_notes": "Context for the presenter..."
    }}
  ]
}}"""


def section_slide_structure_system_prompt() -> str:
    return "You are a presentation designer creating concise, slide-ready content. Always respond with valid JSON."


def section_slide_structure_prompt(sections: list[dict], max_slides: int) -> str:
    section_blocks = []
    for idx, section in enumerate(sections[:max_slides], 1):
        title = section.get("title", f"Section {idx}")
        content = section.get("content", "")
        image_hint = section.get("image_hint", "")
        snippet = content[:1200]
        section_blocks.append(
            f"Section {idx}: {title}\n"
            f"Image hint: {image_hint or 'None'}\n"
            f"Content:\n{snippet}\n"
        )

    return f"""Create a presentation outline aligned to the sections below.

Requirements:
- One slide per section (maximum {max_slides})
- Title must match the section title exactly
- 3-4 bullet points per slide, 7-10 words max each
- Bullets should be parallel, action-led, and slide-ready
- Avoid filler phrases and long sentences
- Bullets should align to the section content and image hint
- Provide 1-2 sentence speaker notes per slide
- Use ONLY information from each section; do not add new facts or examples

Sections:
{chr(10).join(section_blocks)}

Respond in JSON format:
{{
  "slides": [
    {{
      "section_title": "Exact Section Title",
      "title": "Exact Section Title",
      "bullets": ["Point 1", "Point 2"],
      "speaker_notes": "Brief speaker notes"
    }}
  ]
}}"""


def enhance_bullets_system_prompt() -> str:
    return "You are an executive communication specialist."


def enhance_bullets_prompt(bullets: list[str]) -> str:
    return f"""Enhance these bullet points for an executive presentation.

Requirements:
- Start each with an action verb or key metric
- Keep each under 12 words
- Make them impactful and clear
- Maintain the original meaning

Bullet points:
{chr(10).join(f'- {b}' for b in bullets)}

Respond with ONLY the enhanced bullet points, one per line, starting with "-"."""


def speaker_notes_system_prompt() -> str:
    return "You are a presentation coach."


def speaker_notes_prompt(slide_title: str, slide_content: list[str]) -> str:
    return f"""Generate speaker notes for this presentation slide.

Slide Title: {slide_title}
Content:
{chr(10).join(f'- {c}' for c in slide_content)}

Requirements:
- 2-3 sentences providing context
- Include key talking points
- Professional tone

Respond with ONLY the speaker notes text."""


def visualization_suggestions_system_prompt() -> str:
    return (
        "You are a visual communication expert who creates clear, informative diagrams. "
        "You identify the best visualization type for each concept and structure data precisely. "
        "Keep all text labels SHORT (under 20 chars) to prevent overlap in diagrams."
    )


def visualization_suggestions_prompt(content: str, max_visuals: int) -> str:
    return f"""Analyze this content and suggest visual diagrams that would help explain key concepts.
Look for:
1. System architectures or component relationships → architecture diagram
2. Step-by-step processes or decision flows → flowchart
3. Comparisons between options/features → comparison_visual
4. Hierarchical concept relationships → concept_map
5. Topic overviews with subtopics → mind_map

Content:
{content[:6000]}

For each visualization opportunity (maximum {max_visuals}), provide structured data.
IMPORTANT: Keep text labels short (max 20 characters) to prevent overlap.

Return JSON with "visualizations" array. Each visualization must have:
- type: "architecture", "flowchart", "comparison_visual", "concept_map", or "mind_map"
- title: Short descriptive title
- data: Type-specific structured data (see formats below)

Data formats:

For architecture:
{{
  "components": [{{"id": "1", "name": "Component Name", "layer": "frontend|backend|database|external|infrastructure"}}],
  "connections": [{{"from": "1", "to": "2", "label": "connection type"}}]
}}

For flowchart:
{{
  "nodes": [{{"id": "1", "type": "start|end|process|decision", "text": "Node text"}}],
  "edges": [{{"from": "1", "to": "2", "label": "optional label"}}]
}}

For comparison_visual:
{{
  "items": ["Option A", "Option B"],
  "categories": [{{"name": "Category", "scores": [8, 6]}}]
}}

For concept_map:
{{
  "concepts": [{{"id": "1", "text": "Concept", "level": 0}}],
  "relationships": [{{"from": "1", "to": "2", "label": "relates to"}}]
}}

For mind_map:
{{
  "central": "Main Topic",
  "branches": [{{"text": "Branch 1", "children": ["Sub 1.1", "Sub 1.2"]}}]
}}

If no good visualization opportunities exist, return {{"visualizations": []}}"""
