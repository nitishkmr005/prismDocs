# Document Generator Tasks

.PHONY: setup-docgen test-docgen lint-docgen run-docgen docker-build docker-run docker-compose-up clean-docgen help-docgen
.PHONY: process-folder process-folder-fast batch-topics batch-topics-fast quick-pdf clear-cache clear-images list-topics help
.DEFAULT_GOAL := help

# ============================================================================
# Help & Documentation
# ============================================================================

help:  ## Show all available commands (default)
	@$(MAKE) help-docgen

help-docgen:  ## Show all available document generator commands
	@echo "📄 Document Generator - Available Commands"
	@echo ""
	@echo "🚀 Quick Start:"
	@echo "  make process-folder-fast FOLDER=llm-architectures    # Fastest! Reuse images"
	@echo "  make batch-topics-fast                                # Process all folders (fast)"
	@echo "  make quick-pdf INPUT=file.pdf                         # PDF with existing images"
	@echo ""
	@echo "📁 Folder-Based Processing (Merge multiple files → 1 PDF + 1 PPTX):"
	@echo "  make process-folder FOLDER=<name>           # Full processing with images"
	@echo "  make process-folder-fast FOLDER=<name>      # Skip images (use existing)"
	@echo ""
	@echo "  Examples:"
	@echo "    make process-folder-fast FOLDER=llm-architectures"
	@echo "    make process-folder FOLDER=machine-learning"
	@echo ""
	@echo "🔄 Batch Processing (Process all folders in src/data/):"
	@echo "  make batch-topics                           # Full processing (slow)"
	@echo "  make batch-topics-fast                      # Reuse images (fast, recommended!)"
	@echo ""
	@echo "⚡ Quick PDF Generation (Skip image generation):"
	@echo "  make quick-pdf INPUT=<file>                 # Generate PDF with existing images"
	@echo "  Example: make quick-pdf INPUT=src/data/llm-architectures/slides.pdf"
	@echo ""
	@echo "📝 Single File Processing:"
	@echo "  make run-docgen INPUT=<file> OUTPUT=<pdf|pptx>"
	@echo "  bash run.sh <file>                          # Generate both PDF and PPTX"
	@echo ""
	@echo "⚙️  Setup & Configuration:"
	@echo "  make setup-docgen                           # Install all dependencies"
	@echo "  Create .env file with:                      # ANTHROPIC_API_KEY or OPENAI_API_KEY"
	@echo ""
	@echo "🐳 Docker:"
	@echo "  make docker-build                           # Build Docker image"
	@echo "  make docker-run INPUT=<file> OUTPUT=<format>"
	@echo ""
	@echo "🧹 Maintenance:"
	@echo "  make test-docgen                            # Run tests"
	@echo "  make lint-docgen                            # Lint and type check"
	@echo "  make clean-docgen                           # Clean generated files"
	@echo "  make clear-cache                            # Clear content cache"
	@echo "  make clear-images                           # Clear generated images"
	@echo ""
	@echo "📖 Documentation:"
	@echo "  FOLDER_PROCESSING_QUICKSTART.md             # Folder processing guide"
	@echo "  docs/guides/REUSING_IMAGES.md               # Image reuse guide"
	@echo "  README.md                                   # Full documentation"
	@echo ""

setup-docgen:  ## Setup document generator environment (local development)
	@echo "Setting up document generator..."
	@uv pip install -e ".[dev]"
	@echo "✅ Setup complete!"

test-docgen:  ## Run document generator tests
	@echo "Running tests..."
	@pytest tests/ -v --cov=src/doc_generator --cov-report=term-missing

lint-docgen:  ## Lint and type check document generator code
	@echo "Linting code..."
	@ruff check src/doc_generator
	@echo "Type checking..."
	@mypy src/doc_generator

run-docgen:  ## Run document generator (make run-docgen INPUT=file.md OUTPUT=pdf)
	@if [ -z "$(INPUT)" ]; then \
		echo "Usage: make run-docgen INPUT=<file> OUTPUT=<pdf|pptx>"; \
		echo "Example: make run-docgen INPUT=src/data/sample.md OUTPUT=pdf"; \
		exit 1; \
	fi
	@python scripts/run_generator.py $(INPUT) --output $(or $(OUTPUT),pdf)

