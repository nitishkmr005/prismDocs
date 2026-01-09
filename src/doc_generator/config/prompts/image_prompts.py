"""
Prompts for image type auto-detection.

These prompts are used by the LLM to analyze section content and decide
what type of image would best illustrate the section.
"""

# System prompt for image type detection
IMAGE_DETECTION_SYSTEM_PROMPT = """You are an expert visual designer who analyzes document sections
and recommends the best type of visual illustration for each section.

Your goal is to enhance reader understanding by suggesting images that:
- Clarify complex concepts through visual explanation
- Set appropriate mood/tone for section introductions
- Visualize data, processes, and relationships
- Know when NO image is needed (simple text sections)

You always respond with valid JSON."""


# Main detection prompt template
IMAGE_DETECTION_PROMPT = """Analyze this section and decide the best image type to help readers understand the content.

## Section Information
**Title:** {section_title}
**Content Preview:** {content_preview}

## Available Image Types

1. **infographic** - Use when:
   - Complex concept that benefits from visual explanation
   - Process or system that can be illustrated
   - Multiple related ideas that connect visually
   - Technical content that's easier to understand visually
   - Example: "How neural networks work", "The software development lifecycle"

2. **decorative** - Use when:
   - Section introduction or overview that needs mood-setting
   - Abstract topic that benefits from thematic imagery
   - Conclusion or summary sections
   - Example: "Introduction to Machine Learning", "Conclusion and Next Steps"

3. **diagram** - Use when:
   - System architecture with components and connections
   - Technical relationships between entities
   - Software or infrastructure design
   - Example: "Database schema", "API architecture"

4. **chart** - Use when:
   - Data comparison or metrics
   - Feature comparison between options
   - Statistical information
   - Example: "Performance benchmarks", "Feature comparison"

5. **mermaid** - Use when:
   - Sequential process or workflow
   - State machines or decision trees
   - Timeline or sequence diagram
   - Example: "User authentication flow", "Order processing steps"

6. **none** - Use when:
   - Simple explanatory text
   - Already has visual markers/diagrams
   - Short transitional section
   - Content is self-explanatory

## Response Format
Return ONLY valid JSON with no additional text:
{{
    "image_type": "infographic|decorative|diagram|chart|mermaid|none",
    "prompt": "Detailed description for generating the image - be specific about what to show",
    "confidence": 0.0 to 1.0
}}

## Examples

Section: "Introduction to Kubernetes"
Content: "Kubernetes is an open-source container orchestration platform..."
Response: {{
  "image_type": "decorative",
  "prompt": "Modern abstract visualization of cloud infrastructure with interconnected nodes",
  "confidence": 0.85
}}

Section: "How Attention Mechanisms Work"
Content: "The attention mechanism allows the model to focus on relevant parts..."
Response: {{
  "image_type": "infographic",
  "prompt": "Educational infographic showing attention in transformers with Q, K, V matrices",
  "confidence": 0.95
}}

Section: "Setting Up Your Environment"
Content: "First, install Python 3.11. Then run pip install..."
Response: {{"image_type": "none", "prompt": "", "confidence": 0.90}}

Now analyze the provided section and respond with JSON only:"""


# Prompt for generating image description from section content
IMAGE_DESCRIPTION_PROMPT = """Based on the section content, create a detailed image generation prompt.

Section Title: {section_title}
Image Type: {image_type}
Content Summary: {content_summary}

Create a prompt that will generate an image that:
1. Directly relates to the section content
2. Helps readers understand the key concepts
3. Is professional and suitable for a document
4. Has appropriate visual style for the image type

Return ONLY the image generation prompt, nothing else."""


# Fallback prompts for each image type when detection fails
FALLBACK_PROMPTS = {
    "infographic": "Educational infographic explaining {topic} with clear icons and visual flow",
    "decorative": "Professional abstract header image representing {topic} with geometric shapes",
    "diagram": "Technical architecture diagram showing components and relationships for {topic}",
    "chart": "Clean comparison chart visualizing key aspects of {topic}",
    "mermaid": "flowchart TD\n    A[Start] --> B[Process]\n    B --> C[End]",
}
