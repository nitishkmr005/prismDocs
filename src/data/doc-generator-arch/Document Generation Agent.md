# Building a Document Generator: From Raw Inputs to Polished PDF and PPTX

*How a LangGraph workflow turns mixed sources into a single, publish-ready narrative with visuals that are grounded in the content*

---

## Why This Exists

Teams store knowledge in every possible format: PDFs, slide decks, docs, markdown, and web pages. Converting that sprawl into a coherent, professional document usually means hours of manual cleanup and layout work.

This system automates the full path. It ingests multiple sources, normalizes them into a single markdown stream, uses LLMs to structure the story, generates visuals that map to specific sections, and renders a final PDF or PPTX. The result is not a raw conversion; it is **editorial-quality synthesis with visuals that stay aligned to the content**.

---

## System Overview

At a high level, the workflow looks like this:

```
Detect format -> Parse content -> Transform content -> Generate images -> Generate output -> Validate
```

Every step is a **LangGraph node** that mutates a shared state object. That makes retries safe, keeps metadata consistent, and allows the pipeline to stay deterministic across runs.

### LangGraph Node Map (Exact Names)

```
detect_format
        v
parse_content
        v
transform_content
        v
generate_images
        v
generate_output
        v
validate_output
```

[VISUAL:architecture:Workflow Graph:Show detect_format -> parse_content -> transform_content -> generate_images -> validate_images -> generate_output -> validate_output]

---

## Step 1: Detect the Input Format

The workflow begins by identifying how the source should be parsed. Input format is inferred from:

- File extensions (`.pdf`, `.pptx`, `.docx`, `.md`, `.txt`)
- URLs (for web content)
- Inline text (treated as markdown)

This keeps each source routed to the correct parser and avoids early data loss.

---

## Step 2: Parse and Normalize Content

Parsing converts raw inputs into a consistent markdown-like stream with preserved structure and metadata.

### Parsing Methods (Source-Aware)

- **Docling (UnifiedParser)** for PDF, DOCX, PPTX, XLSX, and images. It performs OCR, table extraction, and layout analysis.
- **MarkItDown (WebParser)** for URLs and HTML. It fetches the page and converts it to markdown.
- **MarkdownParser** for `.md` and `.txt`. It supports YAML frontmatter and retains headings and formatting.

Each parser returns:

- Normalized markdown content
- Metadata (title, source URL, page counts, etc.)

A **content hash** is computed on the parsed text (`sha256`) and carried forward as `metadata.content_hash`. That hash becomes the key for downstream caching.

For multi-source requests, every source is parsed separately and then merged into a single markdown file with per-source headings. That merged file becomes the one and only input to the LangGraph workflow.

[VISUAL:architecture:Parsing Stack:Show inputs (PDF/DOCX/PPTX, URL, Markdown/Text) feeding Docling and MarkItDown into normalized markdown]

---

## Step 3: Transform Content Into a Blog-Style Narrative

This is the core content generation step. The LLM takes the merged markdown and rewrites it as a structured, readable blog-style document:

- A generated title
- A clean outline
- Numbered sections with logical flow
- Subsections where needed
- A final key takeaways section

**Important rule:** the LLM must use only information present in the sources. It improves structure and clarity but does not invent new facts.

### How Large Inputs Are Handled

When the input is large, the generator first creates a **global outline** from the full content. Then it processes the content in chunks (about 10k characters each), passing the outline to every chunk so headings stay consistent and section numbering stays stable.

### LLM Outputs Produced Here

The transformation stage produces more than just markdown:

- **Blog content**: structured markdown with numbered sections
- **Outline**: used for long inputs to keep structure consistent across chunks
- **Visual markers**: optional `[VISUAL:...]` hints for diagrams
- **Executive summary**: short, high-level summary of the content
- **Slide structure** (PPTX only): slide titles and bullets optimized for presentation
If the LLM is unavailable, the pipeline falls back to cleaned markdown while still trying to generate executive summaries and slides if possible.

[VISUAL:flowchart:Content Structuring:Raw content -> LLM structuring -> numbered sections -> visual markers]

### API-Driven Model and Preference Controls (FastAPI)

When invoked via the API, request parameters drive runtime behavior rather than hardcoded defaults:

- `model`: LLM content model for summaries and slide structure
- `image_model`: Gemini image model for image generation
- `preferences.max_tokens`: token budget for blog generation
- `preferences.temperature`: summary/slide creativity level
- `preferences.max_slides` and `preferences.max_summary_points`: limits for PPTX + summaries
- `preferences.image_style`: overrides auto-detection (infographic, decorative, mermaid)
- `preferences.image_alignment_retries`: image alignment retry budget

---

## Step 4: Generate Section Images That Match the Content

Images are generated **per section**, grounded in the exact text of that section.

### How Image Prompts Are Built

For each `##` section, the pipeline:

1. Extracts visual concepts from the section text using an LLM (concepts, relationships, and recommended style).
2. Chooses a style (architecture diagram, process flow, comparison chart, handwritten notes).
3. Builds a content-aware prompt that includes **required labels** detected in the section (node names, tool names, and key terms).
4. Uses Gemini to generate the image prompt when available; otherwise falls back to a deterministic template.
5. Enforces that the **image title text exactly matches the section title** (used in both prompt and alignment checks).

Prompts are strict by design:

- Only use concepts from the section
- Include required labels verbatim
- Avoid metaphorical decorations

### Image Generation + Alignment Loop

Once a prompt is created, images are generated with Gemini and stored under:

```
output/<file_id>/images/<section-title>.png
```

If an image is regenerated for the same section, it is saved as:

```
output/<file_id>/images/<section-title>_2.png
```

