# Building a Document Generator: From Raw Inputs to Polished PDF and PPTX

*How a LangGraph workflow turns messy inputs into publish-ready documents with visuals that match the content*

---

## Why This Exists

Teams accumulate content everywhere: PDFs, slide decks, docs, markdown, and web pages. Turning that sprawl into a consistent, professional document usually means hours of manual cleaning, rewriting, and layout work.

This system automates that end-to-end flow. It ingests mixed sources, structures them into a coherent narrative, generates supporting visuals, and renders a final PDF or PPTX with consistent formatting. The goal is not just conversion; it is **editorial-quality synthesis with visual support**.

---

## What the Pipeline Produces

For every run, the generator creates:

- **A clean, well-structured blog-style document** with sections, subsections, and clear flow.
- **Section-aligned visuals** tailored to each section (architecture blocks, comparisons, flowcharts, study notes).
- **A final output** in either PDF or PPTX with consistent themes, typography, and layout.

The outputs are usable as:
- Internal documentation
- Presentations for stakeholders
- Executive summaries
- Training materials

---

## System Overview

At a high level, the workflow looks like this:

```
Detect format → Parse content → Transform content → Generate images → Generate output → Validate
```

Each step is a **LangGraph node** with a single responsibility. The workflow carries a shared state forward, allowing retries and flexible branching without losing context.

### Architecture Diagram (Node Names)

```
detect_format
        ↓
parse_content
        ↓
transform_content
        ↓
generate_images
        ↓
generate_output
        ↓
validate_output
```

These are the exact node names in the workflow graph, mapped one-to-one to the document lifecycle.

[VISUAL:architecture:Workflow Graph:Show detect_format → parse_content → transform_content → generate_images → generate_output → validate_output]

---

## Step 1: Detect the Input Format

The pipeline determines how to handle each source based on its format:

- File extensions (`.pdf`, `.pptx`, `.docx`, `.md`, `.txt`)
- URLs for web content
- Inline text

This classification ensures the right parser is used and prevents content loss early in the process.

---

## Step 2: Parse and Normalize Content

Parsing is where raw data becomes usable text. The system uses dedicated tools per format:

- **Docling** for PDF, DOCX, PPTX, and images (OCR, layouts, tables)
- **MarkItDown** for HTML and web pages
- **Markdown parser** for `.md` and `.txt` (frontmatter-aware)

The parser also attaches metadata (title, URL, source file) and computes a `content_hash` for caching. The output of this stage is normalized markdown-like text with as much structure preserved as possible.

[VISUAL:architecture:Parsing Stack:Show inputs (PDF/DOCX/PPTX, URL, Markdown/Text) feeding Docling and MarkItDown into normalized markdown]

---

## Step 3: Transform Content Into a Blog-Style Narrative

This is the heart of the system. The LLM reorganizes and rewrites the raw content into a clean, readable blog with:

- A generated title
- A short introduction
- Numbered sections with logical flow
- Subsections where needed
- A final key takeaways section

**Important rule**: the transformed content must use **only information present in the source**. No invented facts, no external knowledge, no inferred details. The transformation improves readability, structure, and flow without changing meaning.

This step also inserts **visual markers** in places where an inline diagram would help a reader understand the content (these markers are preserved in the markdown and can be rendered into SVGs if the visualization node is enabled).

Example:
```
[VISUAL:architecture:System Overview:Show ingestion, transformation, and rendering stages]
```

[VISUAL:flowchart:Content Structuring:Raw content → LLM structuring → numbered sections → visual markers]

Under the hood:
- **LLMContentGenerator** handles the main rewrite, with chunked processing for long inputs.
- The content model is provider-driven (Gemini by default, configurable to OpenAI/Claude).
- **LLMService** optionally generates an executive summary, slide structure, and chart suggestions from the transformed markdown.

---

## Step 4: Generate Section Images That Match the Content

The system scans each `##` section and decides whether a visual would improve comprehension. If yes, it generates a prompt grounded in the **actual section content** and chooses a style.

Supported styles (mapped to infographic-style images):

- **Architecture diagrams** (systems, components, data flow)
- **Flowcharts** (processes, decision logic)
- **Comparison visuals** (trade-offs, feature differences)
- **Concept maps** (relationships between ideas)
- **Handwritten notes** (study-guide style explanations)

The prompts are **strictly content-bound**: no extra concepts beyond what appears in the section. Required labels are extracted from the section text (e.g., node names like `parse_content`, `generate_output`, and tools like Docling, ReportLab, python-pptx). This keeps visuals accurate and aligned with the narrative.

Images are generated via the Gemini image API with rate limiting, stored per document under `output/<file_id>/images`, and reused when the `content_hash` matches.

[VISUAL:flowchart:Image Generation Loop:Section text → concept extraction → prompt → Gemini image → cached output]

---

## How Images Stay Aligned With Content

Alignment is deterministic:

- Images are generated per `##` section from that section's text.
- The renderers walk the markdown in order and insert the section image immediately after each `##` banner (PDF) or as a section image slide (PPTX).
- Because the prompt is content-bound and the placement is order-bound, images stay anchored to the narrative instead of floating to unrelated pages.

