# Gemini Image Generation Design

## Overview

Add image generation capability to the document generator using Google's Gemini API, with auto-detection to choose the best image type (infographic, decorative, diagram) for each section.

## Requirements

1. **Image Types**: Support three types of images per section:
   - Illustrative infographics (Gemini) - explains concepts visually
   - Decorative headers (Gemini) - thematic mood-setting images
   - Data visualizations (existing SVG/Mermaid) - technical diagrams

2. **Auto-Detection**: LLM analyzes each section and picks the best image type automatically

3. **Gemini Model**: `gemini-3-pro-image-preview`

4. **Rate Limiting**: 20 images/minute (3 second delay between requests)

5. **Storage**:
   - PDF: Embed images inline (base64/direct)
   - PPTX: Reference external files from `src/output/images/`

6. **Full Document Support**: Leverage existing chunking mechanism - no truncation

## Configuration Schema

```python
class ImageGenerationSettings(BaseSettings):
    """Image generation settings."""

    # Provider selection
    default_provider: str = "auto"  # "auto", "gemini", "svg", "mermaid"

    # Gemini settings
    gemini_model: str = "gemini-3-pro-image-preview"
    gemini_rate_limit: int = 20  # images per minute
    gemini_request_delay: float = 3.0  # seconds between requests

    # Image storage
    images_dir: Path = Path("src/output/images")
    embed_in_pdf: bool = True
    embed_in_pptx: bool = False

    # Auto-detection options
    enable_decorative_headers: bool = True
    enable_infographics: bool = True
    enable_diagrams: bool = True
```

## Image Type Enum

```python
class ImageType(Enum):
    INFOGRAPHIC = "infographic"      # Gemini - explains concepts visually
    DECORATIVE = "decorative"        # Gemini - thematic header image
    DIAGRAM = "diagram"              # SVG - architecture, flowcharts
    CHART = "chart"                  # SVG - data comparisons
    MERMAID = "mermaid"              # Mermaid - sequence diagrams, flows
    NONE = "none"                    # Skip image for this section
```

## Auto-Detection Logic

The LLM analyzes each section and returns an image type decision:

```python
# Detection prompt (sent to content LLM)
"""
Analyze this section and decide the best image type:

Section Title: {title}
Content: {content_preview}

Choose ONE:
- "infographic": Complex concept that benefits from illustrated explanation
- "decorative": Section intro/conclusion that needs mood-setting imagery
- "diagram": Technical architecture, system components, relationships
- "chart": Data comparison, metrics, feature matrices
- "mermaid": Sequential processes, state machines, timelines
- "none": Simple text that doesn't need visualization

Return JSON: {"image_type": "...", "prompt": "description for image generation"}
"""
```

## Gemini Image Generator

```python
# src/doc_generator/infrastructure/gemini_image_generator.py

class GeminiImageGenerator:
    """Generate images using Gemini API with rate limiting."""

    def __init__(self):
        self.client = genai.Client()
        self.settings = get_settings().image_generation
        self._last_request_time = 0
        self._request_count = 0
        self._minute_start = time.time()

    def _wait_for_rate_limit(self):
        """Ensure we don't exceed 20 requests/minute."""
        now = time.time()

        # Reset counter every minute
        if now - self._minute_start >= 60:
            self._request_count = 0
            self._minute_start = now

        # If at limit, wait for next minute
        if self._request_count >= self.settings.gemini_rate_limit:
            sleep_time = 60 - (now - self._minute_start)
            time.sleep(sleep_time)
            self._request_count = 0
            self._minute_start = time.time()

        # Minimum delay between requests
        elapsed = now - self._last_request_time
        if elapsed < self.settings.gemini_request_delay:
            time.sleep(self.settings.gemini_request_delay - elapsed)

    def generate_image(
        self,
        prompt: str,
        image_type: ImageType,
        section_title: str,
        output_path: Path
    ) -> Optional[Path]:
        """Generate image with rate limiting."""
        self._wait_for_rate_limit()

        # Enhance prompt based on image type
        enhanced_prompt = self._enhance_prompt(prompt, image_type)

        chat = self.client.chats.create(
            model=self.settings.gemini_model,
            config=types.GenerateContentConfig(
                response_modalities=['IMAGE']
            )
        )

        response = chat.send_message(enhanced_prompt)

        for part in response.parts:
            if image := part.as_image():
                image.save(str(output_path))
                self._last_request_time = time.time()
                self._request_count += 1
                return output_path

        return None
```

## Workflow Integration

### Updated Flow

```
Current:
  Detect → Parse → Transform → Generate Visuals → Generate Output → Validate

Updated:
  Detect → Parse → Transform → Generate Visuals → Generate Images → Generate Output → Validate
                                    ↓                    ↓
                              (SVG/Mermaid)         (Gemini)
```