After generation, a **Gemini alignment check** verifies that the image matches the section content **and** that the embedded title text matches the section title. The validator returns `aligned`, `notes`, plus `visual_feedbacks` and `labels_or_text_feedback` for more specific corrections. If it does not align, the system:

1. Revises the prompt using the alignment feedback
2. Regenerates the image
3. Re-validates the image

This loop is implemented inside `generate_images` (not a separate LangGraph node). It retries only the misaligned sections and stops after three attempts per section. The separate LangGraph retry loop is reserved for output validation, not image generation.

### Image Descriptions (New)

Once a section image is generated, the system uses the LLM to write a short **blog-style description** of the image. This paragraph is saved alongside the image and inserted **directly below the image** in the PDF output, so visuals always have a narrative explanation.

[VISUAL:flowchart:Image Alignment Loop:Section text -> concept extraction -> prompt -> Gemini image -> alignment check -> prompt feedback -> regenerate (max 3)]

---

## Step 5: Render the Final Output

### PDF Output

PDF generation uses **ReportLab**, which gives full layout control:

- Clean typography and hierarchy
- Consistent spacing and margins
- Inline section images and blog-style descriptions
- Code blocks and tables

Section images are inserted immediately after each `##` header, keeping them anchored to the narrative sequence. The output file itself is saved under the **file_id** folder (for example: `output/<file_id>/pdf/...`).

### PPTX Output

PPTX generation uses **python-pptx**:

- Title slide + section slides
- Section images placed on dedicated image slides when available
- Optional LLM slide structure used for more executive-quality layouts

Both formats are designed to be client-ready with minimal editing.

[VISUAL:comparison:Output Rendering:ReportLab -> PDF vs python-pptx -> PPTX]

---

## Step 6: Validate and Retry When Needed

Validation checks the output file before the workflow finishes:

- File exists
- File size > 0
- Extension matches the requested format

If validation fails, **LangGraph loops back to `generate_output`** and retries up to three times. Parsing and content transformation are not re-run; only the output generation step is retried.

[VISUAL:flowchart:Validation Gate:Generate output -> validate_output -> pass/fail retry (max 3)]

---

## Observability (Opik)

All LLM calls are traced to Opik when `COMET_API_KEY` is set. Traces include:

- Content generation calls (outline + chunked blog generation)
- Summary/slide structure generation
- Image prompt generation and alignment feedback
- Gemini image generation prompts (logged as `image_generate`)

The default Opik project name is **document generator** (override with `OPIK_PROJECT_NAME`).

---

## Caching: Three Layers of Reuse

This pipeline avoids repeated LLM and image work with three explicit caches:

### 1) API Request Cache (FastAPI)

`CacheService` stores results by hashing the entire request:

- Output format
- Sources (URLs, file_ids, or text)
- Provider + model
- Preferences (temperature, max tokens, slide count, etc.)

If `cache.reuse` is enabled and the hash matches, the API returns a **cache_hit** event without running the workflow.

### 2) Structured Content Cache (Workflow)

After transformation, the structured markdown is saved to:

```
src/output/cache/<input_name>_content_cache.json
```

On future runs, the content is reused when the **content_hash** matches the current input.

### 3) Image Cache + Manifest

Generated images live under `output/<file_id>/images`. A `manifest.json` file stores:

- The content hash used for those images
- The list of section titles
- Section title map + image types
- Image descriptions (used for PDF captions)

If the hash matches, the image generation node skips re-generation and reuses the existing images.

---

## How the FastAPI Flow Works End to End

### 1) Upload Files

`POST /api/upload` stores the file and returns a `file_id`.

### 2) Generate Document (SSE)

`POST /api/generate` does the following:

1. **Checks API cache** (if `cache.reuse` is enabled)
2. **Collects sources** (files, URLs, and text)
3. **Parses each source** using the appropriate parser
4. **Merges** the sources into a single markdown file
5. **Runs the LangGraph workflow** in a thread pool (with `file_id` passed through to keep outputs under the correct folder)
6. **Streams progress events** via SSE

### 3) Download

The final event includes a `download_url` and `file_path`. The output is fetched from:

```
GET /api/download/{file_path}
```

This API layout makes the generation flow easy to integrate into a frontend or async pipeline.

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
[VISUAL:architecture:Generation Pipeline:Show ingest -> normalize -> transform -> generate images -> render output]
```

---

## Performance & Cost Notes

- **Typical runtimes**: 60-120 seconds for multi-source inputs, depending on length and image count.
- **Cache savings**: When content is unchanged, the system skips structured-content and image regeneration.
- **Image limits**: Gemini image generation is rate-limited (default delay is enforced in the generator).
- **Best practice**: Keep sections focused to reduce image count and keep slides concise.

---

## Why This Workflow Works

**1) Clean separation of responsibilities**
Each LangGraph node does one job, which keeps the pipeline debuggable and extensible.

**2) Content fidelity**
The LLM rewrites for clarity without introducing new facts. The output stays grounded in the sources.

**3) Visuals that explain, not decorate**
Prompts are content-bound, labels are extracted from the text, and alignment checks enforce relevance.

**4) Multi-format output without duplication**
The same structured markdown feeds both PDF and PPTX generators.

**5) Deterministic anchoring**
Images are tied to section IDs and inserted immediately after their section headers.

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
    "model": "gemini-2.5-flash",
    "image_model": "gemini-2.5-flash",
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

---

## Closing Thoughts

This generator is more than a file converter. It is a **content transformation workflow** designed to turn messy inputs into a structured, visual, presentation-ready document. By combining strict parsing, LLM-based organization, and content-grounded image generation, it produces outputs that feel authored rather than assembled.

If your team produces or collects large volumes of content, this pipeline turns that sprawl into a consistent, professional narrative in a repeatable way.
