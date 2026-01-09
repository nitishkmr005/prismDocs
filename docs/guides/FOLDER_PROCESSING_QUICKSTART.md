# Quick Start: Folder-Based Topic Processing

Process entire folders as topics - combine multiple files into one PDF/PPTX per topic.

## Current Setup

```
src/data/
└── llm-architectures/              ✅ Your topic folder
    ├── Transformers-Internals_slides.pdf
    └── Transformers-Internals_transcript.txt

src/output/
└── images/                         ✅ 27 existing images
    ├── section_0_infographic.png
    ├── section_1_infographic.png
    └── ... (27 total)
```

---

## ✅ Process Your LLM Architectures Folder

### Option 1: With Existing Images (Fast - Recommended!)

```bash
python scripts/generate_from_folder.py \
    src/data/llm-architectures \
    --skip-images
```

**What it does:**
1. ✅ Processes both files (slides.pdf + transcript.txt)
2. ✅ Merges them intelligently with LLM
3. ✅ Reuses your 27 existing images
4. ✅ Generates **ONE** PDF: `src/output/llm-architectures.pdf`
5. ✅ Generates **ONE** PPTX: `src/output/llm-architectures.pptx`

**Time:** ~2-3 minutes (no image generation!)

---

### Option 2: Full Generation (Slower)

```bash
python scripts/generate_from_folder.py src/data/llm-architectures
```

**What it does:**
1. ✅ Processes both files
2. ✅ Merges with LLM
3. 🐌 Generates new images (slow)
4. ✅ Creates PDF and PPTX

**Time:** ~10-15 minutes

---

## How It Works

### Single Folder Processing

```
INPUT (folder):
llm-architectures/
├── slides.pdf        (File 1)
└── transcript.txt    (File 2)

PROCESSING:
1. Parse slides.pdf → extract content
2. Parse transcript.txt → extract content
3. LLM merges both → cohesive document
4. Generate/reuse images
5. Create outputs

OUTPUT:
├── llm-architectures.pdf   (Combined from both files)
└── llm-architectures.pptx  (Combined from both files)
```

---

## Adding More Topics

### 1. Create New Topic Folder

```bash
mkdir src/data/machine-learning
```

### 2. Add Files

```bash
# Add any supported files
cp intro.pdf src/data/machine-learning/
cp advanced.md src/data/machine-learning/
cp notes.txt src/data/machine-learning/
```

### 3. Process

```bash
python scripts/generate_from_folder.py src/data/machine-learning --skip-images
```

### 4. Get Combined Output

```
src/output/
├── machine-learning.pdf   (All files combined)
└── machine-learning.pptx  (All files combined)
```

---

## Batch Process All Topics

Process **all folders** in `src/data/` at once:

```bash
python scripts/batch_process_topics.py --skip-images
```

**Example with 3 topics:**

```
src/data/
├── llm-architectures/     → llm-architectures.pdf + .pptx
├── machine-learning/      → machine-learning.pdf + .pptx
└── python-basics/         → python-basics.pdf + .pptx

Result:
✅ 3 PDFs generated
✅ 3 PPTXs generated
✅ All in one run!
```

---

## Supported File Types

Your folder can contain any mix of:

| Type | Extensions | Example |
|------|------------|---------|
| PDF | `.pdf` | slides.pdf |
| Word | `.docx` | notes.docx |
| PowerPoint | `.pptx` | presentation.pptx |
| Markdown | `.md`, `.markdown` | readme.md |
| Text | `.txt` | transcript.txt |

**All files in the folder are merged together!**

---

## Your Workflow

### Current State
You have:
- ✅ 1 topic folder: `llm-architectures/`
- ✅ 2 files in it: slides.pdf + transcript.txt
- ✅ 27 existing images in `src/output/images/`

### Recommended Workflow

#### Step 1: Process with existing images
```bash
python scripts/generate_from_folder.py src/data/llm-architectures --skip-images
```

**Output:**
```
src/output/
├── llm-architectures.pdf   ✅ Combined document
├── llm-architectures.pptx  ✅ Combined presentation
└── images/                 ✅ Your 27 images (reused)
```

#### Step 2: Add more topics as needed
```bash
# Create new folder
mkdir src/data/new-topic

# Add files
cp file1.pdf src/data/new-topic/
cp file2.md src/data/new-topic/

# Process
python scripts/generate_from_folder.py src/data/new-topic --skip-images
```

#### Step 3: Batch process everything
```bash
# Process all topics at once
python scripts/batch_process_topics.py --skip-images
```

---

## Key Benefits

### ✅ Multiple Files → One Output
- Merge slides + transcript + notes
- One cohesive PDF per topic
- Professional combined presentation

### ✅ Smart LLM Merging
- Intelligent content integration
- Logical section structure
- Cross-references between sources
- Auto-generated table of contents

### ✅ Image Reuse
- Skip regeneration with `--skip-images`
- Fast iterations (minutes vs hours)
- Save API costs

### ✅ Batch Processing
- Process all topics with one command
- Consistent output across topics
- Easy to maintain

---

## Examples

### Example 1: Single Topic (Your Current Case)
```bash
# Process llm-architectures folder
python scripts/generate_from_folder.py src/data/llm-architectures --skip-images

# Output: src/output/llm-architectures.pdf + .pptx
```

### Example 2: Multiple Topics
```bash
# Setup
mkdir src/data/topic-a
mkdir src/data/topic-b
cp files... src/data/topic-a/
cp files... src/data/topic-b/

# Batch process
python scripts/batch_process_topics.py --skip-images

# Output:
# - topic-a.pdf + .pptx
# - topic-b.pdf + .pptx
```

### Example 3: Mixed File Types
```bash
# Folder with mixed types
src/data/ml-course/
├── lecture-1.pdf
├── lecture-2.pptx
├── notes.md
└── transcript.txt

# Process all together
python scripts/generate_from_folder.py src/data/ml-course --skip-images

# Output: ml-course.pdf + .pptx (all files merged)
```

---

## Quick Commands

```bash
# Single folder with image reuse (RECOMMENDED)
python scripts/generate_from_folder.py src/data/<folder-name> --skip-images

# Single folder with full generation
python scripts/generate_from_folder.py src/data/<folder-name>

# All folders with image reuse
python scripts/batch_process_topics.py --skip-images

# All folders with full generation
python scripts/batch_process_topics.py

# With verbose logging
python scripts/generate_from_folder.py src/data/<folder> --skip-images --verbose
```

---

## Performance

| Scenario | Files | Images | Time |
|----------|-------|--------|------|
| Single folder (reuse images) | 2 | Reuse 27 | ~2 min |
| Single folder (full) | 2 | Generate 27 | ~10 min |
| Batch 3 folders (reuse) | 6 | Reuse | ~6 min |
| Batch 3 folders (full) | 6 | Generate | ~30 min |

**Recommendation:** Always use `--skip-images` unless content changed significantly!

---

## Full Documentation

See: [`docs/guides/FOLDER_BASED_PROCESSING.md`](docs/guides/FOLDER_BASED_PROCESSING.md)

---

## Summary

✅ **Your setup:** 1 folder (`llm-architectures`) with 2 files  
✅ **Command:** `python scripts/generate_from_folder.py src/data/llm-architectures --skip-images`  
✅ **Output:** One combined PDF + PPTX with your 27 images  
✅ **Time:** ~2 minutes  
✅ **Result:** Professional merged document from all sources! 🎉