### Generate Images Node

```python
def generate_images_node(state: WorkflowState) -> WorkflowState:
    """Generate images for all sections using auto-detection."""

    structured_content = state.get("structured_content", {})
    markdown = structured_content.get("markdown", "")

    # Parse sections from markdown (preserves full content)
    section_contents = _extract_section_contents(markdown)

    # Initialize generators
    gemini_gen = GeminiImageGenerator()  # Rate-limited
    svg_gen = get_svg_generator()

    images = {}

    for section_id, section in enumerate(section_contents):
        # Auto-detect best image type for this section
        image_decision = _detect_image_type(section["title"], section["content"])

        if image_decision.image_type == ImageType.NONE:
            continue

        # Generate based on type
        if image_decision.image_type in (ImageType.INFOGRAPHIC, ImageType.DECORATIVE):
            # Gemini - respects rate limit internally
            image_path = gemini_gen.generate_image(
                prompt=image_decision.prompt,
                image_type=image_decision.image_type,
                section_title=section["title"],
                output_path=images_dir / f"section_{section_id}.png"
            )
        elif image_decision.image_type in (ImageType.DIAGRAM, ImageType.CHART):
            # Existing SVG flow
            image_path = svg_gen.generate(...)
        elif image_decision.image_type == ImageType.MERMAID:
            # Existing mermaid flow
            image_path = render_mermaid(...)

        if image_path:
            images[section_id] = {
                "path": image_path,
                "type": image_decision.image_type,
                "embed_base64": _encode_if_needed(image_path)  # For PDF
            }

    structured_content["section_images"] = images
    state["structured_content"] = structured_content
    return state
```

## File Structure

### New Files

```
src/doc_generator/
├── domain/
│   └── models.py                    # Add ImageType enum
├── infrastructure/
│   ├── gemini_image_generator.py    # NEW - Gemini API with rate limiting
│   └── settings.py                  # Add ImageGenerationSettings
├── application/
│   └── nodes/
│       ├── generate_images.py       # NEW - Image generation node
│       └── generate_visuals.py      # Update to coordinate with images
└── config/
    └── prompts/
        └── image_prompts.py         # NEW - Auto-detection prompts
```

### Modified Files

- `src/doc_generator/infrastructure/settings.py` - Add ImageGenerationSettings
- `src/doc_generator/domain/models.py` - Add ImageType enum
- `src/doc_generator/application/graph_workflow.py` - Add generate_images node
- `src/doc_generator/application/generators/pdf_generator.py` - Embed images inline
- `src/doc_generator/application/generators/pptx_generator.py` - Reference external images

## PDF Embedding

```python
# In pdf_generator.py - embed directly
from reportlab.lib.utils import ImageReader

def _embed_section_image(self, image_info: dict, story: list):
    """Embed image inline in PDF."""
    image_path = Path(image_info["path"])
    if image_path.exists():
        story.append(Spacer(1, 12))
        story.extend(make_image_flowable(
            image_info.get("title", ""),
            image_path,
            self.styles
        ))
        story.append(Spacer(1, 12))
```

## PPTX Referencing

```python
# In pptx_generator.py - reference external file
def _add_section_image(self, slide, image_info: dict):
    """Add image to slide from external file."""
    image_path = Path(image_info["path"])
    if image_path.exists():
        slide.shapes.add_picture(
            str(image_path),
            left=Inches(0.5),
            top=Inches(1.5),
            width=Inches(9),
            height=Inches(5)
        )
```

## Summary Table

| Feature | Implementation |
|---------|----------------|
| **Image types** | Infographic, Decorative (Gemini), Diagram/Chart (SVG), Mermaid |
| **Selection** | Auto-detect via LLM per section |
| **Gemini model** | `gemini-3-pro-image-preview` |
| **Rate limiting** | 20/min with 3s delay between requests |
| **PDF** | Embed images inline (base64/direct) |
| **PPTX** | Reference external files from `src/output/images/` |
| **Full docs** | Leverages existing chunking - no truncation |

## Implementation Order

1. Add `ImageType` enum to `domain/models.py`
2. Add `ImageGenerationSettings` to `infrastructure/settings.py`
3. Create `infrastructure/gemini_image_generator.py` with rate limiting
4. Create `config/prompts/image_prompts.py` for auto-detection
5. Create `application/nodes/generate_images.py` node
6. Update `application/graph_workflow.py` to include new node
7. Update `pdf_generator.py` to embed section images
8. Update `pptx_generator.py` to reference section images
9. Test end-to-end with sample document
