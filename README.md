<div align="center">

# DocGen

### Transform any content into professional documents with AI

**AI-Powered Document Generation | Multi-Format | Production-Ready**

From Research Papers to Pitch Decks • From Web Articles to Study Guides  
Built on LangGraph, Docling, and modern LLMs • Clean Architecture • Type-Safe • Extensible

</div>

<p align="center">
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-use-cases-by-role">Use Cases</a> •
  <a href="#-api-usage">API</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-roadmap">Roadmap</a>
</p>

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

<div align="center">

### System Overview

<svg width="900" height="500" xmlns="http://www.w3.org/2000/svg">
  <!-- Background -->
  <rect width="900" height="500" fill="#f8f9fa" rx="10"/>

  <!-- Input Layer -->
  <rect x="50" y="100" width="150" height="300" fill="#dbeafe" stroke="#3b82f6" stroke-width="2" rx="5"/>
  <text x="125" y="130" font-family="Arial" font-size="16" font-weight="bold" fill="#1e40af" text-anchor="middle">Input Sources</text>

  <text x="125" y="165" font-family="Arial" font-size="13" fill="#374151" text-anchor="middle">📄 PDF</text>
  <text x="125" y="195" font-family="Arial" font-size="13" fill="#374151" text-anchor="middle">📝 Markdown</text>
  <text x="125" y="225" font-family="Arial" font-size="13" fill="#374151" text-anchor="middle">🌐 Web URLs</text>
  <text x="125" y="255" font-family="Arial" font-size="13" fill="#374151" text-anchor="middle">📊 DOCX/XLSX</text>
  <text x="125" y="285" font-family="Arial" font-size="13" fill="#374151" text-anchor="middle">🖼️ Images</text>
  <text x="125" y="315" font-family="Arial" font-size="13" fill="#374151" text-anchor="middle">📋 Plain Text</text>

  <!-- Processing Layer -->
  <rect x="275" y="50" width="350" height="400" fill="#fef3c7" stroke="#f59e0b" stroke-width="2" rx="5"/>
  <text x="450" y="80" font-family="Arial" font-size="16" font-weight="bold" fill="#92400e" text-anchor="middle">LangGraph Workflow</text>

  <!-- Workflow Steps -->
  <rect x="320" y="110" width="260" height="50" fill="#fbbf24" stroke="#d97706" stroke-width="2" rx="5"/>
  <text x="450" y="140" font-family="Arial" font-size="14" font-weight="bold" fill="#000" text-anchor="middle">1. Detect Format</text>

  <rect x="320" y="180" width="260" height="50" fill="#fbbf24" stroke="#d97706" stroke-width="2" rx="5"/>
  <text x="450" y="210" font-family="Arial" font-size="14" font-weight="bold" fill="#000" text-anchor="middle">2. Parse Content (Docling)</text>

  <rect x="320" y="250" width="260" height="50" fill="#fbbf24" stroke="#d97706" stroke-width="2" rx="5"/>
  <text x="450" y="280" font-family="Arial" font-size="14" font-weight="bold" fill="#000" text-anchor="middle">3. Transform (LLM + Images)</text>

  <rect x="320" y="320" width="260" height="50" fill="#fbbf24" stroke="#d97706" stroke-width="2" rx="5"/>
  <text x="450" y="350" font-family="Arial" font-size="14" font-weight="bold" fill="#000" text-anchor="middle">4. Generate Output</text>

  <rect x="320" y="390" width="260" height="40" fill="#fbbf24" stroke="#d97706" stroke-width="2" rx="5"/>
  <text x="450" y="415" font-family="Arial" font-size="14" font-weight="bold" fill="#000" text-anchor="middle">5. Validate</text>

  <!-- Output Layer -->
  <rect x="700" y="100" width="150" height="300" fill="#dcfce7" stroke="#22c55e" stroke-width="2" rx="5"/>
  <text x="775" y="130" font-family="Arial" font-size="16" font-weight="bold" fill="#166534" text-anchor="middle">Outputs</text>

  <text x="775" y="175" font-family="Arial" font-size="13" fill="#374151" text-anchor="middle">📕 PDF</text>
  <text x="775" y="215" font-family="Arial" font-size="13" fill="#374151" text-anchor="middle">📊 PPTX</text>
  <text x="775" y="255" font-family="Arial" font-size="13" fill="#374151" text-anchor="middle">📝 Markdown</text>
  <text x="775" y="295" font-family="Arial" font-size="13" fill="#374151" text-anchor="middle">❓ FAQ Docs</text>
  <text x="775" y="335" font-family="Arial" font-size="13" fill="#374151" text-anchor="middle">🎙️ Podcasts*</text>

  <!-- Arrows -->
  <defs>
    <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
      <polygon points="0 0, 10 3, 0 6" fill="#6b7280" />
    </marker>
  </defs>

  <line x1="200" y1="250" x2="275" y2="250" stroke="#6b7280" stroke-width="3" marker-end="url(#arrowhead)"/>
  <line x1="625" y1="250" x2="700" y2="250" stroke="#6b7280" stroke-width="3" marker-end="url(#arrowhead)"/>

  <!-- Retry Loop -->
  <path d="M 580 320 Q 650 290 580 260" stroke="#ef4444" stroke-width="2" fill="none" marker-end="url(#arrowhead)"/>
  <text x="620" y="280" font-family="Arial" font-size="11" fill="#ef4444">Retry (max 3x)</text>

  <!-- Tech Stack Labels -->
  <text x="450" y="30" font-family="Arial" font-size="12" fill="#6b7280" text-anchor="middle" font-style="italic">Claude • Gemini • OpenAI • Docling • ReportLab</text>