---

## Step 5: Render the Final Output

### PDF Output

PDFs are rendered with ReportLab for full layout control:

- Consistent typography and spacing
- Section hierarchy and headings
- Inline images and captions
- Code blocks and tables
- Clean margins and palettes

Section images are inserted immediately after each `##` header banner, which keeps visuals in lockstep with the content sequence.

### PPTX Output

PPTX generation uses python-pptx:

- Title slide
- One slide per major section
- Visuals embedded on relevant slides
- Consistent theme and layout

When LLM enhancements are present, the generator uses the LLM-proposed slide structure and attaches section images as dedicated image slides or as part of the section flow.

Both formats are designed to be client-ready with minimal manual editing.

[VISUAL:comparison:Output Rendering:ReportLab → PDF vs python-pptx → PPTX]

---

## Step 6: Validate and Retry When Needed

The pipeline validates the output before finalizing:

- Output file exists
- File size is non-zero
- Basic readability checks

If validation fails, the system retries output generation up to three times. This prevents partial or corrupted documents from being returned.

[VISUAL:flowchart:Validation Gate:Generate output → validate_output → pass/fail retry (max 3)]

---

## Mini Example: From Raw Snippet to Visualized Output

**Input snippet (raw):**
```
We ingest PDFs and web pages, normalize them into markdown, then use an LLM to structure the content.
After that we generate section images and render PDF/PPTX outputs.
```

**Transformed section (blog style):**
```
## 2. Content Normalization and Structuring
The pipeline begins by ingesting PDFs and web pages and normalizing them into markdown. This
standardized representation makes it possible to apply consistent transformations. An LLM then
structures the content into logical sections with clear flow, preparing it for visuals and final
rendering.
```

**Visual marker injected by the transformer:**
```
[VISUAL:architecture:Generation Pipeline:Show ingest → normalize → transform → generate images → render output]
```

**Final output (screenshot placeholders):**

- PDF screenshot: _replace with a real PDF export image_
- PPTX screenshot: _replace with a real slide export image_

---

## Performance & Cost Notes

- **Typical runtimes**: 60–120 seconds for multi-source inputs, depending on document length and image count.
- **Cache savings**: When content is unchanged, image generation is skipped, reducing runtime and API cost.
- **Image generation limits**: Gemini image generation is rate-limited (default 20 images/min with request delay).
- **Best practice**: Keep sections focused to reduce image count and keep slides concise.

---

## Why This Workflow Works

**1) Clean separation of responsibilities**
Each node does one job, making the pipeline easier to test, debug, and evolve.

**2) Content fidelity**
The LLM improves structure and readability without inventing content. This preserves trust and accuracy.

**3) Visuals that explain, not decorate**
Images are generated to support understanding. They are always derived from the exact section content.

**4) Multi-format output without duplication**
A single workflow produces both PDF and PPTX without maintaining separate pipelines.

**5) Image alignment is deterministic**
Images are keyed to section order and embedded immediately after each `##` header, so visuals stay anchored to the narrative.

---

## A Quick Example

Input sources:

- A PDF research paper
- A markdown design doc
- A web article

Output:

- A single blog-style PDF with a clean narrative
- Five section images (architecture, comparison, flowchart, concept map, handwritten notes)
- A PPTX deck using the same structured content

Total time: minutes, not hours.

---

## Closing Thoughts

This generator is more than a file converter. It is a **content transformation workflow** designed to turn messy inputs into structured, visual, presentation-ready documents. By combining parsing, LLM-based organization, and tightly scoped image generation, it produces outputs that feel authored rather than assembled.

If your team produces or collects large volumes of content, this pipeline turns that sprawl into a consistent, professional narrative in a repeatable way.

---

## How to Call the FastAPI Service

### 1) Upload a source file
```bash
curl -sS -X POST http://localhost:8000/api/upload \
  -F "file=@/path/to/input.pdf"
```
Response:
```json
{"file_id":"f_abc123","filename":"input.pdf","size":12345,"mime_type":"application/pdf","expires_in":3600}
```

### 2) Generate PDF or PPTX (SSE stream)
```bash
curl -N -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -H "X-Google-Key: $GEMINI_API_KEY" \
  -d '{
    "output_format": "pdf",
    "provider": "gemini",
    "model": "gemini-3-pro-preview",
    "image_model": "gemini-3-pro-image-preview",
    "sources": [
      {"type": "file", "file_id": "f_abc123"},
      {"type": "url", "url": "https://example.com/article"},
      {"type": "text", "content": "Raw text to include"}
    ],
    "cache": {"reuse": true}
  }'
```
For PPTX, set `"output_format": "pptx"`.

The stream ends with a `complete` (or `cache_hit`) event that includes:
```json
{"download_url":"/api/download/f_abc123/pdf/your-file.pdf?token=...","file_path":"f_abc123/pdf/your-file.pdf"}
```

### 3) Download the generated file
```bash
curl -L -o output.pdf "http://localhost:8000/api/download/f_abc123/pdf/your-file.pdf"
```
You can also use the `download_url` directly if you want the tokenized link.
