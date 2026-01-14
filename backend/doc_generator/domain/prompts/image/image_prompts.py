"""
Prompts for image type auto-detection and content-aware image generation.

These prompts are used by the LLM to analyze section content, extract
key visual concepts, and generate content-specific image prompts.
"""

# System prompt for image type detection
IMAGE_DETECTION_SYSTEM_PROMPT = """You are an expert visual designer who analyzes document sections
and recommends the best type of visual illustration for each section.

Your goal is to enhance reader understanding by suggesting images that:
- Clarify complex concepts through visual explanation
- Set appropriate mood/tone for section introductions
- Visualize data, processes, and relationships
- Know when NO image is needed (simple text sections)
- Use ONLY concepts explicitly present in the section content

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
    "prompt": "Detailed description for generating the image - be specific about what to show (only from this section)",
    "confidence": 0.0 to 1.0
}}

Important:
- Use ONLY information present in the section content
- Do NOT add new concepts, entities, or labels
- If the section lacks concrete visuals, choose "none"

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
5. Uses ONLY concepts mentioned in the section (no new ideas)

Return ONLY the image generation prompt, nothing else."""


# Fallback prompts for each image type when detection fails
FALLBACK_PROMPTS = {
    "infographic": "Educational infographic explaining {topic} with clear icons and visual flow",
    "decorative": "Professional abstract header image representing {topic} with geometric shapes",
    "diagram": "Technical architecture diagram showing components and relationships for {topic}",
    "chart": "Clean comparison chart visualizing key aspects of {topic}",
    "mermaid": "flowchart TD\n    A[Start] --> B[Process]\n    B --> C[End]",
}


# =============================================================================
# CONTENT-AWARE IMAGE GENERATION PROMPTS
# =============================================================================

# System prompt for concept extraction
CONCEPT_EXTRACTION_SYSTEM_PROMPT = """You are an expert at analyzing technical content and identifying 
concepts that would benefit from visual illustration.

Your task is to extract SPECIFIC visual concepts from the content - not generic descriptions,
but actual components, relationships, formulas, and comparisons mentioned in the text.

Hard constraint: Use ONLY information explicitly present in the content. Do not infer or invent.

You always respond with valid JSON."""


# Main concept extraction prompt
CONCEPT_EXTRACTION_PROMPT = """Analyze this technical section and identify SPECIFIC concepts that should be visualized.

## Section Information
**Title:** {section_title}
**Content:** {content}

## What to Extract

Identify concepts in THIS SPECIFIC CONTENT that would benefit from visualization:

1. **Architecture concepts**: Systems, components, layers, data flows mentioned
   - Example: "Transformer has encoder and decoder, each with attention layers and FFN"
   
2. **Comparisons**: Features, methods, or approaches being compared
   - Example: "RoPE vs Sinusoidal vs Learned position embeddings"
   
3. **Processes/Algorithms**: Step-by-step procedures or computations
   - Example: "Self-attention: Q*K^T -> softmax -> multiply by V"
   
4. **Mathematical concepts**: Formulas, equations, or calculations to illustrate
   - Example: "Attention(Q,K,V) = softmax(QK^T/sqrt(d_k))V"
   
5. **Hierarchies/Classifications**: Categories, types, or taxonomies
   - Example: "Types of attention: MHA, GQA, MQA"

## Response Format
Return ONLY valid JSON:
{{
    "primary_concept": {{
        "type": "architecture|comparison|process|formula|hierarchy",
        "title": "Specific title for the visual",
        "elements": ["List of specific components/items to show"],
        "relationships": ["How elements connect or relate"],
        "details": "Key technical details from the content to include"
    }},
    "secondary_concepts": [
        {{
            "type": "...",
            "title": "...",
            "elements": ["..."],
            "details": "..."
        }}
    ],
    "recommended_style": "architecture_diagram|comparison_chart|process_flow|formula_illustration|handwritten_notes",
    "key_terms": ["Technical terms that must appear in the visual"]
}}

Important:
- Use ONLY information present in the section content
- Do NOT add new concepts, entities, or labels
- If a concept is not in the text, do not include it

## Examples

For content about "Position embeddings use sine/cosine functions. RoPE rotates Q and K vectors...":
{{
    "primary_concept": {{
        "type": "comparison",
        "title": "Position Embedding Methods",
        "elements": ["Sinusoidal PE", "RoPE", "Learned embeddings"],
        "relationships": ["All encode position info", "Sinusoidal is fixed, RoPE rotates vectors"],
        "details": "Sinusoidal uses PE(pos,2i)=sin(pos/10000^(2i/d)), RoPE applies rotation matrices to Q,K"
    }},
    "secondary_concepts": [],
    "recommended_style": "comparison_chart",
    "key_terms": ["position embedding", "sine", "cosine", "rotation matrix", "Q", "K"]
}}

Now analyze the provided section:"""


# Content-aware image generation prompt
CONTENT_AWARE_IMAGE_PROMPT = """Create a {style} that visualizes:

## Main Concept: {title}

**Elements to include:**
{elements}

**Relationships/Connections:**
{relationships}

**Technical Details:**
{details}

**Key Terms that MUST appear:**
{key_terms}

**Required Labels (verbatim):**
{required_labels}

**Title Requirement:**
The image title text must exactly match: {title}

## Style Requirements for {style}:
{style_requirements}

Generate an image that clearly explains these SPECIFIC concepts from the content.
The image should help readers understand the technical details, not just the general topic.
Do NOT introduce any new concepts or elements beyond the listed items.
Do NOT use metaphorical objects (pipes, ropes, factories) unless explicitly present in the content.
Prefer labeled boxes and arrows for workflows and architectures.
If you include LLM, label it as "LLM" only (no model internals unless explicitly listed)."""


# Style-specific requirements
IMAGE_STYLE_TEMPLATES = {
    "architecture_diagram": """
- Use flat, rounded rectangles for components (no 3D)
- Use arrows to show flow and connections
- Keep layout left-to-right or top-to-bottom
- Use a clean, minimal diagram style (no photos or textures)
- Use a muted teal/orange/gray palette
- Add concise labels inside boxes
- Optional subtle dotted grid background
- Do NOT add domain concepts not in the labels""",

    "comparison_chart": """
- Create a side-by-side or tabular comparison
- List features/characteristics for each item
- Use visual indicators (checkmarks, icons) for differences
- Include brief descriptions under each item
- Highlight key differentiators
- Show formulas or key equations if applicable
- Clean, educational infographic style""",

    "process_flow": """
- Show steps in sequential order with arrows
- Use flat, rounded rectangles for steps
- Use one decision diamond only if explicitly mentioned
- Keep labels short and literal (no metaphors)
- Use a clean, minimal diagram style (no photos or textures)
- Use a muted teal/orange/gray palette
- Optional subtle dotted grid background
- Do NOT add domain concepts not in the labels""",

    "formula_illustration": """
- Show the mathematical formula prominently
- Break down each component with labels
- Use visual representations of variables
- Show example values or dimensions
- Include annotations explaining each term
- Connect formula to visual representation
- Educational math-heavy style with clarity""",

    "handwritten_notes": """
- Whiteboard or notebook paper style
- Hand-drawn looking diagrams and arrows
- Key concepts circled or highlighted
- Annotations and side notes
- Informal but clear labeling
- Mix of text, diagrams, and formulas
- Study notes aesthetic with personal touch""",

    "technical_infographic": """
- Modern infographic design
- Icons representing key concepts
- Clear visual hierarchy
- Numbered steps or sections if applicable
- Key statistics or facts highlighted
- Professional color scheme (blues, teals)
- Balance of visuals and text""",
}
