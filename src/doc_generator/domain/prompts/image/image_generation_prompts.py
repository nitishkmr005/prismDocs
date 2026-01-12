"""
Prompt templates for image generation and evaluation.
"""

from ...content_types import ImageType


def build_gemini_image_prompt(image_type: ImageType, prompt: str, size_hint: str) -> str:
    """
    Build Gemini image generation prompt with size hints.
    """
    if image_type == ImageType.INFOGRAPHIC:
        return f"""Create a vibrant, educational infographic that explains: {prompt}

Style requirements:
- Clean, modern infographic design
- Use clear icons only when they represent actual concepts
- Include clear labels and annotations
- Use a professional color palette (blues, teals, oranges)
- Make it suitable for inclusion in a professional document
- No text-heavy design - focus on visual explanation
- High contrast for readability when printed
- Use ONLY the concepts in the prompt; do not add new information
- Avoid metaphorical objects (pipes, ropes, factories) unless explicitly mentioned
- For workflows/architectures, use flat rounded rectangles + arrows in a clean grid
{size_hint}"""

    if image_type == ImageType.DECORATIVE:
        return f"""Create a professional, thematic header image for: {prompt}

Style requirements:
- Abstract or semi-abstract design
- Professional and modern aesthetic
- Subtle and elegant - not distracting
- Use muted, professional colors
- Suitable as a section header in a document
- Wide aspect ratio (16:9 or similar)
- No text in the image
- Use ONLY the concepts in the prompt; do not add new information
{size_hint}"""

    if image_type == ImageType.MERMAID:
        return f"""Create a professional, clean flowchart/diagram image that represents: {prompt}

Style requirements:
- Clean, modern diagram design with clear flow
- Use boxes, arrows, and connections to show relationships
- Professional color scheme (blues, grays, with accent colors)
- Include clear labels for each step/component
- Make it suitable for inclusion in a corporate document
- High contrast for readability when printed
- No watermarks or decorative elements
- Focus on clarity and visual hierarchy
- Use ONLY the concepts in the prompt; do not add new information
{size_hint}"""

    return prompt


def build_image_description_prompt(section_title: str, content: str) -> str:
    """
    Prompt to describe an image based on section content.
    """
    return (
        "Write a concise blog-style description of this image. "
        "Use only what is visible and what is supported by the section content. "
        "Keep it to 2-4 sentences.\n\n"
        f"Section Title: {section_title}\n\n"
        f"Section Content:\n{content[:2000]}"
    )


def build_prompt_generator_prompt(
    section_title: str,
    content_preview: str,
) -> str:
    """
    Prompt to generate a content-specific image prompt.
    """
    prompt = "Decide whether this section needs an image.\n\n"
    prompt += f"Section Title: {section_title}\n"
    prompt += f"Section Content:\n{content_preview}\n\n"
    prompt += "Rules:\n"
    prompt += "- If an image is NOT needed, return exactly: none\n"
    prompt += "- If an image IS needed, return a single concise image prompt.\n"
    prompt += "- Use ONLY concepts present in the content.\n"
    prompt += "- Do NOT add new facts, tools, or labels.\n"
    prompt += "- The prompt should describe what to depict clearly.\n"
    return prompt
