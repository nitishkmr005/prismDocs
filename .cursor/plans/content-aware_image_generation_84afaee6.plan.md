---
name: Content-Aware Image Generation
overview: Enhance the image generation pipeline to extract actual concepts from content and generate specific, content-relevant prompts that produce architecture diagrams, comparisons, and educational visualizations instead of generic infographics.
todos:
  - id: add-concept-prompts
    content: Add CONCEPT_EXTRACTION_PROMPT and CONTENT_AWARE_IMAGE_PROMPT to image_prompts.py
    status: completed
  - id: add-extractor-class
    content: Add ConceptExtractor class to generate_images.py that extracts visual concepts from section content
    status: completed
  - id: update-detector
    content: Modify ImageTypeDetector to use concept extraction and generate content-specific prompts
    status: completed
  - id: test-generation
    content: Run generator on Transformers transcript and verify content-relevant images
    status: completed
---

# Content-Aware Image Generation

## Problem Analysis

The current image generation produces **generic infographics** that don't relate to the actual content. For a Transformers lecture, we get generic "learning stages" images instead of:

- Transformer architecture diagrams
- Self-attention Q/K/V visualizations
- Position embedding comparisons (RoPE vs Sinusoidal)
- Multi-head attention variants (MQA/GQA/MHA)

## Root Cause

The issue is in [`image_prompts.py`](src/doc_generator/config/prompts/image_prompts.py):

- `IMAGE_DETECTION_PROMPT` focuses on deciding image **type** not **content**
- `FALLBACK_PROMPTS` use generic templates: `"Educational infographic explaining {topic}"`
- No extraction of key concepts, architectures, or relationships from content

## Solution: Two-Stage Prompt Generation

### Stage 1: Concept Extraction

Add a new prompt that extracts **specific visual concepts** from section content:

```python
CONCEPT_EXTRACTION_PROMPT = """Analyze this technical section and identify concepts that should be visualized.

Section: {section_title}
Content: {content}

Extract:
1. **Architecture concepts**: Systems, components, data flows to diagram
2. **Comparisons**: Features, approaches, or methods being compared
3. **Processes**: Step-by-step procedures or algorithms
4. **Key formulas/equations**: Mathematical concepts to illustrate
5. **Relationships**: How concepts connect to each other

Return JSON with specific visual concepts found in THIS content."""
```

### Stage 2: Content-Specific Prompt Generation

Replace generic prompts with content-extracted specifics:

- **Before**: `"Educational infographic explaining Position Embeddings"`
- **After**: `"Technical diagram showing three position embedding approaches: (1) Learned embeddings with position lookup table, (2) Sinusoidal embeddings with sine/cosine formulas at different frequencies, (3) RoPE rotation matrices applied to Q/K vectors. Show the mathematical formulas and visual representations for each."`

## Files to Modify

### 1. [`src/doc_generator/config/prompts/image_prompts.py`](src/doc_generator/config/prompts/image_prompts.py)

- Add `CONCEPT_EXTRACTION_PROMPT` for extracting visual concepts
- Add `CONTENT_AWARE_IMAGE_PROMPT` template
- Add image style templates for: architecture, comparison, process, handwritten_notes

### 2. [`src/doc_generator/application/nodes/generate_images.py`](src/doc_generator/application/nodes/generate_images.py)

- Add `ConceptExtractor` class to extract visual concepts from content
- Modify `ImageTypeDetector.detect()` to call concept extraction
- Generate **content-specific prompts** using extracted concepts
- Choose image style (architecture/comparison/notes) based on concept type

## Implementation Details

### ConceptExtractor Output Structure

```python
@dataclass
class VisualConcept:
    concept_type: str  # "architecture", "comparison", "process", "formula"
    title: str
    key_elements: list[str]  # Components to show
    relationships: list[str]  # How elements connect
    specific_details: str  # Content-specific details from text
```

### Enhanced ImageDecision

```python
@dataclass
class ImageDecision:
    image_type: ImageType
    prompt: str  # Now content-specific
    concepts: list[VisualConcept]  # Extracted concepts
    style: str  # "architecture_diagram", "comparison_chart", "handwritten_notes"
```

### Example: Transformer Content

For section "Position Embeddings" with content about sinusoidal/RoPE:

- **Extracted concepts**:
                                                                                                                                - type: "comparison"
                                                                                                                                - elements: ["Learned embeddings", "Sinusoidal PE", "RoPE"]  
                                                                                                                                - details: "Sinusoidal uses sin/cos with frequency decay, RoPE rotates Q/K vectors"

- **Generated prompt**:
  ```
  Create a comparison diagram showing three position embedding methods:
  1. LEARNED: Lookup table with position → embedding mapping
  2. SINUSOIDAL: Sine/cosine waves at different frequencies (show formula PE(pos,2i) = sin(pos/10000^(2i/d)))
  3. RoPE: Rotation matrices applied to Q and K vectors
  
  Style: Technical whiteboard diagram with handwritten annotations
  Include: Formulas, vector representations, and key advantages of each
  ```