</svg>

</div>

**Core Stack:**
- **Workflow:** LangGraph 0.2.55 - State machine orchestration with retry logic
- **Parsing:** Docling 2.66.0 (IBM Research) - Advanced OCR, table extraction, layout analysis
- **LLM Synthesis:** Claude/Gemini/OpenAI - Content transformation and intelligent summarization
- **Image Generation:** Gemini/DALL-E - AI-generated visuals and diagrams
- **Generation:** ReportLab 4.2.5 + python-pptx 1.0.2 - Professional PDF/PPTX rendering
- **Architecture:** Clean Architecture - Domain/Application/Infrastructure layers with zero circular dependencies

**Two Ways to Use DocGen:**

1. **Python Package** (Coming Soon) - `pip install docgen` for programmatic access
2. **Web UI + API** - FastAPI backend + Next.js frontend for UI-driven generation

### Multi-Format Input Parsing

Ingest and normalize content from diverse sources with intelligent extraction:

| Format | Parser | Capabilities |
|--------|--------|--------------|
| **PDF** | Docling | OCR, table extraction, layout analysis, image extraction |
| **Markdown** | Native | Frontmatter support, code blocks, nested structures |
| **Web URLs** | MarkItDown | Article extraction, metadata parsing, link resolution |
| **Office Docs** | Docling | DOCX, PPTX, XLSX with formatting preservation |
| **Images** | Docling | PNG, JPG, TIFF with OCR and layout detection |
| **Plain Text** | Native | TXT files with encoding detection |

### AI-Powered Synthesis
- **Content Transformation:** LLM-driven summarization, restructuring, and style adaptation
- **Visual Generation:** Context-aware diagrams, charts, and illustrations via Gemini/DALL-E
- **Intelligent Merging:** Multi-source synthesis with conflict resolution and deduplication
- **Slide Generation:** Automatic PPTX layouts with bullet points, titles, and visuals

### Professional Output Formats
- **PDF:** ReportLab-based generation with custom styling, headers, footers, and TOC
- **PPTX:** python-pptx presentations with 16:9 layouts and embedded images
- **Markdown:** Structured docs with frontmatter and proper heading hierarchy
- **FAQ Docs:** Q&A format generation from input content
- **Podcasts:** MP3 audio generation (coming soon)

### Production-Ready Features
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
├── domain/              # 🎯 Pure business logic (zero dependencies)
│   ├── models.py        # Core entities: Document, Content, Output
│   ├── enums.py         # InputFormat, OutputFormat, ProcessingStatus
│   ├── exceptions.py    # Custom exceptions with error codes
│   └── interfaces.py    # Abstract interfaces for parsers/generators
│
├── application/         # 🔄 Use case orchestration
│   ├── parsers/         # Format-specific parsing implementations
│   ├── generators/      # Output format generators
│   ├── graph_workflow.py # LangGraph state machine
│   └── nodes/           # Workflow nodes (parse, transform, generate)
│
└── infrastructure/      # 🔌 External integrations
    ├── docling/         # Docling integration for parsing
    ├── markitdown/      # MarkItDown for web content
    ├── llm/             # LLM providers (Claude, Gemini, OpenAI)
    ├── image/           # Image generation services
    ├── api/             # FastAPI endpoints and routes
    └── settings.py      # Config management (YAML + env)
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
- **YAML Config:** `backend/config/settings.yaml` for defaults (page layouts, colors, LLM params)
- **Environment Variables:** `.env` for secrets (API keys, database URLs)
- **Pydantic Settings:** Type-safe config with validation and auto-reload

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker (for containerized deployment)
- LLM API key (Claude, Gemini, or OpenAI)

### Option 1: Web UI (Fastest)

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

### Option 2: Python Package (Coming Soon)

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

### Option 3: Local Development

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

### Upload Files

