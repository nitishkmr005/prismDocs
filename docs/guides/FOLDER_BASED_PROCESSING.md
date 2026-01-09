# Folder-Based Topic Processing

Process multiple files from a single topic folder and generate one combined PDF/PPTX per topic.

## Overview

The document generator supports **folder-based processing** where:
- Each subfolder in `src/data/` represents one topic
- All files in a folder are merged into a single cohesive document
- One PDF and one PPTX are generated per folder
- Images can be reused across regenerations

---

## Directory Structure

```
src/data/
├── llm-architectures/           # Topic 1
│   ├── slides.pdf              # File 1
│   ├── transcript.txt          # File 2
│   └── notes.md                # File 3
│
├── machine-learning/            # Topic 2
│   ├── intro.pdf
│   └── advanced.docx
│
└── python-basics/               # Topic 3
    ├── tutorial.md
    └── examples.txt

After processing:

src/output/
├── llm-architectures.pdf        # Combined from all files in folder
├── llm-architectures.pptx
├── machine-learning.pdf
├── machine-learning.pptx
├── python-basics.pdf
└── python-basics.pptx
```

---

## How It Works

### 1. Discovery
Scans `src/data/` for subdirectories (topic folders).

### 2. File Processing
For each file in the folder:
- Parses content (PDF, DOCX, Markdown, TXT, PPTX)
- Extracts text and structure
- Collects metadata

### 3. Content Merging
Uses **LLM-powered chunked processing** to:
- Combine all content intelligently
- Generate cohesive blog-style document
- Create logical section structure
- Add visual markers for diagrams
- Generate unified table of contents

### 4. Output Generation
Creates:
- **One PDF** with all merged content
- **One PPTX** with all merged content
- Embedded images (if generated or reused)

---

## Usage

### Option 1: Process Single Topic Folder

```bash
# Basic usage
python scripts/generate_from_folder.py src/data/llm-architectures

# With existing images (fast!)
python scripts/generate_from_folder.py src/data/llm-architectures --skip-images

# Custom output directory
python scripts/generate_from_folder.py src/data/llm-architectures --output-dir output/reports

# With verbose logging
python scripts/generate_from_folder.py src/data/llm-architectures --verbose
```

**Example:**
```bash
python scripts/generate_from_folder.py src/data/llm-architectures --skip-images
```

**Output:**
```
Processing folder: llm-architectures
Found 2 file(s):
  - Transformers-Internals_slides.pdf
  - Transformers-Internals_transcript.txt

Merging 2 files using LLM...
LLM transformation complete: 32 sections, 5 visual markers

✅ PDF generated: src/output/llm-architectures.pdf
✅ PPTX generated: src/output/llm-architectures.pptx
```

---

### Option 2: Batch Process All Topics

Process all subfolders in `src/data/` at once:

```bash
# Process all topics
python scripts/batch_process_topics.py

# Reuse images (recommended for fast iteration)
python scripts/batch_process_topics.py --skip-images

# Custom data directory
python scripts/batch_process_topics.py --data-dir path/to/topics

# With verbose logging
python scripts/batch_process_topics.py --skip-images --verbose
```

**Example:**
```bash
python scripts/batch_process_topics.py --skip-images
```

**Output:**
```
BATCH PROCESSING ALL TOPICS
Found 3 topic folder(s):
  - llm-architectures
  - machine-learning
  - python-basics

PROCESSING TOPIC 1/3: llm-architectures
✅ Successfully processed: llm-architectures

PROCESSING TOPIC 2/3: machine-learning
✅ Successfully processed: machine-learning

PROCESSING TOPIC 3/3: python-basics
✅ Successfully processed: python-basics

BATCH PROCESSING COMPLETE
Total topics: 3
Successfully processed: 3
Failed: 0

Generated documents:
llm-architectures:
  PDF:  src/output/llm-architectures.pdf
  PPTX: src/output/llm-architectures.pptx
machine-learning:
  PDF:  src/output/machine-learning.pdf
  PPTX: src/output/machine-learning.pptx
python-basics:
  PDF:  src/output/python-basics.pdf
  PPTX: src/output/python-basics.pptx
```

---

## Supported File Types

The processor automatically handles:

| Extension | Format | Description |
|-----------|--------|-------------|
| `.pdf` | PDF | Parsed using Docling |
| `.docx` | Word | Parsed with python-docx |
| `.pptx` | PowerPoint | Parsed with python-pptx |
| `.md`, `.markdown` | Markdown | Native support |
| `.txt` | Text | Plain text |

**Note:** All files in a folder are processed and merged together.

---

## Content Merging Strategy

### LLM-Powered Merging (Default)

Uses **chunked LLM processing** to:
1. Analyze all files and detect content type (transcript, slides, mixed, document)
2. Process ALL content (no truncation) using intelligent chunking
3. Generate unified blog-style document with:
   - Cohesive narrative flow
   - Logical section structure
   - Visual markers for diagrams
   - Cross-references between sources
4. Create metadata with auto-generated title