docker-build:  ## Build Docker image for document generator
	@echo "Building Docker image..."
	@docker build -t doc-generator:latest .
	@echo "✅ Docker image built successfully"

docker-run:  ## Run in Docker (make docker-run INPUT=src/data/file.md OUTPUT=pdf)
	@if [ -z "$(INPUT)" ]; then \
		echo "Usage: make docker-run INPUT=<file> OUTPUT=<pdf|pptx>"; \
		echo "Example: make docker-run INPUT=src/data/sample.md OUTPUT=pdf"; \
		exit 1; \
	fi
	@docker run --rm \
		-v $(PWD)/src/data:/app/src/data \
		-v $(PWD)/src/output:/app/src/output \
		doc-generator:latest $(INPUT) --output $(or $(OUTPUT),pdf)

docker-compose-up:  ## Run with docker-compose
	@echo "Starting docker-compose..."
	@docker-compose up

# ============================================================================
# Folder-Based Processing Commands
# ============================================================================

process-folder:  ## Process a topic folder with full image generation (make process-folder FOLDER=<name>)
	@if [ -z "$(FOLDER)" ]; then \
		echo "❌ Usage: make process-folder FOLDER=<folder-name>"; \
		echo ""; \
		echo "Example:"; \
		echo "  make process-folder FOLDER=llm-architectures"; \
		echo ""; \
		echo "Available folders in src/data/:"; \
		find src/data -mindepth 1 -maxdepth 1 -type d -exec basename {} \; 2>/dev/null | sort; \
		exit 1; \
	fi
	@if [ ! -d "src/data/$(FOLDER)" ]; then \
		echo "❌ Folder not found: src/data/$(FOLDER)"; \
		echo ""; \
		echo "Available folders:"; \
		find src/data -mindepth 1 -maxdepth 1 -type d -exec basename {} \; 2>/dev/null | sort; \
		exit 1; \
	fi
	@echo "🚀 Processing folder: $(FOLDER)"
	@echo "📝 Mode: Full processing (with image generation)"
	@python scripts/generate_from_folder.py src/data/$(FOLDER)
	@echo ""
	@echo "✅ Complete! Output files:"
	@ls -lh src/output/$(FOLDER).pdf src/output/$(FOLDER).pptx 2>/dev/null || echo "  (check logs for errors)"

process-folder-fast:  ## Process a topic folder with existing images (FAST) (make process-folder-fast FOLDER=<name>)
	@if [ -z "$(FOLDER)" ]; then \
		echo "❌ Usage: make process-folder-fast FOLDER=<folder-name>"; \
		echo ""; \
		echo "Example:"; \
		echo "  make process-folder-fast FOLDER=llm-architectures"; \
		echo ""; \
		echo "Available folders in src/data/:"; \
		find src/data -mindepth 1 -maxdepth 1 -type d -exec basename {} \; 2>/dev/null | sort; \
		exit 1; \
	fi
	@if [ ! -d "src/data/$(FOLDER)" ]; then \
		echo "❌ Folder not found: src/data/$(FOLDER)"; \
		echo ""; \
		echo "Available folders:"; \
		find src/data -mindepth 1 -maxdepth 1 -type d -exec basename {} \; 2>/dev/null | sort; \
		exit 1; \
	fi
	@echo "⚡ Processing folder: $(FOLDER)"
	@echo "📝 Mode: Fast (reusing existing images)"
	@python scripts/generate_from_folder.py src/data/$(FOLDER) --skip-images
	@echo ""
	@echo "✅ Complete! Output files:"
	@ls -lh src/output/$(FOLDER).pdf src/output/$(FOLDER).pptx 2>/dev/null || echo "  (check logs for errors)"

batch-topics:  ## Process all topic folders with full image generation
	@echo "🔄 Batch processing all topics in src/data/"
	@echo "📝 Mode: Full processing (with image generation)"
	@echo "⚠️  This may take a while..."
	@echo ""
	@python scripts/batch_process_topics.py
	@echo ""
	@echo "✅ Batch processing complete!"
	@echo "📂 Check src/output/ for generated files"

