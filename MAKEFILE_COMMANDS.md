# Makefile Commands Quick Reference

All automation commands for the document generator.

## Quick Start

```bash
# Show all commands
make help

# Process your LLM architectures folder (FASTEST!)
make llm-arch

# Process all folders in src/data/
make batch-topics-fast
```

---

## 📁 Folder-Based Processing

Process entire folders (merge all files → 1 PDF + 1 PPTX).

### Fast Mode (Reuse Existing Images) - RECOMMENDED ⚡

```bash
# Process single folder (fast)
make process-folder-fast FOLDER=<folder-name>

# Example
make process-folder-fast FOLDER=llm-architectures
make process-folder-fast FOLDER=machine-learning
```

### Full Mode (Generate Images)

```bash
# Process single folder (full, slow)
make process-folder FOLDER=<folder-name>

# Example
make process-folder FOLDER=llm-architectures
```

---

## 🔄 Batch Processing

Process all folders in `src/data/` at once.

```bash
# Fast mode (reuse images) - RECOMMENDED
make batch-topics-fast

# Full mode (generate images)
make batch-topics
```

**Output:** One PDF and one PPTX per folder in `src/data/`

---

## ⚡ Quick PDF Generation

Generate PDF with existing images (no image generation).

```bash
make quick-pdf INPUT=<file>
```

**Examples:**
```bash
make quick-pdf INPUT=src/data/llm-architectures/slides.pdf
make quick-pdf INPUT=src/data/document.md
make quick-pdf INPUT=README.md
```

---

## 🎯 Convenient Shortcuts

```bash
# Process llm-architectures folder (fast)
make llm-arch

# Process llm-architectures folder (full)
make llm-arch-full
```

---

## 📝 Single File Processing

Process individual files (not folders).

```bash
# Generate single format
make run-docgen INPUT=<file> OUTPUT=<pdf|pptx>

# Examples
make run-docgen INPUT=src/data/sample.md OUTPUT=pdf
make run-docgen INPUT=README.md OUTPUT=pptx
```

---

## 🗂️ Topic Management

```bash
# List all available topic folders
make list-topics
```

**Example output:**
```
📁 Available topic folders in src/data/:
llm-architectures
machine-learning
python-basics
```

---

## 🧹 Cache & Cleanup

```bash
# Clear content cache
make clear-cache

# Clear generated images (WARNING: will need regeneration)
make clear-images

# Clean all generated files and caches
make clean-docgen
```

---

## ⚙️ Setup & Maintenance

```bash
# Install dependencies
make setup-docgen

# Run tests
make test-docgen

# Lint and type check
make lint-docgen
```

---

## 🐳 Docker Commands

```bash
# Build Docker image
make docker-build

# Run in Docker
make docker-run INPUT=<file> OUTPUT=<format>

# Example
make docker-run INPUT=src/data/sample.md OUTPUT=pdf
```

---

## Command Comparison

| Task | Command | Speed | When to Use |
|------|---------|-------|-------------|
| **Process folder (fast)** | `make process-folder-fast FOLDER=name` | ⚡ Fast | Images exist, quick iteration |
| **Process folder (full)** | `make process-folder FOLDER=name` | 🐌 Slow | First time, content changed |
| **Batch (fast)** | `make batch-topics-fast` | ⚡⚡ Fast | Process all, images exist |
| **Batch (full)** | `make batch-topics` | 🐌🐌 Very slow | First time batch |
| **Quick PDF** | `make quick-pdf INPUT=file` | ⚡ Fast | Single file, reuse images |
| **Shortcut** | `make llm-arch` | ⚡ Fast | LLM architectures folder |

---

## Typical Workflows

### Workflow 1: First Time Setup

```bash
# 1. Install dependencies
make setup-docgen

# 2. Process your folder (full, generates images)
make process-folder FOLDER=llm-architectures

# Output:
# ✅ src/output/llm-architectures.pdf
# ✅ src/output/llm-architectures.pptx
# ✅ src/output/images/*.png (27 images)
```

### Workflow 2: Quick Iteration (Existing Images)

```bash
# Fast! Reuse existing images
make llm-arch

# Or:
make process-folder-fast FOLDER=llm-architectures

# Time: ~2 minutes
```

### Workflow 3: Multiple Topics

```bash
# 1. Add folders to src/data/
mkdir src/data/topic-1
mkdir src/data/topic-2
cp files... src/data/topic-1/
cp files... src/data/topic-2/

# 2. Batch process all
make batch-topics-fast

# Output:
# ✅ topic-1.pdf + .pptx
# ✅ topic-2.pdf + .pptx
```

### Workflow 4: Content Update

```bash
# 1. Update files in folder
vim src/data/llm-architectures/slides.pdf

# 2. Regenerate with existing images (fast)
make llm-arch

# 3. If visuals changed significantly, regenerate images
make llm-arch-full
```

---

## Environment Variables

Some commands support additional options:

```bash
# Verbose logging
make process-folder-fast FOLDER=llm-architectures VERBOSE=1

# Custom output directory
make process-folder FOLDER=name OUTPUT_DIR=reports/
```

---

## Examples

### Example 1: Your Current Setup

```bash
# You have:
# - src/data/llm-architectures/ (folder with 2 files)
# - src/output/images/ (27 existing images)

# Process with existing images (RECOMMENDED)
make llm-arch

# Output:
# ✅ src/output/llm-architectures.pdf
# ✅ src/output/llm-architectures.pptx
```

### Example 2: Add New Topic

```bash
# 1. Create folder
mkdir src/data/machine-learning
cp intro.pdf src/data/machine-learning/
cp advanced.md src/data/machine-learning/

# 2. Process (will generate images)
make process-folder FOLDER=machine-learning

# Or batch process everything
make batch-topics-fast
```

### Example 3: Quick PDF from Single File

```bash
make quick-pdf INPUT=src/data/llm-architectures/slides.pdf
```

---

## Help & Documentation

```bash
# Show all commands
make help

# Show detailed help
make help-docgen
```

**Documentation files:**
- `FOLDER_PROCESSING_QUICKSTART.md` - Folder processing guide
- `docs/guides/FOLDER_BASED_PROCESSING.md` - Complete folder guide
- `docs/guides/REUSING_IMAGES.md` - Image reuse guide
- `README.md` - Full documentation

---

## Summary of New Commands

| Command | Description |
|---------|-------------|
| `make llm-arch` | Process LLM architectures (fast) ⭐ |
| `make process-folder-fast FOLDER=<name>` | Process folder (reuse images) ⭐ |
| `make process-folder FOLDER=<name>` | Process folder (generate images) |
| `make batch-topics-fast` | Process all folders (fast) ⭐ |
| `make batch-topics` | Process all folders (full) |
| `make quick-pdf INPUT=<file>` | Quick PDF with existing images ⭐ |
| `make list-topics` | List available folders |
| `make clear-cache` | Clear content cache |
| `make clear-images` | Clear generated images |

**⭐ = Most commonly used commands**

---

## Quick Reference Card

```bash
# MOST COMMON COMMANDS:

make llm-arch                                # Process LLM architectures (fast)
make batch-topics-fast                       # Process all folders (fast)
make quick-pdf INPUT=file.pdf                # Quick PDF generation

# FOLDER PROCESSING:

make process-folder-fast FOLDER=name         # Fast (reuse images)
make process-folder FOLDER=name              # Full (generate images)

# UTILITIES:

make list-topics                             # List available folders
make clear-cache                             # Clear cache
make help                                    # Show all commands
```

---

**Ready to use!** Start with: `make llm-arch` 🚀
