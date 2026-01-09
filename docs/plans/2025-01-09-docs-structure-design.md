# Documentation Structure Design

## Overview

A comprehensive documentation structure for MVP projects using Claude Code, designed to be portable across projects while supporting the document-generator project specifically.

## Goals

1. Track MVP progress (specs, milestones, status)
2. Document Claude Code configurations (MCP, hooks, subagents, skills)
3. Capture workflows (issue-based, multi-agent, model selection)
4. Preserve learnings for future MVP iterations
5. Automate common tasks via skills

---

## Folder Structure

```
docs/
├── README.md                    # Index of all documentation
├── project/                     # Project-specific docs
│   ├── SPEC.md                  # Project specification
│   ├── MILESTONES.md            # Phases with deliverables
│   ├── STATUS.md                # Current status (updated frequently)
│   └── DECISIONS.md             # Decision log
├── architecture/                # System design
│   ├── README.md                # Architecture overview
│   ├── decisions/               # ADRs if needed
│   └── diagrams/                # Mermaid/visual diagrams
├── workflows/                   # How to work with this project
│   ├── README.md                # Workflow overview
│   ├── issue-based.md           # Issue-driven development
│   ├── multi-agent.md           # Parallel agent workflow
│   ├── model-selection.md       # Opus vs Sonnet guidance
│   └── session-checklist.md     # Start/end session rituals
├── claude-code/                 # Claude Code configuration
│   ├── README.md                # Setup overview
│   ├── mcp-servers.md           # MCP server configs
│   ├── hooks.md                 # Hook configurations
│   ├── subagents.md             # Custom subagent definitions
│   ├── skills.md                # Project skills reference
│   └── permissions.md           # Permission settings
├── plans/                       # Implementation plans
│   └── YYYY-MM-DD-<topic>-plan.md
├── learnings/                   # Retros and lessons
│   ├── README.md                # Index of learnings
│   ├── YYYY-MM-DD-retro.md      # Retrospectives
│   └── patterns.md              # Recurring patterns
└── guides/                      # How-to guides
    ├── README.md                # Guide index
    ├── git-worktree.md          # Git worktree setup
    ├── setup.md                 # Project setup
    └── troubleshooting.md       # Common issues
```

---

## File Purposes

### project/

| File | Purpose | Update Frequency |
|------|---------|------------------|
| SPEC.md | Features, constraints, success criteria, tech stack | Rarely (scope changes) |
| MILESTONES.md | MVP phases, deliverables, acceptance criteria | When phases complete |
| STATUS.md | Done, in-progress, blocked, next up | End of each session |
| DECISIONS.md | "We chose X over Y because Z" | When decisions made |

### claude-code/

| File | Purpose |
|------|---------|
| mcp-servers.md | MCP server configs, what they do, how to add |
| hooks.md | Hook scripts, what they enforce |
| subagents.md | Custom agents, their tools, when to use |
| skills.md | Available /commands, usage examples |
| permissions.md | What's allowed/denied, security rationale |

### workflows/

| File | Purpose |
|------|---------|
| issue-based.md | Specs/milestones → GitHub issues via `gh` CLI |
| multi-agent.md | Git worktree for parallel agents |
| model-selection.md | Opus 4.5 (planning) vs Sonnet 4.5 (implementation) |
| session-checklist.md | Start/end session rituals |

### learnings/

| File | Purpose |
|------|---------|
| YYYY-MM-DD-retro.md | What went well/poorly/learned per milestone |
| patterns.md | Recurring patterns to carry to next MVP |

---

## Skills to Create

Located in `.claude/skills/`:

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `/update-status` | End of session | Update STATUS.md with progress |
| `/retro` | End of milestone | Create retrospective |
| `/create-issues` | After milestones defined | MILESTONES.md → GitHub issues |
| `/new-milestone` | Planning new phase | Add milestone with template |
| `/session-start` | Beginning of session | Review STATUS.md, show next tasks |
| `/session-end` | End of session | Update status + optional retro |

### Skill Behaviors

**`/update-status`**
- Reads recent git commits
- Asks what was accomplished
- Updates STATUS.md with new entries

**`/retro`**
- Prompts: What went well? What went poorly? What did you learn?
- Writes to `learnings/YYYY-MM-DD-retro.md`
- Optionally updates `patterns.md` with recurring insights

**`/create-issues`**
- Parses MILESTONES.md for deliverables
- Creates GitHub issues via `gh issue create`
- Adds labels per milestone phase
- Links issues to milestone

**`/new-milestone`**
- Prompts for milestone name, deliverables, acceptance criteria
- Appends to MILESTONES.md with template

**`/session-start`**
- Reads STATUS.md
- Summarizes current state
- Suggests first task based on priorities

**`/session-end`**
- Runs `/update-status`
- Asks if retro is needed
- Optionally runs `/retro`

---

## Migration Plan

### Existing Files to Move

| Current Location | New Location |
|------------------|--------------|
| docs/learnings/git-worktree-guide.md | docs/guides/git-worktree.md |
| docs/WORKFLOW-VISUALIZATION.md | docs/architecture/diagrams/ |
| docs/langgraph-diagram.md | docs/architecture/diagrams/ |
| docs/langgraph-mermaid.txt | docs/architecture/diagrams/ |
| docs/setup-python-project.md | docs/guides/setup.md |
| docs/refactoring-report.md | docs/learnings/ (as a retro) |

### New Files to Create

1. `docs/README.md` - Index
2. `docs/project/SPEC.md` - Extract from README.md
3. `docs/project/MILESTONES.md` - Define phases
4. `docs/project/STATUS.md` - Current state
5. `docs/project/DECISIONS.md` - Decision log
6. All `claude-code/` files
7. All `workflows/` files
8. README.md files for each folder

---

## Portability

To use this structure in a new project:

1. Copy entire `docs/` folder structure
2. Copy `.claude/skills/` folder
3. Update `docs/project/SPEC.md` with new project details
4. Clear `docs/project/STATUS.md` and `docs/learnings/`
5. Keep `docs/workflows/` and `docs/claude-code/` as-is (universal)

---

## Implementation Order

1. Create folder structure
2. Create README.md index files
3. Create project/ files with templates
4. Move existing files to new locations
5. Create workflows/ documentation
6. Create claude-code/ documentation
7. Create skills
8. Test skills end-to-end
