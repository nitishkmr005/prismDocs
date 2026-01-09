# Quick Start: Reuse Your Existing Images

You have **27 images** already generated in `src/output/images/`. Here's how to reuse them!

## ✅ Right Now: Generate PDF with Your Existing Images

```bash
# Skip image generation, use existing images
python scripts/quick_pdf_with_images.py src/data/llm-architectures/Transformers-Internals_slides.pdf
```

**What this does:**
- ✅ Loads your 27 existing images from `src/output/images/`
- ✅ Processes content with LLM (creates sections, structure)
- ✅ Generates PDF with embedded images
- ⚡ Fast! No image generation wait
- 💰 Saves API costs (no Gemini calls)

---

## How It Works

### Your Images
```
src/output/images/
├── section_0_infographic.png   ✅ Already exists
├── section_1_infographic.png   ✅ Already exists
├── section_2_infographic.png   ✅ Already exists
...
└── section_32_infographic.png  ✅ Already exists
```

### What Happens
1. **Image Generation Node**: Detects `skip_image_generation=True`
2. **Loads existing images**: Scans `src/output/images/` for `section_*.png`
3. **Maps to sections**: `section_0` → your first section, etc.
4. **Embeds in PDF**: Uses your existing images

---

## Three Options

### 1. Quick Script (Recommended for You)
```bash
python scripts/quick_pdf_with_images.py src/data/llm-architectures/Transformers-Internals_slides.pdf
```
**Use case:** You have images, just need a new PDF

---

### 2. Automatic Reuse (Default)
```bash
make run
# Or: python scripts/run_generator.py <input>
```
**What happens:**
- Checks if each image exists
- Reuses existing images
- Only generates missing images
- Logs: "Reusing existing image for section X"

---

### 3. Full Control
```bash
python scripts/generate_pdf_from_cache.py src/data/llm-architectures/Transformers-Internals_slides.pdf
```
**Use case:** Future - when you have cached content too

---

## Your Workflow Now

```bash
# 1. Use your existing images to generate PDF
python scripts/quick_pdf_with_images.py src/data/llm-architectures/Transformers-Internals_slides.pdf

# Output: src/output/Transformers-Internals_slides.pdf
# With your 27 images embedded!
```

---

## Content Caching (Not Yet Saved)

Currently, you don't have cached structured content. To enable it:

```python
from doc_generator.application.graph_workflow import run_workflow

result = run_workflow(
    input_path="input.pdf",
    output_format="pdf",
    metadata={
        "skip_image_generation": True,  # Use existing images
        "cache_content": True           # Save content for next time
    }
)
```

**This saves to:** `src/output/cache/<name>_content_cache.json`

**Contains:**
- Markdown content
- Section structure  
- Image mappings
- All LLM-processed data

---

## Benefits

| Without Reuse | With Reuse |
|--------------|------------|
| 5-10 minutes | 1-2 minutes |
| 27 API calls | 0 API calls |
| $$$ | Free |

---

## Files

```
📁 Your Current Setup:
src/output/
├── images/                          ✅ 27 images ready
│   ├── section_0_infographic.png
│   ├── section_1_infographic.png
│   └── ...
└── cache/                           ⚠️ Not yet created
    └── (will be created if you enable caching)
```

---

## Try It Now!

```bash
cd /Users/nitishkumarharsoor/Documents/1.Learnings/1.Projects/4.Experiments/7.document-generator

python scripts/quick_pdf_with_images.py \
    src/data/llm-architectures/Transformers-Internals_slides.pdf
```

**Expected output:**
```
INFO     | Quick PDF generation with existing images
INFO     | Loaded 27 existing images (generation skipped)
INFO     | Processing content...
SUCCESS  | ✅ PDF generated successfully: src/output/Transformers-Internals_slides.pdf
```

---

## Full Documentation

See: [`docs/guides/REUSING_IMAGES.md`](docs/guides/REUSING_IMAGES.md)

---

## Summary

✅ **You have:** 27 images in `src/output/images/`  
✅ **You can:** Reuse them to generate PDFs quickly  
✅ **How:** Run `python scripts/quick_pdf_with_images.py <input>`  
✅ **Benefit:** Fast, free, no waiting! 🎉
