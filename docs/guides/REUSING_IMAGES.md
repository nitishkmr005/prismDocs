# Reusing Images and Cached Content

This guide explains how to reuse existing images and cached content without regenerating them.

## Problem

Image generation with Gemini is:
- **Slow** (3+ seconds per image with rate limiting)
- **Expensive** (API costs)
- **Unnecessary** if you already have good images

## Solution

The system now supports:
1. ✅ **Reusing existing images** - Skip regeneration, use images from `src/output/images/`
2. ✅ **Content caching** - Save structured content (markdown, sections, metadata)
3. ✅ **Automatic image detection** - Check if image exists before generating

---

## Quick Start: Generate PDF with Existing Images

The **easiest way** to reuse your existing images:

```bash
python scripts/quick_pdf_with_images.py src/data/llm-architectures/Transformers-Internals_slides.pdf
```

This will:
- ✅ Skip image generation entirely
- ✅ Load existing images from `src/output/images/`
- ✅ Generate PDF with those images embedded
- ⚠️ Still runs LLM content processing (for sections, structure, etc.)

---

## How Images Are Stored

Images are saved with predictable filenames:

```
src/output/images/
├── section_0_infographic.png   # Section 0 image
├── section_1_infographic.png   # Section 1 image
├── section_2_infographic.png   # Section 2 image
└── ...
```

The system maps `section_id` to the corresponding image during PDF generation.

---

## Three Ways to Reuse Images

### Option 1: Quick Script (Easiest)

Use the quick script to skip image generation:

```bash
# Generate PDF with existing images
python scripts/quick_pdf_with_images.py <input_file>
```

**Example:**
```bash
python scripts/quick_pdf_with_images.py src/data/llm-architectures/Transformers-Internals_slides.pdf
```

**What it does:**
- Runs full workflow (parse → transform → generate PDF)
- Skips image generation node
- Loads existing images from disk
- Fast (no image generation wait time)

---

### Option 2: Using Metadata Flags

Add `skip_image_generation` flag to workflow metadata:

```python
from doc_generator.application.graph_workflow import run_workflow

result = run_workflow(
    input_path="input.pdf",
    output_format="pdf",
    metadata={"skip_image_generation": True}  # Skip image generation
)
```

**What happens:**
1. Workflow detects `skip_image_generation=True`
2. `generate_images_node` loads existing images from disk
3. PDF generator uses those images
4. No Gemini API calls

---

### Option 3: Automatic Reuse (Default Behavior)

The system **automatically reuses existing images** if they're already present:

```bash
# First run: generates images
make run

# Second run: reuses images automatically
make run
```

**How it works:**
- Before generating an image, checks if file exists: `section_X_infographic.png`
- If exists: reuse it (skip generation)
- If missing: generate new image
- Logs: `"Reusing existing image for section X"`

---

## Content Caching (Advanced)

### Save Structured Content

To cache the LLM-processed content (markdown, sections, metadata):

```python
from doc_generator.application.graph_workflow import run_workflow

result = run_workflow(
    input_path="input.pdf",
    output_format="pdf",
    metadata={"cache_content": True}  # Enable caching
)
```

**Saves to:** `src/output/cache/<filename>_content_cache.json`

**Contains:**
- Processed markdown content
- Section structure
- Image mappings
- Metadata

### Load Cached Content

```python
from doc_generator.utils.content_cache import load_structured_content

# Load previously cached content
cached = load_structured_content("input.pdf")

if cached:
    # Use cached content directly
    print(f"Loaded {len(cached.get('section_images', {}))} cached image references")
```

### Load Existing Images

```python
from doc_generator.utils.content_cache import load_existing_images

# Scan and load all existing images
section_images = load_existing_images()

print(f"Found {len(section_images)} existing images")
# Output: Found 27 existing images
```

---

## Advanced: Generate PDF from Cache Script

For maximum control, use the full caching script:

```bash
python scripts/generate_pdf_from_cache.py <input_file> [options]
```

**Options:**
- `--no-cache`: Don't use cached content (reprocess with LLM)
- `--regenerate-images`: Regenerate images (don't reuse existing)
- `-o <path>`: Custom output path

**Examples:**

```bash
# Use both cached content and existing images (fastest)
python scripts/generate_pdf_from_cache.py input.pdf

# Use cached content but regenerate images
python scripts/generate_pdf_from_cache.py input.pdf --regenerate-images

# Reprocess content but reuse images
python scripts/generate_pdf_from_cache.py input.pdf --no-cache

# Everything fresh (no cache or image reuse)
python scripts/generate_pdf_from_cache.py input.pdf --no-cache --regenerate-images
```

---

## File Locations

```
src/output/
├── images/                          # Generated images
│   ├── section_0_infographic.png
│   ├── section_1_infographic.png
│   └── ...
├── cache/                           # Cached structured content
│   └── <filename>_content_cache.json
└── <output>.pdf                     # Generated PDFs
```

---

## Clear Cache

To remove all cached content:

```python
from doc_generator.utils.content_cache import clear_cache

clear_cache()
```

Or manually:
```bash
rm -rf src/output/cache/*.json
```

---

## Performance Comparison

| Method | Time | API Calls | Cost |
|--------|------|-----------|------|
| **Full generation** | ~5-10 min | 20-30 images | $$$ |
| **Reuse images** | ~1-2 min | 0 images | $ |
| **Use cache + images** | ~30 sec | 0 everything | Free |

---

## Tips

1. **Keep your images** - Don't delete `src/output/images/` between runs
2. **Version control** - Consider committing generated images for consistency
3. **Cache for iterations** - When tweaking PDF layout/styling, use cached content
4. **Force regeneration** - Delete specific images to regenerate only those sections

---

## Example Workflow

### Initial Generation
```bash
# Generate everything (images + content)
python scripts/run_generator.py input.pdf

# Images saved to: src/output/images/section_*.png
# PDF saved to: src/output/input.pdf
```

### Quick Iteration (Change PDF styling)
```bash
# Reuse images, just regenerate PDF
python scripts/quick_pdf_with_images.py input.pdf

# Fast! No image generation
```

### Full Reuse
```bash
# Both content and images cached
python scripts/generate_pdf_from_cache.py input.pdf

# Fastest! Everything from cache
```

---

## Troubleshooting

### "No images found"
- Check if `src/output/images/` contains `section_*_infographic.png` files
- Verify filenames match pattern: `section_{ID}_infographic.png`

### "Images not appearing in PDF"
- Ensure `skip_image_generation=True` is set in metadata
- Check logs for "Loaded X existing images"
- Verify section IDs match between markdown and image filenames

### "Wrong images in PDF"
- Delete old images: `rm src/output/images/*.png`
- Regenerate: `make run`

---

## Summary

✅ **Quick PDF with existing images:**
```bash
python scripts/quick_pdf_with_images.py input.pdf
```

✅ **Automatic reuse (default):**
```bash
make run  # Reuses existing images automatically
```

✅ **Full caching:**
```bash
python scripts/generate_pdf_from_cache.py input.pdf
```

This saves time, money, and bandwidth while maintaining quality! 🎉