batch-topics-fast:  ## Process all topic folders with existing images (FAST - RECOMMENDED)
	@echo "⚡ Batch processing all topics in src/data/"
	@echo "📝 Mode: Fast (reusing existing images)"
	@echo ""
	@python scripts/batch_process_topics.py --skip-images
	@echo ""
	@echo "✅ Batch processing complete!"
	@echo "📂 Check src/output/ for generated files"

# ============================================================================
# Quick PDF Generation (Skip image generation)
# ============================================================================

quick-pdf:  ## Generate PDF with existing images (make quick-pdf INPUT=<file>)
	@if [ -z "$(INPUT)" ]; then \
		echo "❌ Usage: make quick-pdf INPUT=<file>"; \
		echo ""; \
		echo "Examples:"; \
		echo "  make quick-pdf INPUT=src/data/llm-architectures/slides.pdf"; \
		echo "  make quick-pdf INPUT=src/data/document.md"; \
		exit 1; \
	fi
	@if [ ! -f "$(INPUT)" ]; then \
		echo "❌ File not found: $(INPUT)"; \
		exit 1; \
	fi
	@echo "⚡ Quick PDF generation (reusing existing images)"
	@echo "📄 Input: $(INPUT)"
	@python scripts/quick_pdf_with_images.py "$(INPUT)"

# ============================================================================
# Cache Management
# ============================================================================

clear-cache:  ## Clear content cache files
	@echo "🗑️  Clearing content cache..."
	@rm -rf src/output/cache/*.json
	@echo "✅ Content cache cleared!"

clear-images:  ## Clear generated images (WARNING: Images will need to be regenerated)
	@echo "⚠️  WARNING: This will delete all generated images!"
	@echo "Images in src/output/images/ will be removed."
	@read -p "Are you sure? (y/N): " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		rm -rf src/output/images/*.png; \
		rm -rf src/output/pdf_images/*.png; \
		echo "✅ Images cleared!"; \
	else \
		echo "❌ Cancelled"; \
	fi

list-topics:  ## List all available topic folders
	@echo "📁 Available topic folders in src/data/:"
	@find src/data -mindepth 1 -maxdepth 1 -type d -exec basename {} \; 2>/dev/null | sort || echo "  (no folders found)"

# ============================================================================
# Convenient Shortcuts
# ============================================================================

llm-arch:  ## Shortcut: Process llm-architectures folder (fast, with image reuse)
	@$(MAKE) process-folder-fast FOLDER=llm-architectures

llm-arch-full:  ## Shortcut: Process llm-architectures folder (full, with image generation)
	@$(MAKE) process-folder FOLDER=llm-architectures

# ============================================================================
# Cleanup
# ============================================================================

clean-docgen:  ## Clean document generator files and caches
	@echo "Cleaning generated files..."
	@rm -rf src/output/*
	@rm -rf **/__pycache__
	@rm -rf .pytest_cache
	@rm -rf .ruff_cache
	@rm -rf .mypy_cache
	@rm -rf *.egg-info
	@echo "✅ Cleaned!"

example-md-to-pdf:  ## Example: Convert markdown to PDF
	@echo "Example: Converting markdown to PDF..."
	@python scripts/run_generator.py README.md --output pdf

example-url-to-pptx:  ## Example: Convert web article to PPTX
	@echo "Example: Converting web article to PPTX..."
	@python scripts/run_generator.py https://example.com --output pptx

run-llm-architectures:  ## DEPRECATED: Use 'make llm-arch' or 'make process-folder-fast FOLDER=llm-architectures'
	@echo "⚠️  DEPRECATED: This command is deprecated"
	@echo "📝 Use instead:"
	@echo "   make llm-arch                                    # Fast (reuse images)"
	@echo "   make process-folder-fast FOLDER=llm-architectures"
	@echo ""
	@echo "Redirecting to new command..."
	@$(MAKE) llm-arch