**Benefits:**
- ✅ Professional output quality
- ✅ Handles large content (no truncation)
- ✅ Smart section organization
- ✅ Automatic visual suggestions

### Basic Merging (Fallback)

If LLM is unavailable:
- Concatenates content from all files
- Adjusts header levels
- Adds table of contents
- Preserves source file markers

---

## Image Handling

### Generate Images (Default)
```bash
python scripts/generate_from_folder.py src/data/llm-architectures
```
- Generates new images for each section
- Uses Gemini Imagen 3.0
- Saves to `src/output/images/`
- Embeds in PDF/PPTX

### Reuse Existing Images (Faster)
```bash
python scripts/generate_from_folder.py src/data/llm-architectures --skip-images
```
- Loads existing images from `src/output/images/`
- Skips generation (saves time and API costs)
- Perfect for quick iterations

**Performance Comparison:**
| Mode | Time | API Calls | Cost |
|------|------|-----------|------|
| Full generation | 5-10 min | 20-30 | $$$ |
| Reuse images | 1-2 min | 0 | $ |

---

## Workflow Examples

### First Time: Full Generation

```bash
# Process a new topic folder with full image generation
python scripts/generate_from_folder.py src/data/new-topic

# Output:
# - Processes all files
# - Merges content with LLM
# - Generates images (slow)
# - Creates PDF and PPTX
```

### Iteration: Reuse Images

```bash
# Regenerate PDF/PPTX with existing images (fast!)
python scripts/generate_from_folder.py src/data/new-topic --skip-images

# Output:
# - Processes all files
# - Merges content with LLM
# - Reuses existing images (fast!)
# - Creates PDF and PPTX
```

### Batch Processing

```bash
# Process all topics with image reuse
python scripts/batch_process_topics.py --skip-images

# Output:
# - Discovers all folders in src/data/
# - Processes each folder
# - Generates PDF and PPTX for each
# - Summary report at the end
```

---

## Adding New Topics

1. **Create a folder** in `src/data/`:
   ```bash
   mkdir src/data/my-new-topic
   ```

2. **Add files** to the folder:
   ```bash
   cp slides.pdf src/data/my-new-topic/
   cp transcript.txt src/data/my-new-topic/
   ```

3. **Process** the folder:
   ```bash
   python scripts/generate_from_folder.py src/data/my-new-topic
   ```

4. **Output** will be:
   ```
   src/output/my-new-topic.pdf
   src/output/my-new-topic.pptx
   ```

---

## Tips & Best Practices

### 1. Organize by Topic
- One folder = One cohesive topic
- Related files in same folder
- Descriptive folder names (used as output filename)

### 2. File Naming
- Name files logically: `intro.pdf`, `advanced.md`, `notes.txt`
- Files are processed in alphabetical order
- Consider numbering: `01-intro.pdf`, `02-details.md`

### 3. Image Reuse
- Use `--skip-images` for quick iterations
- Only regenerate images when content changes significantly
- Keep `src/output/images/` between runs

### 4. Batch Processing
- Process all topics overnight with batch script
- Use `--skip-images` for faster batch runs
- Check logs for any failures

### 5. Content Quality
- Include diverse sources (slides + transcript + notes)
- LLM will merge them intelligently
- More content = better merged output

---

## Troubleshooting

### "No supported files found"
- Check folder contains `.pdf`, `.md`, `.txt`, `.docx`, or `.pptx` files
- Verify file extensions are correct

### "Failed to process file"
- Check individual file is valid (can be opened)
- Look at logs for specific error
- Try processing file individually first

### "Images not appearing in PDF"
- Ensure `src/output/images/` contains images
- Use `--skip-images` only if images exist
- Check logs for image loading errors

### Batch processing partial failures
- Check logs for specific folder errors
- Retry failed folders individually
- Some folders may succeed while others fail

---

## Advanced Configuration

### Custom Output Directory
```bash
python scripts/generate_from_folder.py src/data/topic \
    --output-dir reports/2025
```

### With API Key
```bash
python scripts/generate_from_folder.py src/data/topic \
    --api-key YOUR_OPENAI_KEY
```

### Verbose Logging
```bash
python scripts/generate_from_folder.py src/data/topic \
    --verbose \
    --log-file logs/processing.log
```

### Batch with All Options
```bash
python scripts/batch_process_topics.py \
    --data-dir src/data \
    --output-dir reports \
    --skip-images \
    --verbose \
    --log-file logs/batch.log
```

---

## Summary

### Single Topic
```bash
# Full processing
python scripts/generate_from_folder.py src/data/topic-name

# Fast (reuse images)
python scripts/generate_from_folder.py src/data/topic-name --skip-images
```

### All Topics
```bash
# Batch process everything
python scripts/batch_process_topics.py --skip-images
```

### Output
```
src/output/
├── topic-name.pdf     # Combined PDF
├── topic-name.pptx    # Combined PPTX
└── images/            # Generated/reused images
```

**This is perfect for organizing multiple topics with multiple files per topic!** 🎉
