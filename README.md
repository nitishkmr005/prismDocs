# Document Generator

LangGraph-based document generator for converting multiple input formats (PDF, Markdown, TXT, web articles) into PDF and PPTX outputs using 100% Python implementation.

## Table of Contents
- [Features](#features)
- [Architecture](#architecture)
- [Process Flow](#process-flow)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Docker Deployment](#docker-deployment)
- [Development](#development)
- [Project Structure](#project-structure)
- [Testing](#testing)

## Features

✅ **Multiple Input Formats**:
- PDF documents (with OCR support via Docling)
- Markdown files (.md) with frontmatter support
- Plain text files (.txt)
- DOCX, PPTX, XLSX documents
- Web articles (URLs)
- Images (PNG, JPG, TIFF)

✅ **Multiple Output Formats**:
- PDF (ReportLab with custom styling)
- PPTX (python-pptx for PowerPoint)

✅ **Advanced Features**:
- Advanced PDF parsing with IBM's Docling (OCR, table extraction, layout analysis)
- Web content extraction with Microsoft's MarkItDown
- LangGraph workflow orchestration
- Automatic retry on generation errors (max 3 attempts)
- Comprehensive error handling and logging
- Docker containerization for portability

✅ **Pure Python**:
- No Node.js dependencies
- Runs on Python 3.11+
- Fully containerized with Docker

## Architecture

**Hybrid Clean Architecture** combining:
- **Domain Layer**: Pure business logic (models, enums, exceptions, interfaces)
- **Application Layer**: Use case orchestration (parsers, generators, LangGraph nodes)
- **Infrastructure Layer**: External integrations (Docling, MarkItDown, file I/O)

**LangGraph Workflow**:
```
detect_format → parse_content → transform_content → generate_output → validate_output
                                                                              ↓
                                                                    (retry on error, max 3x)
```

## Process Flow

For a comprehensive visual guide to the entire document generation process, see **[docs/PROCESS_FLOW.md](docs/PROCESS_FLOW.md)**.

This includes detailed diagrams for:
- 🔄 Complete architecture overview
- 📥 Input detection and parsing
- 🤖 LLM content transformation
- 🎨 Visual and image generation
- 📄 PDF/PPTX output creation
- 🔁 Validation and retry logic
- 📁 Folder-based processing
- 🛠️ Technology stack flow

## Tech Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Document Parsing** | Docling | 2.66.0 | Advanced PDF/DOCX/PPTX parsing with OCR |
| **Document Conversion** | MarkItDown | 0.0.1a2 | HTML/web articles to Markdown |
| **PDF Generation** | ReportLab | 4.2.5 | Professional PDF creation |
| **PPTX Generation** | python-pptx | 1.0.2 | PowerPoint presentations |
| **Workflow Orchestration** | LangGraph | 0.2.55 | State machine workflow |
| **Validation** | Pydantic | 2.10.5 | Data validation |
| **Logging** | Loguru | 0.7.3 | Structured logging |
| **Package Manager** | uv | latest | Fast Python package installation |

## Installation

### Local Development

1. **Prerequisites**:
   - Python 3.11+
   - `uv` package manager ([install uv](https://github.com/astral-sh/uv))

2. **Install dependencies**:
   ```bash
   make setup-docgen
   ```

   Or manually:
   ```bash
   uv pip install -e ".[dev]"
   ```

3. **Configure API Keys** (Optional - for LLM-enhanced features):
   Create a `.env` file in the project root:
   ```bash
   # Claude API (Recommended for visuals)
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   
   # Or OpenAI API
   OPENAI_API_KEY=your_openai_api_key_here
   ```
   
   See `ENV_SETUP.md` for detailed configuration options.

### Docker (Recommended for Production)

1. **Build Docker image**:
   ```bash
   make docker-build
   ```

   Or manually:
   ```bash
   docker build -t doc-generator:latest .
   ```

## Configuration

### API Keys (Optional)

The system supports multiple LLM providers for enhanced content transformation:

1. **Claude (Anthropic)** - Recommended for visual generation
   ```bash
   ANTHROPIC_API_KEY=your_key_here
   # or
   CLAUDE_API_KEY=your_key_here
   ```

2. **OpenAI** - Alternative LLM provider
   ```bash
   OPENAI_API_KEY=your_key_here
   ```

**Priority**: Claude > OpenAI > No LLM (basic mode)

Create a `.env` file with your API key to enable LLM-enhanced features:
- Executive summaries
- Intelligent slide generation
- Content transformation
- Visual diagram generation

### Settings File

Edit `config/settings.yaml` to customize:
- Page layouts and margins
- Color themes
- LLM parameters
- Retry limits

## Usage

### Command Line (Local)

**Quick Start - Process Entire Folder**:
```bash
# Process LLM architectures folder (generates both PDF and PPTX)
make run-llm-architectures

# Or use the shell script directly
bash run.sh src/data/llm-architectures --verbose
```

**Single File Processing**:
```bash
# Using make (single output format)
make run-docgen INPUT=src/data/article.md OUTPUT=pdf

# Using run.sh (generates both PDF and PPTX)
bash run.sh src/data/article.md --verbose

# Using Python directly
python scripts/run_generator.py src/data/article.md --output pdf
```

**Folder Processing**:
```bash
# Process all files in a folder
python scripts/generate_from_folder.py src/data/llm-architectures --verbose

# The script will:
# 1. Parse all supported files (PDF, MD, TXT, DOCX, PPTX)
# 2. Merge content intelligently
# 3. Generate both PDF and PPTX outputs
```

**More Examples**:
```bash
# Web article to PPTX
python scripts/run_generator.py https://example.com/article --output pptx

# PDF to PPTX (extract and convert)
python scripts/run_generator.py src/data/document.pdf --output pptx

# With verbose logging
python scripts/run_generator.py input.md --output pdf --verbose

# With log file
python scripts/run_generator.py input.md --output pdf --log-file output.log
```

### Docker Usage

**Direct Docker run**:
```bash
# Markdown to PDF
docker run --rm \
  -v $(pwd)/src/data:/app/src/data \
  -v $(pwd)/src/output:/app/src/output \
  doc-generator:latest src/data/article.md --output pdf

# Web article to PPTX (no input mount needed)
docker run --rm \
  -v $(pwd)/src/output:/app/src/output \
  doc-generator:latest https://example.com/article --output pptx
```

**Using Makefile**:
```bash
make docker-run INPUT=src/data/article.md OUTPUT=pdf
```

**Using Docker Compose**:

1. Edit `docker-compose.yaml` to set the command:
   ```yaml
   command: ["src/data/sample.md", "--output", "pdf"]
   ```

2. Run:
   ```bash
   make docker-compose-up
   # or
   docker-compose up
   ```

### Python API

```python
from doc_generator.application.graph_workflow import run_workflow

# Run workflow
result = run_workflow(
    input_path="src/data/article.md",
    output_format="pdf"
)

# Check results
if result["errors"]:
    print(f"Errors: {result['errors']}")
else:
    print(f"Generated: {result['output_path']}")
```

### FastAPI API

Run the API (see `src/doc_generator/infrastructure/api/main.py` for app wiring), then use:

**1) Upload a file**
```bash
curl -sS -X POST http://localhost:8000/api/upload \
  -F "file=@/path/to/input.pdf"
```
Response:
```json
{"file_id":"f_abc123","filename":"input.pdf","size":12345,"mime_type":"application/pdf","expires_in":3600}
```

**2) Generate PDF or PPTX (SSE stream)**
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

**3) Download the generated file**
```bash
curl -L -o output.pdf "http://localhost:8000/api/download/f_abc123/pdf/your-file.pdf"
```
You can also use the `download_url` directly if you want the tokenized link.

**Headers by provider**
- Gemini: `X-Google-Key`
- OpenAI: `X-OpenAI-Key`
- Anthropic: `X-Anthropic-Key`

## Docker Deployment

### Building for Production

```bash
# Build image
docker build -t doc-generator:latest .

# Tag for registry
docker tag doc-generator:latest your-registry/doc-generator:v1.0.0

# Push to registry
docker push your-registry/doc-generator:v1.0.0
```

### Running in Production

```bash
# Run with volume mounts
docker run -d \
  --name doc-generator \
  -v /path/to/data:/app/src/data \
  -v /path/to/output:/app/src/output \
  -e LOG_LEVEL=INFO \
  doc-generator:latest src/data/input.md --output pdf
```

## Development

### Setup Development Environment

```bash
# Install dependencies with dev extras
make setup-docgen

# Or manually
uv pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests with coverage
make test-docgen

# Or manually
pytest tests/ -v --cov=src/doc_generator --cov-report=term-missing
```

### Linting and Type Checking

```bash
# Lint and type check
make lint-docgen

# Or manually
ruff check src/doc_generator
mypy src/doc_generator
```

### Cleaning Generated Files

```bash
# Clean output and cache files
make clean-docgen
```

## Project Structure

```
src/doc_generator/
├── domain/                           # Core business logic (zero dependencies)
│   ├── models.py                     # Pydantic models (WorkflowState, Config)
│   ├── content_types.py              # Enums (ContentFormat, OutputFormat)
│   ├── exceptions.py                 # Custom exceptions
│   └── interfaces.py                 # Protocols (ContentParser, OutputGenerator)
│
├── application/                      # Use case orchestration
│   ├── graph_workflow.py             # LangGraph state machine
│   ├── parsers/                      # Input parsers
│   │   ├── unified_parser.py         # Docling-based parser (PDF, DOCX, PPTX)
│   │   ├── markdown_parser.py        # Markdown with frontmatter support
│   │   └── web_parser.py             # MarkItDown-based web parser
│   ├── generators/
│   │   ├── pdf_generator.py          # ReportLab PDF generation
│   │   └── pptx_generator.py         # python-pptx PPTX generation
│   └── nodes/                        # LangGraph nodes
│       ├── detect_format.py          # Format detection
│       ├── parse_content.py          # Content parsing
│       ├── transform_content.py      # Content transformation
│       ├── generate_output.py        # Document generation
│       └── validate_output.py        # Output validation
│
├── infrastructure/                   # External integrations
│   ├── docling_adapter.py            # Docling wrapper
│   ├── markitdown_adapter.py         # MarkItDown wrapper
│   ├── file_system.py                # File I/O operations
│   ├── pdf_utils.py                  # ReportLab utilities
│   ├── pptx_utils.py                 # python-pptx utilities
│   └── logging_config.py             # Loguru configuration
│
└── utils/                            # Shared utilities

scripts/
└── run_generator.py                  # CLI entry point

tests/                                # Test suite
├── test_parsers.py
├── test_generators.py
└── test_workflow.py

config/
└── settings.yaml                     # Configuration

Dockerfile                            # Docker image definition
docker-compose.yaml                   # Docker Compose configuration
pyproject.toml                        # Python dependencies
Makefile                              # Automation tasks
```

## Testing

### Unit Tests

Test individual components:
```bash
pytest tests/test_parsers.py -v
pytest tests/test_generators.py -v
```

### Integration Tests

Test end-to-end workflows:
```bash
pytest tests/test_workflow.py -v
```

### Manual Testing

```bash
# Test markdown to PDF
make run-docgen INPUT=README.md OUTPUT=pdf

# Check output
ls -lh src/output/*.pdf
```

## Advanced Configuration

Configuration is managed through `config/settings.yaml` and `.env` file:

```yaml
generator:
  input_dir: "src/data"
  output_dir: "src/output"
  default_output_format: "pdf"
  max_retries: 3

logging:
  level: "INFO"

pdf:
  page_size: "letter"
  margin:
    top: 72
    bottom: 18
    left: 72
    right: 72

pptx:
  layout: "LAYOUT_16x9"
  slide_width: 960
  slide_height: 540
```

## Troubleshooting

### Common Issues

**ImportError: Docling not available**:
```bash
# Install Docling explicitly
uv pip install docling==2.66.0
```

**ImportError: MarkItDown not available**:
```bash
# Install MarkItDown with all extras
uv pip install "markitdown[all]==0.0.1a2"
```

**Docker build fails**:
```bash
# Rebuild without cache
docker build --no-cache -t doc-generator:latest .
```

**Permission denied on output directory**:
```bash
# Fix permissions
chmod 755 src/output
```

## Contributing

1. Follow the clean architecture pattern
2. Add type hints to all functions
3. Write comprehensive docstrings
4. Add unit tests for new features
5. Update README with new capabilities

## License

MIT License - See LICENSE file for details

## Acknowledgments

- **Docling** by IBM Research - Advanced document parsing
- **MarkItDown** by Microsoft - Document-to-markdown conversion
- **ReportLab** - Professional PDF generation
- **python-pptx** - PowerPoint presentations
- **LangGraph** - Workflow orchestration