**Endpoint:** `POST /api/upload`

```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@paper.pdf"

# Response:
{
  "file_id": "f_abc123",
  "filename": "paper.pdf",
  "size": 245810,
  "mime_type": "application/pdf",
  "expires_in": 3600
}
```

### Download Generated Files

**Endpoint:** `GET /api/download/{file_id}/{format}/{filename}`

```bash
curl -L -o output.pdf \
  "http://localhost:8000/api/download/f_abc123/pdf/report.pdf"
```

### Health Check

**Endpoint:** `GET /api/health`

```bash
curl http://localhost:8000/api/health

# Response:
{"status": "healthy", "version": "0.1.0"}
```

---

## 🗺️ Roadmap

DocGen is under active development with ambitious plans for new capabilities. Our vision is to become the **go-to toolkit for AI-powered document generation** across all industries and use cases.

<div align="center">

### Development Timeline

<svg width="900" height="700" xmlns="http://www.w3.org/2000/svg">
  <!-- Background -->
  <rect width="900" height="700" fill="#ffffff" rx="10"/>

  <!-- Timeline vertical line -->
  <line x1="100" y1="50" x2="100" y2="650" stroke="#94a3b8" stroke-width="3"/>

  <!-- Phase 1: Enhanced Generation -->
  <circle cx="100" cy="100" r="15" fill="#3b82f6"/>
  <rect x="150" y="60" width="700" height="140" fill="#dbeafe" stroke="#3b82f6" stroke-width="2" rx="5"/>
  <text x="170" y="85" font-family="Arial" font-size="18" font-weight="bold" fill="#1e40af">Phase 1: Enhanced Generation 🎨</text>
  <text x="170" y="110" font-family="Arial" font-size="13" fill="#374151">Priority: High | Timeline: Q1 2026</text>

  <text x="170" y="135" font-family="Arial" font-size="12" fill="#1e293b">✅ Podcast MP3 generation with multi-voice support</text>
  <text x="170" y="155" font-family="Arial" font-size="12" fill="#1e293b">⏳ Mind maps with visual hierarchy and relationships</text>
  <text x="170" y="175" font-family="Arial" font-size="12" fill="#1e293b">⏳ Advanced code blocks with syntax highlighting + Mermaid</text>

  <!-- Phase 2: UI/UX Improvements -->
  <circle cx="100" cy="280" r="15" fill="#8b5cf6"/>
  <rect x="150" y="240" width="700" height="140" fill="#f3e8ff" stroke="#8b5cf6" stroke-width="2" rx="5"/>
  <text x="170" y="265" font-family="Arial" font-size="18" font-weight="bold" fill="#6b21a8">Phase 2: UI/UX Excellence 🔧</text>
  <text x="170" y="290" font-family="Arial" font-size="13" fill="#374151">Priority: High | Timeline: Q1-Q2 2026</text>

  <text x="170" y="315" font-family="Arial" font-size="12" fill="#1e293b">⏳ API key management in UI (secure vault)</text>
  <text x="170" y="335" font-family="Arial" font-size="12" fill="#1e293b">⏳ Real-time generation preview panel</text>
  <text x="170" y="355" font-family="Arial" font-size="12" fill="#1e293b">📋 Template marketplace with pre-built document types</text>

  <!-- Phase 3: Document Templates -->
  <circle cx="100" cy="460" r="15" fill="#ec4899"/>
  <rect x="150" y="420" width="700" height="140" fill="#fce7f3" stroke="#ec4899" stroke-width="2" rx="5"/>
  <text x="170" y="445" font-family="Arial" font-size="18" font-weight="bold" fill="#9f1239">Phase 3: Template Library 📄</text>
  <text x="170" y="470" font-family="Arial" font-size="13" fill="#374151">Priority: Medium | Timeline: Q2 2026</text>

  <text x="170" y="495" font-family="Arial" font-size="12" fill="#1e293b">📋 Professional resumes with 5+ industry-specific styles</text>
  <text x="170" y="515" font-family="Arial" font-size="12" fill="#1e293b">📋 arXiv-style research paper formatting</text>
  <text x="170" y="535" font-family="Arial" font-size="12" fill="#1e293b">📋 Wedding cards, YouTube thumbnails, interview prep docs</text>

  <!-- Phase 4: Platform & Scale -->
  <circle cx="100" cy="640" r="15" fill="#22c55e"/>
  <rect x="150" y="600" width="700" height="80" fill="#dcfce7" stroke="#22c55e" stroke-width="2" rx="5"/>
  <text x="170" y="625" font-family="Arial" font-size="18" font-weight="bold" fill="#166534">Phase 4: Enterprise Ready 🚀</text>
  <text x="170" y="650" font-family="Arial" font-size="13" fill="#374151">Priority: High | Timeline: Q3 2026</text>

  <text x="170" y="675" font-family="Arial" font-size="12" fill="#1e293b">📦 Python package on PyPI • 🔐 Auth & user management • ☁️ Cloud optimization</text>

  <!-- Legend -->
  <text x="50" y="30" font-family="Arial" font-size="14" font-weight="bold" fill="#475569">Status:</text>
  <text x="120" y="30" font-family="Arial" font-size="13" fill="#22c55e">✅ Complete</text>
  <text x="220" y="30" font-family="Arial" font-size="13" fill="#f59e0b">⏳ In Progress</text>
  <text x="340" y="30" font-family="Arial" font-size="13" fill="#64748b">📋 Planned</text>
