<div align="center">

```
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   ██████╗  ██████╗  ██████╗ ██████╗ ███████╗███╗   ██╗             ║
║   ██╔══██╗██╔═══██╗██╔════╝██╔════╝ ██╔════╝████╗  ██║             ║
║   ██║  ██║██║   ██║██║     ██║  ███╗█████╗  ██╔██╗ ██║             ║
║   ██║  ██║██║   ██║██║     ██║   ██║██╔══╝  ██║╚██╗██║             ║
║   ██████╔╝╚██████╔╝╚██████╗╚██████╔╝███████╗██║ ╚████║             ║
║   ╚═════╝  ╚═════╝  ╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝             ║
║                                                                      ║
║          AI-Powered Document Generation Toolkit                     ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
```

### Transform any content into professional documents with AI

**From Research Papers to Pitch Decks • From Web Articles to Study Guides**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128-009688.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.55-purple.svg)](https://github.com/langchain-ai/langgraph)

Built on **LangGraph**, **Docling**, and modern LLMs • Clean Architecture • Type-Safe • Extensible

<p align="center">
  <a href="#-quick-start"><b>Quick Start</b></a> •
  <a href="#-use-cases-by-role"><b>Use Cases</b></a> •
  <a href="#-api-usage"><b>API</b></a> •
  <a href="#-architecture"><b>Architecture</b></a> •
  <a href="#-roadmap"><b>Roadmap</b></a>
</p>

</div>

---

## 📋 Table of Contents

- [✨ Use Cases by Role](#-use-cases-by-role)
- [🎯 What DocGen Does](#-what-docgen-does)
- [🏗️ Architecture](#️-architecture)
- [🚀 Quick Start](#-quick-start)
- [📡 API Usage](#-api-usage)
- [🗺️ Roadmap](#️-roadmap)
- [🛠️ Development](#️-development)
- [🙏 Acknowledgments](#-acknowledgments)

---

## ✨ Use Cases by Role

**DocGen adapts to your workflow, no matter your role.**

<table>
<tr>
<td width="50%" valign="top">

### 👨‍💼 **For Executives & Business Leaders**
> *"Create consistent, on-brand presentations in minutes"*

**What You Can Do:**
- 📊 Transform meeting notes → Pitch decks
- 🎨 Brand-consistent presentations
- 📄 Executive summaries from long reports
- 📈 Data reports → Visual dashboards

**Key Features:** Style enforcement, PPTX templates, multi-source synthesis

</td>
<td width="50%" valign="top">

### 🎓 **For Students & Researchers**
> *"Turn research papers into study materials automatically"*

**What You Can Do:**
- 📚 PDF papers → Study guides + flashcards
- 🔬 arXiv formatting for submissions
- 📝 Literature reviews from multiple sources
- ❓ Auto-generate FAQ docs from lectures

**Key Features:** Multi-format parsing, intelligent summarization, citation handling

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 💼 **For Job Seekers & Career Professionals**
> *"Generate professional resumes and interview prep in one click"*

**What You Can Do:**
- 📋 Professional resume generation
- 💬 Interview Q&A preparation docs
- 🎯 Tailored cover letters
- 📊 Portfolio presentations

**Key Features:** Professional templates, Q&A formatting, PDF/PPTX output

</td>
<td width="50%" valign="top">

### 🎨 **For Content Creators & Marketers**
> *"Scale your content production with AI"*

**What You Can Do:**
- 🎙️ Blog posts → Podcast scripts
- 🖼️ YouTube thumbnails generation
- 📱 Social media content packages
- 📊 Marketing decks from reports

**Key Features:** Image generation, audio synthesis, multi-format export

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 👨‍💻 **For Developers & Technical Writers**
> *"Documentation that writes itself"*

**What You Can Do:**
- 📖 Code → Technical documentation
- 🔀 API documentation generation
- 📊 Architecture diagrams (Mermaid)
- 📝 Markdown with syntax highlighting

**Key Features:** Code block support, diagram generation, version control friendly

</td>
<td width="50%" valign="top">

### 🏢 **For Teams & Enterprises**
> *"Scalable document generation infrastructure"*

**What You Can Do:**
- 🔄 Automated report generation
- 🏭 High-volume processing
- 🔐 Self-hosted deployment
- 🔌 API-first integration

**Key Features:** Docker support, REST API, caching, retry logic, observability

</td>
</tr>
</table>

---

## 🎯 What DocGen Does

### System Overview

```
┌─────────────────────┐       ┌────────────────────────┐       ┌─────────────────────┐
│                     │       │                        │       │                     │
│   INPUT SOURCES     │──────▶│   LANGGRAPH WORKFLOW   │──────▶│      OUTPUTS        │
│                     │       │                        │       │                     │
│  📄 PDF Documents   │       │  1️⃣  Detect Format     │       │  📕 PDF Reports     │
│  📝 Markdown Files  │       │  2️⃣  Parse Content     │       │  📊 PPTX Slides     │
│  🌐 Web URLs        │       │  3️⃣  Transform (LLM)   │       │  📝 Markdown Docs   │
│  📊 DOCX/XLSX       │       │  4️⃣  Generate Output   │       │  ❓ FAQ Documents   │
│  🖼️  Images (OCR)   │       │  5️⃣  Validate Result   │       │  🎙️  Podcasts*      │
│  📋 Plain Text      │       │                        │       │                     │
│                     │       │   🔄 Auto-retry (3x)   │       │                     │
└─────────────────────┘       └────────────────────────┘       └─────────────────────┘
                                         │
                              ┌──────────┴──────────┐
                              │                     │
                       ┌──────▼──────┐      ┌──────▼──────┐
                       │   Docling   │      │   LLM APIs  │
                       │  OCR+Parse  │      │   Synthesis │
                       └─────────────┘      └──────┬──────┘
                                                   │
                                            ┌──────▼──────┐
                                            │   Image Gen │
                                            │Gemini/DALL-E│
                                            └─────────────┘

        Powered by: Claude • Gemini • OpenAI • Docling • ReportLab
```

### Core Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Workflow Engine** | LangGraph 0.2.55 | State machine orchestration with retry logic |
| **Document Parsing** | Docling 2.66.0 (IBM Research) | Advanced OCR, table extraction, layout analysis |
| **LLM Synthesis** | Claude/Gemini/OpenAI | Content transformation and intelligent summarization |
| **Image Generation** | Gemini/DALL-E | AI-generated visuals and diagrams |
| **PDF Generation** | ReportLab 4.2.5 | Professional PDF rendering with custom styling |
| **PPTX Generation** | python-pptx 1.0.2 | PowerPoint presentations with 16:9 layouts |
| **Architecture** | Clean Architecture | Domain/Application/Infrastructure layers (zero circular deps) |

### Two Ways to Use DocGen

| Method | Status | Best For |
|--------|--------|----------|
| **🐍 Python Package** | Coming Soon | Programmatic access, scripts, automation |
| **🌐 Web UI + API** | ✅ Available Now | Interactive use, team collaboration |

```python
# Coming Soon: Python Package
pip install docgen

from docgen import Generator

generator = Generator(api_key="your-api-key")
result = generator.create(
    sources=["paper.pdf", "https://blog.com/article", "notes.md"],
    output_format="pdf",
    image_generation=True
)
```

### 📥 Multi-Format Input Parsing

Ingest and normalize content from diverse sources with intelligent extraction:

| Format | Parser | Capabilities |
|--------|--------|--------------|
| **PDF** | Docling | OCR, table extraction, layout analysis, image extraction |
| **Markdown** | Native | Frontmatter support, code blocks, nested structures |
| **Web URLs** | MarkItDown | Article extraction, metadata parsing, link resolution |
| **Office Docs** | Docling | DOCX, PPTX, XLSX with formatting preservation |
| **Images** | Docling | PNG, JPG, TIFF with OCR and layout detection |
| **Plain Text** | Native | TXT files with encoding detection |

### 🤖 AI-Powered Synthesis

- **Content Transformation:** LLM-driven summarization, restructuring, and style adaptation
- **Visual Generation:** Context-aware diagrams, charts, and illustrations via Gemini/DALL-E
- **Intelligent Merging:** Multi-source synthesis with conflict resolution and deduplication
- **Slide Generation:** Automatic PPTX layouts with bullet points, titles, and visuals

### 📤 Professional Output Formats

- **PDF:** ReportLab-based generation with custom styling, headers, footers, and TOC
- **PPTX:** python-pptx presentations with 16:9 layouts and embedded images
- **Markdown:** Structured docs with frontmatter and proper heading hierarchy
- **FAQ Docs:** Q&A format generation from input content
- **Podcasts:** MP3 audio generation (coming soon)

### ⚡ Production-Ready Features

- **LangGraph Workflow:** State machine with automatic retry (max 3 attempts) on failures
- **Caching:** Content and image caching to reduce LLM costs and latency
- **Logging:** Structured logging with Loguru for observability
- **Type Safety:** Pydantic validation throughout the pipeline
- **Docker Support:** Containerized backend and frontend for easy deployment
- **BYO API Keys:** Users bring their own LLM credentials (Claude, Gemini, OpenAI)

---

## 🏗️ Architecture

DocGen follows **Hybrid Clean Architecture** for maintainability, testability, and extensibility.

### Clean Architecture Layers

```
backend/doc_generator/
│
├── 🎯 domain/              # Pure business logic (zero dependencies)
│   ├── models.py           # Core entities: Document, Content, Output
│   ├── enums.py            # InputFormat, OutputFormat, ProcessingStatus
│   ├── exceptions.py       # Custom exceptions with error codes
│   └── interfaces.py       # Abstract interfaces for parsers/generators
│
├── 🔄 application/         # Use case orchestration
│   ├── parsers/            # Format-specific parsing implementations
│   ├── generators/         # Output format generators
│   ├── graph_workflow.py   # LangGraph state machine
│   └── nodes/              # Workflow nodes (parse, transform, generate)
│
└── 🔌 infrastructure/      # External integrations
    ├── docling/            # Docling integration for parsing
    ├── markitdown/         # MarkItDown for web content
    ├── llm/                # LLM providers (Claude, Gemini, OpenAI)
    ├── image/              # Image generation services
    ├── api/                # FastAPI endpoints and routes
    └── settings.py         # Config management (YAML + env)
```

### LangGraph Workflow

The workflow uses a state machine with **automatic retry logic** (up to 3 attempts):

```mermaid
graph LR
    A[START] --> B[detect_format]
    B --> C[parse_content]
    C --> D[transform_content]
    D --> E[generate_output]
    E --> F[validate_output]
    F --> G[END]
    E -.retry on error.-> D
```

**Node Responsibilities:**
- `detect_format`: Identify input type (PDF, MD, URL, etc.)
- `parse_content`: Extract raw content using appropriate parser
- `transform_content`: LLM synthesis + image generation
- `generate_output`: Render PDF/PPTX/MD using templates
- `validate_output`: Check file integrity and completeness

### Configuration Management

| Type | Location | Purpose |
|------|----------|---------|
| **YAML Config** | `backend/config/settings.yaml` | Defaults (page layouts, colors, LLM params) |
| **Environment Variables** | `.env` | Secrets (API keys, database URLs) |
| **Pydantic Settings** | Runtime | Type-safe config with validation and auto-reload |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker (for containerized deployment)
- LLM API key (Claude, Gemini, or OpenAI)

### Option 1: Web UI (Fastest) ⚡

**Run with Docker Compose:**
```bash
# Clone the repo
git clone https://github.com/your-org/docgen.git
cd docgen

# Start backend + frontend
docker-compose up --build

# Open http://localhost:3000
```

**Or deploy to cloud:**
- **Backend:** Deploy to [Render](https://render.com) using `backend/render.yaml`
- **Frontend:** Deploy to [Vercel](https://vercel.com) using `vercel.json`

### Option 2: Python Package (Coming Soon) 🐍

```python
pip install docgen

from docgen import Generator

# Initialize with your API key
generator = Generator(api_key="your-claude-key")

# Generate from multiple sources
result = generator.create(
    sources=["paper.pdf", "https://blog.com/article", "notes.md"],
    output_format="pdf",
    image_generation=True
)

print(f"Generated: {result.output_path}")
```

### Option 3: Local Development 💻

```bash
# Install dependencies with uv
make setup

# Configure API keys
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY or OPENAI_API_KEY

# Run generation
make run-docgen INPUT=sample.md OUTPUT=pdf

# Start FastAPI backend
cd backend
uvicorn doc_generator.infrastructure.api.main:app --reload

# Start Next.js frontend (separate terminal)
cd frontend
npm install && npm run dev
```

### Configuration

**Backend config** (`backend/config/settings.yaml`):
```yaml
generator:
  output_dir: "data/output"
  max_retries: 3

pdf:
  page_size: "letter"
  margin: {top: 72, bottom: 18, left: 72, right: 72}

pptx:
  layout: "LAYOUT_16x9"
  slide_width: 960
  slide_height: 540
```

**Environment variables** (`.env`):
```bash
# LLM API Keys (choose one or more)
ANTHROPIC_API_KEY=your_claude_key
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_gemini_key

# Optional: Database (coming soon)
DATABASE_URL=postgresql://user:pass@localhost/docgen
```

---

## 📡 API Usage

DocGen exposes a FastAPI backend for programmatic document generation.

### Authentication (Coming Soon)
API authentication with user-managed API keys is planned. Currently, bring your own LLM keys via headers.

### Generate Documents (SSE Stream)

**Endpoint:** `POST /api/generate`

**Headers:**
```bash
Content-Type: application/json
X-Anthropic-Key: your_claude_key     # For Claude
X-OpenAI-Key: your_openai_key        # For OpenAI
X-Google-Key: your_gemini_key        # For Gemini
```

**Request Body:**
```json
{
  "output_format": "pdf",
  "provider": "gemini",
  "model": "gemini-2.0-flash-exp",
  "image_model": "imagen-3.0-generate-001",
  "sources": [
    {"type": "file", "file_id": "f_abc123"},
    {"type": "url", "url": "https://arxiv.org/pdf/2301.07041"},
    {"type": "text", "content": "Additional context to include"}
  ],
  "cache": {"reuse": true}
}
```

**Response:** Server-Sent Events (SSE) stream

```bash
curl -N -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -H "X-Google-Key: $GEMINI_API_KEY" \
  -d '{
    "output_format": "pdf",
    "provider": "gemini",
    "sources": [{"type": "url", "url": "https://example.com/article"}]
  }'
```

**Stream Events:**
```
event: progress
data: {"message": "Parsing PDF...", "progress": 20}

event: progress
data: {"message": "Generating images...", "progress": 60}

event: complete
data: {"download_url": "/api/download/f_abc/pdf/output.pdf", "file_path": "f_abc/pdf/output.pdf"}
```

### Other Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/upload` | POST | Upload files for processing |
| `/api/download/{file_id}/{format}/{filename}` | GET | Download generated files |
| `/api/health` | GET | Health check endpoint |

📖 **Full API documentation:** Available at `/docs` when running the backend

---

## 🗺️ Roadmap

DocGen is under active development with ambitious plans for new capabilities. Our vision is to become the **go-to toolkit for AI-powered document generation** across all industries and use cases.

### Development Timeline

```
2026 Q1                    Q2                     Q3                     Q4
  │                        │                      │                      │
  ├─ Phase 1 ─────────────┤                      │                      │
  │  🎨 Enhanced Generation│                      │                      │
  │  ✅ Podcast MP3        │                      │                      │
  │  ⏳ Mind maps          │                      │                      │
  │  ⏳ Code blocks        │                      │                      │
  │                        │                      │                      │
  │                        ├─ Phase 2 ───────────┤                      │
  │                        │  🔧 UI/UX Excellence │                      │
  │                        │  ⏳ API key vault    │                      │
  │                        │  ⏳ Real-time preview│                      │
  │                        │  📋 Template library │                      │
  │                        │                      │                      │
  │                        │  📄 Phase 3 ─────────┤                      │
  │                        │  Template Library    │                      │
  │                        │  📋 Resumes (5+)     │                      │
  │                        │  📋 arXiv papers     │                      │
  │                        │  📋 Creative designs │                      │
  │                        │                      │                      │
  │                        │                      ├─ Phase 4 ───────────┤
  │                        │                      │  🚀 Enterprise Ready │
  │                        │                      │  📦 PyPI package     │
  │                        │                      │  🔐 Authentication   │
  │                        │                      │  ☁️  Cloud optimize  │
  └────────────────────────┴──────────────────────┴──────────────────────┘

Legend: ✅ Complete  ⏳ In Progress  📋 Planned
```

### 🎯 Feature Categories

<details>
<summary><b>🎨 Enhanced Generation</b> (expand to see details)</summary>

**Content & Media:**
- ⏳ **Podcast MP3 generation** - Multi-voice support with ElevenLabs/Azure TTS
- 📋 **Mind maps** - Visual hierarchy with D3.js/Mermaid
- 📋 **FAQ cards** - Structured Q&A with auto-formatting
- 📋 **SVG diagram generation** - Technical diagrams from text
- ✅ **Image generation toggle** - Per-request control

**Developer Tools:**
- ⏳ **Advanced code blocks** - Syntax highlighting + line numbers
- ⏳ **Mermaid diagrams** - Flowcharts, sequence diagrams, ER diagrams
- 📋 **API documentation** - OpenAPI/Swagger to markdown
- 📋 **Architecture diagrams** - Auto-generate from code

</details>

<details>
<summary><b>🔧 UI/UX Improvements</b> (expand to see details)</summary>

**User Experience:**
- ⏳ **API key vault** - Secure multi-provider key management
- ⏳ **Real-time preview** - See documents as they generate
- 📋 **Batch processing** - Process multiple files at once
- 📋 **Cache management** - One-click cleanup utilities
- 📋 **Generation history** - Track past generations

**Marketplace:**
- 📋 **Template library** - 50+ pre-built templates
- 📋 **Community templates** - Share and discover
- 📋 **Style customization** - Brand colors, fonts, layouts
- 📋 **Template versioning** - Track changes, rollback

</details>

<details>
<summary><b>📄 Document Templates</b> (expand to see details)</summary>

**Professional:**
- 📋 **Resumes** - Tech, Marketing, Finance, Academic, Creative
- 📋 **Research papers** - arXiv, IEEE, ACM, Nature formats
- 📋 **Pitch decks** - Startup, Sales, Investor presentations
- 📋 **Reports** - Annual, Quarterly, Project status

**Creative & Personal:**
- 📋 **Wedding cards** - Invitations, save-the-dates, programs
- 📋 **YouTube thumbnails** - 10+ design styles
- 📋 **Social media** - Instagram posts, Twitter threads
- 📋 **Study materials** - Flashcards, summaries, notes

</details>

<details>
<summary><b>🚀 Platform & Scale</b> (expand to see details)</summary>

**Distribution:**
- 📋 **PyPI package** - `pip install docgen` with CLI
- 📋 **Docker Hub** - Pre-built images for all platforms
- 📋 **npm package** - JavaScript/TypeScript SDK
- 📋 **GitHub Action** - CI/CD integration

**Enterprise Features:**
- 📋 **Authentication** - OAuth2, SSO, API keys
- 📋 **User management** - Teams, roles, permissions
- 📋 **Rate limiting** - Per-user, per-tier quotas
- 📋 **Usage analytics** - Cost tracking, insights
- 📋 **White-labeling** - Custom branding, domains

</details>

---

## 🛠️ Development

### Setup Development Environment

```bash
# Clone and install
git clone https://github.com/your-org/docgen.git
cd docgen
make setup

# Or manually with uv
uv pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests with coverage
make test

# Or manually
pytest tests/ -v --cov=backend/doc_generator --cov-report=term-missing
```

### Linting & Type Checking

```bash
# Lint and type check
make lint

# Or manually
ruff check backend/doc_generator
mypy backend/doc_generator
```

### Project Commands

```bash
make setup       # Install dependencies
make run         # Run sample generation
make test        # Run test suite
make lint        # Lint and type check
make clean       # Clean output/cache files
make help        # Show all commands
```

### Project Structure

```
docgen/
├── backend/
│   ├── Dockerfile                    # FastAPI backend container
│   ├── config/settings.yaml          # Configuration
│   ├── doc_generator/                # Core package
│   │   ├── domain/                   # Business logic
│   │   ├── application/              # Use cases
│   │   └── infrastructure/           # External integrations
│   └── requirements-docker.txt
│
├── frontend/
│   ├── Dockerfile                    # Next.js frontend container
│   ├── src/app/                      # App router pages
│   └── package.json
│
├── scripts/                          # CLI utilities
├── tests/                            # Test suite
├── docs/                             # Documentation
├── docker-compose.yml                # Multi-container setup
└── Makefile                          # Automation tasks
```

### Contributing

We welcome contributions! Please follow these guidelines:

1. **Architecture:** Follow clean architecture patterns (domain/application/infrastructure)
2. **Type Safety:** Add type hints to all functions
3. **Documentation:** Write comprehensive docstrings
4. **Testing:** Add unit tests for new features (aim for >80% coverage)
5. **Linting:** Run `make lint` before committing
6. **Commits:** Use conventional commits (feat, fix, docs, refactor, test)

**Before submitting a PR:**
```bash
make lint        # Ensure code passes linting
make test        # Ensure tests pass
```

---

## 🐛 Troubleshooting

<details>
<summary><b>Port already in use (Docker)</b></summary>

```bash
# Stop existing containers
docker-compose down

# Or change port in docker-compose.yml
```
</details>

<details>
<summary><b>Module not found errors</b></summary>

```bash
# Reinstall dependencies
make setup

# Or manually
uv pip install -e ".[dev]"
```
</details>

<details>
<summary><b>Docker build fails</b></summary>

```bash
# Rebuild without cache
docker-compose build --no-cache
```
</details>

<details>
<summary><b>LLM API errors</b></summary>

```bash
# Verify API key in .env
cat .env | grep API_KEY

# Check API key validity
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01"
```
</details>

<details>
<summary><b>Permission denied on output directory</b></summary>

```bash
chmod 755 backend/data/output
```
</details>

### Getting Help

- **Issues:** [GitHub Issues](https://github.com/your-org/docgen/issues)
- **Discussions:** [GitHub Discussions](https://github.com/your-org/docgen/discussions)
- **Documentation:** See `docs/` for architecture and guides

---

## 🙏 Acknowledgments

DocGen is built on the shoulders of giants:

- **[Docling](https://github.com/DS4SD/docling)** by IBM Research - Advanced document parsing with OCR and layout analysis
- **[MarkItDown](https://github.com/microsoft/markitdown)** by Microsoft - Document-to-markdown conversion
- **[LangGraph](https://github.com/langchain-ai/langgraph)** by LangChain - Workflow orchestration and state machines
- **[ReportLab](https://www.reportlab.com/)** - Professional PDF generation
- **[python-pptx](https://github.com/scanny/python-pptx)** - PowerPoint presentation generation
- **[Loguru](https://github.com/Delgan/loguru)** - Beautiful and powerful logging

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with ❤️ for developers who value clean architecture, type safety, and extensibility.**

⭐ **Star this repo if you find it useful!**

[![GitHub stars](https://img.shields.io/github/stars/your-org/docgen?style=social)](https://github.com/your-org/docgen/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/your-org/docgen?style=social)](https://github.com/your-org/docgen/network/members)
[![GitHub watchers](https://img.shields.io/github/watchers/your-org/docgen?style=social)](https://github.com/your-org/docgen/watchers)

</div>
