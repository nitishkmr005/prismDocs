# Reused Commands and Workflows

## Index

| Category | Description |
| --- | --- |
| Python project setup | Common bootstrapping steps for new Python projects |
| Git workflow | Initial repo setup, worktrees, and daily commands |
| Claude Code planning and execution | Session start, planning, and wrap-up routines |

## Python project setup

| Step | Command | Notes |
| --- | --- | --- |
| 1 | `uv init` | Scaffold project metadata |
| 2 | `uv venv` | Create virtual environment |
| 3 | `source .venv/bin/activate` | Activate venv |
| 4 | `uv pip install -r requirements.txt` | Install dependencies from file |
| 5 | `uv pip install <package>` | Add a dependency |
| 6 | `uv pip freeze > requirements.txt` | Capture current dependencies |
| 7 | `python -m pip install -U pip` | Update pip when needed |
| 8 | System installs: `brew install <pkg>` or `apt-get install <pkg>` | OS-level deps |
| 9 | `.env` setup (example: `OPENAI_API_KEY=...`) | LLM API keys |
| 10 | `python -m pytest` or `pytest -q` | Quick test run |

## Git workflow

| Step | Command | Notes |
| --- | --- | --- |
| 1 | `git init` | Initialize repo |
| 2 | `git remote add origin <repo-url>` | Set remote |
| 3 | `git checkout -b <branch>` | Create working branch |
| 4 | `git status` | Check working tree |
| 5 | `git add -p` | Stage interactively |
| 6 | `git commit -m "..."` | Commit changes |
| 7 | `git push -u origin <branch>` | First push |
| 8 | `git fetch --prune` | Sync remotes |
| 9 | `git rebase origin/<branch>` | Rebase on remote |
| 10 | `git log -n 10 --oneline` | Recent history |
| 11 | `git diff` or `git diff --staged` | Review changes |
| 12 | `git stash` / `git stash pop` | Park changes |
| 13 | `git worktree add ../<worktree-name> <branch>` | Parallel worktree |
| 14 | `git worktree list` | Show worktrees |
| 15 | `git branch -vv` | Track status |

## Claude Code planning and execution

| Step | Command | Notes |
| --- | --- | --- |
| 1 | `/session-start` | Use when resuming previous work |
| 2 | `/brainstorm` | Create initial `spec.md` |
| 3 | `/agent` or `/subagent` | Delegate if multi-agent work |
| 4 | Work phase | Implement changes, update docs, run tests |
| 5 | `/update-status` | Update `docs/project/STATUS.md` |
| 6 | `/retro` | Update `docs/learnings/YYYY-MM-DD-retro.md` |
| 7 | `/session-end` | Wrap up, optionally run updates |

## Recommendations

| Area | Recommendation | Benefit |
| --- | --- | --- |
| Scope | Keep tasks small and time-boxed | Faster feedback and cleaner status updates |
| Status | Update `docs/project/STATUS.md` every session | Avoids lost context |
| Branching | Use one branch per task | Easier review and rollback |
| Worktrees | Use worktrees for parallel work | Fewer context switches |
| Testing | Run quick tests before commits | Catch regressions early |
| Docs | Capture decisions in `docs/project/DECISIONS.md` | Maintains rationale |
| Retros | Add patterns to `docs/learnings/` | Compounds learnings |
| Remote | Push frequently | Backup and collaboration ready |
