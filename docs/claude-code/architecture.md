# Architecture Guidelines

## Clean Architecture Layers

```
src/{project}/
├── domain/          # Pure business logic, entities (NO external dependencies)
├── application/     # Use cases, orchestration services
├── infrastructure/  # External integrations (APIs, DB, file I/O)
├── config/          # Configuration re-exports
└── utils/           # Shared utilities
```

## Dependency Rules

> [!IMPORTANT]
> Dependencies flow INWARD only: infrastructure → application → domain

- `domain/` imports: **nothing** (pure Python only)
- `application/` imports: `domain/` only
- `infrastructure/` imports: `application/`, `domain/`, external packages

## File Naming Conventions

| Type       | Pattern                | Example                  |
| ---------- | ---------------------- | ------------------------ |
| Entity     | `{name}.py`            | `document.py`            |
| Service    | `{name}_service.py`    | `content_service.py`     |
| Repository | `{name}_repository.py` | `document_repository.py` |
| Use Case   | `{action}_{entity}.py` | `generate_pdf.py`        |

## New Project Structure

For any new Python project, start with:

```
project-name/
├── .claude/
│   └── CLAUDE.md
├── config/
│   └── settings.yaml
├── src/
│   ├── {project_name}/
│   │   ├── __init__.py
│   │   ├── domain/
│   │   │   └── __init__.py
│   │   ├── application/
│   │   │   └── __init__.py
│   │   └── infrastructure/
│   │       └── __init__.py
│   └── data/
│       ├── input/           # Input files to process
│       ├── logging/         # LLM logs, JSON logs (timestamped)
│       └── output/          # Generated outputs
│       └── cache/           # Cached outputs
├── tests/
│   └── __init__.py
├── docs/
│   ├── project/
│   │   ├── SPEC.md
│   │   └── STATUS.md
│   ├── claude-code/
│   ├── blog/                # Technical blog posts
│   ├── plans/               # Design plans (YYYY-MM-DD-topic.md)
│   └── learnings/           # Session retrospectives
├── .env
├── .gitignore
├── Dockerfile
├── pyproject.toml
├── Makefile
├── README.md
└── Quickstart.md
```

## Principles

1. **Domain purity**: Domain layer has zero external dependencies
2. **Interface segregation**: Define interfaces in application, implement in infrastructure
3. **Dependency injection**: Pass dependencies via constructors, not global imports
4. **Single responsibility**: One class/module = one reason to change