</svg>

</div>

---

### 🎯 Feature Categories

<table>
<tr>
<td width="50%" valign="top">

### 🎨 **Enhanced Generation**

<details open>
<summary><b>Content & Media</b></summary>

- ⏳ **Podcast MP3 generation** - Multi-voice support with ElevenLabs/Azure TTS
- 📋 **Mind maps** - Visual hierarchy with D3.js/Mermaid
- 📋 **FAQ cards** - Structured Q&A with auto-formatting
- 📋 **SVG diagram generation** - Technical diagrams from text
- ✅ **Image generation toggle** - Per-request control

</details>

<details open>
<summary><b>Developer Tools</b></summary>

- ⏳ **Advanced code blocks** - Syntax highlighting + line numbers
- ⏳ **Mermaid diagrams** - Flowcharts, sequence diagrams, ER diagrams
- 📋 **API documentation** - OpenAPI/Swagger to markdown
- 📋 **Architecture diagrams** - Auto-generate from code

</details>

</td>
<td width="50%" valign="top">

### 🔧 **UI/UX Improvements**

<details open>
<summary><b>User Experience</b></summary>

- ⏳ **API key vault** - Secure multi-provider key management
- ⏳ **Real-time preview** - See documents as they generate
- 📋 **Batch processing** - Process multiple files at once
- 📋 **Cache management** - One-click cleanup utilities
- 📋 **Generation history** - Track past generations

</details>

<details open>
<summary><b>Marketplace</b></summary>

- 📋 **Template library** - 50+ pre-built templates
- 📋 **Community templates** - Share and discover
- 📋 **Style customization** - Brand colors, fonts, layouts
- 📋 **Template versioning** - Track changes, rollback

</details>

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 📄 **Document Templates**

<details open>
<summary><b>Professional</b></summary>

- 📋 **Resumes** - Tech, Marketing, Finance, Academic, Creative
- 📋 **Research papers** - arXiv, IEEE, ACM, Nature formats
- 📋 **Pitch decks** - Startup, Sales, Investor presentations
- 📋 **Reports** - Annual, Quarterly, Project status

</details>

<details open>
<summary><b>Creative & Personal</b></summary>

- 📋 **Wedding cards** - Invitations, save-the-dates, programs
- 📋 **YouTube thumbnails** - 10+ design styles
- 📋 **Social media** - Instagram posts, Twitter threads
- 📋 **Study materials** - Flashcards, summaries, notes

</details>

</td>
<td width="50%" valign="top">

### 🚀 **Platform & Scale**

<details open>
<summary><b>Distribution</b></summary>

- 📋 **PyPI package** - `pip install docgen` with CLI
- 📋 **Docker Hub** - Pre-built images for all platforms
- 📋 **npm package** - JavaScript/TypeScript SDK
- 📋 **GitHub Action** - CI/CD integration

</details>

<details open>
<summary><b>Enterprise Features</b></summary>

- 📋 **Authentication** - OAuth2, SSO, API keys
- 📋 **User management** - Teams, roles, permissions
- 📋 **Rate limiting** - Per-user, per-tier quotas
- 📋 **Usage analytics** - Cost tracking, insights
- 📋 **White-labeling** - Custom branding, domains

</details>

</td>
</tr>
</table>

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

## Troubleshooting

### Common Issues

**Port already in use (Docker)**
```bash
# Stop existing containers
docker-compose down

# Or change port in docker-compose.yml
```

**Module not found errors**
```bash
# Reinstall dependencies
make setup

# Or manually
uv pip install -e ".[dev]"
```

**Docker build fails**
```bash
# Rebuild without cache
docker-compose build --no-cache
```

**LLM API errors**
```bash
# Verify API key in .env
cat .env | grep API_KEY

# Check API key validity
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01"
```

**Permission denied on output directory**
```bash
chmod 755 backend/data/output
```

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

## License

MIT License - See [LICENSE](LICENSE) file for details.

---

**Built with ❤️ for developers who value clean architecture, type safety, and extensibility.**

⭐ Star this repo if you find it useful!
