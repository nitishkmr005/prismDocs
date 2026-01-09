# Makefile Quick Start

All automation commands ready to use! Just type `make <command>`.

---

## ⚡ Your Top 3 Commands

```bash
# 1. Process your LLM architectures folder (FASTEST!)
make llm-arch

# 2. Process all folders in src/data/
make batch-topics-fast

# 3. Quick PDF from a file
make quick-pdf INPUT=src/data/file.pdf
```

---

## 🚀 Quick Command Reference

### Show All Commands
```bash
make help           # Show all available commands
make list-topics    # List your topic folders
```

### Process Single Folder
```bash
# Fast (reuse images) - RECOMMENDED
make process-folder-fast FOLDER=llm-architectures

# Or use shortcut
make llm-arch

# Full (generate images)
make process-folder FOLDER=llm-architectures
```

### Process All Folders
```bash
# Fast (reuse images)
make batch-topics-fast

# Full (generate images)
make batch-topics
```

### Quick PDF
```bash
make quick-pdf INPUT=src/data/file.pdf
```

---

## 📝 What Each Command Does

| Command | What It Does | Speed | Output |
|---------|--------------|-------|--------|
| `make llm-arch` | Process LLM architectures folder | ⚡ Fast | PDF + PPTX |
| `make process-folder-fast FOLDER=<name>` | Process folder, reuse images | ⚡ Fast | PDF + PPTX |
| `make process-folder FOLDER=<name>` | Process folder, generate images | 🐌 Slow | PDF + PPTX |
| `make batch-topics-fast` | Process all folders, reuse images | ⚡⚡ Fast | Multiple PDFs + PPTXs |
| `make batch-topics` | Process all folders, generate images | 🐌🐌 Very slow | Multiple PDFs + PPTXs |
| `make quick-pdf INPUT=<file>` | Single PDF with existing images | ⚡ Fast | 1 PDF |
| `make list-topics` | List available folders | Instant | List |

---

## 🎯 Common Scenarios

### Scenario 1: First Time Setup
```bash
make setup-docgen                          # Install dependencies
make process-folder FOLDER=llm-architectures   # Generate everything
```

### Scenario 2: Quick Iteration (You Have Images)
```bash
make llm-arch                              # Fast! 2-3 minutes
```

### Scenario 3: Add New Topic
```bash
mkdir src/data/new-topic
cp files... src/data/new-topic/
make process-folder-fast FOLDER=new-topic
```

### Scenario 4: Process Everything
```bash
make batch-topics-fast                     # Process all folders
```

---

## 🧹 Maintenance Commands

```bash
make clear-cache      # Clear content cache
make clear-images     # Clear generated images (careful!)
make clean-docgen     # Clean all generated files
```

---

## 💡 Pro Tips

1. **Always use `*-fast` commands** when you have existing images
2. **Use `make llm-arch`** for your LLM architectures folder (shortcut)
3. **Use `make batch-topics-fast`** to process all folders quickly
4. **Run `make list-topics`** to see available folders
5. **Keep images** in `src/output/images/` between runs

---

## 📖 Your Current Setup

```bash
# Check what you have
make list-topics

# Output shows:
📁 Available topic folders in src/data/:
llm-architectures

# Process it (fast!)
make llm-arch
```

---

## 🎬 Try It Now!

```bash
# 1. Show help
make help

# 2. List your folders
make list-topics

# 3. Process your LLM architectures folder (fast!)
make llm-arch

# Expected output:
⚡ Processing folder: llm-architectures
📝 Mode: Fast (reusing existing images)
...
✅ Complete! Output files:
-rw-r--r-- ... src/output/llm-architectures.pdf
-rw-r--r-- ... src/output/llm-architectures.pptx
```

---

## 📚 Documentation

- `MAKEFILE_COMMANDS.md` - Complete command reference
- `FOLDER_PROCESSING_QUICKSTART.md` - Folder processing guide
- `docs/guides/REUSING_IMAGES.md` - Image reuse guide

---

## Summary

✅ **Show commands:** `make help`  
✅ **Your folder:** `make llm-arch`  
✅ **All folders:** `make batch-topics-fast`  
✅ **Quick PDF:** `make quick-pdf INPUT=file.pdf`  

**Ready to go!** 🚀
