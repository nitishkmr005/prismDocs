# Claude Code Instructions

## Commands
```bash
make setup      # First-time setup (creates venv, installs deps)
make run        # Run the application
make test       # Run tests
make lint       # Format + lint check
make all        # lint + test + build
```

## Architecture
Three-layer clean architecture: `Domain → Application → Infrastructure`
- Domain: Zero external dependencies (pure business logic)
- Application: Orchestrates domain (use cases)
- Infrastructure: External connections (API, DB, LLM)

## Project Layout
```
src/{project}/domain|application|infrastructure/
tests/           # All tests (mirrors src/ structure)
docs/            # Extended docs (see docs/README.md for index)
```

## Key Files
- `pyproject.toml`: All dependencies (use `uv`, pin versions)
- `Makefile`: Single entry point for all commands
- `.env`: Secrets (never commit, use `.env.example`)
- `tests/conftest.py`: Shared fixtures

## Code Conventions
- Linting handled by pre-commit hooks (ruff/biome) - no manual style enforcement
- Use `loguru` for logging, never `print()`
- One responsibility per module
- Reference patterns: see `src/{project}/domain/` for examples

## Documentation
- Root: `README.md` only (objective, setup, run, structure)
- Extended docs: `docs/` with index
- Docstrings: Google style, required for public APIs

## Workflow
1. Read relevant files before changes (use `file:line` references)
2. Simplest working version first
3. Run `make lint` after code changes
4. Run `make test` before committing
5. One end-to-end test minimum

## Principles
- Simplicity over complexity
- No premature abstraction
- Delete unused code (no backwards-compat hacks)
- Evidence before assertions (run tests, don't assume)