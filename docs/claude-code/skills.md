# Skills

Reusable capabilities invoked via `/command` syntax.

## What are Skills?

Skills are:
- Invoked with `/skill-name`
- Loaded and executed inline
- Can have arguments
- Project-specific or global

## Current Skills

### Project Skills (`.claude/skills/`)

| Skill | Command | Purpose |
|-------|---------|---------|
| pdf | `/pdf` | PDF manipulation toolkit |
| pptx | `/pptx` | Presentation creation and editing |
| skill-creator | `/skill-creator` | Guide for creating skills |
| theme-factory | `/theme-factory` | Styling artifacts with themes |

### Project Commands (`.claude/commands/`)

| Command | Invoke | Purpose |
|---------|--------|---------|
| commit | `/commit` | Create git commit |
| five-whys | `/five-whys` | Root cause analysis |
| retro | `/retro` | Create retrospective |
| save-prompt | `/save-prompt` | Save prompt to file |

### Workflow Commands (`.claude/commands/`)

| Command | Invoke | Purpose |
|---------|--------|---------|
| session-start | `/session-start` | Review status, suggest tasks |
| session-end | `/session-end` | Update status, optional retro |
| update-status | `/update-status` | Update STATUS.md |
| retro | `/retro` | Create retrospective |
| new-milestone | `/new-milestone` | Add milestone template |

## Using Skills

### Basic Usage
```
/skill-name
```

### With Arguments
```
/skill-name arg1 arg2
```

### Examples
```
/commit              # Create a commit
/pdf                 # PDF manipulation
/retro               # Create retrospective
/create-issues       # Generate GitHub issues
```

## Creating Skills

### Location
- `.claude/skills/skill-name/` - Multi-file skill
- `.claude/commands/skill-name.md` - Single-file command

### Format

```markdown
---
name: skill-name
description: When to use this skill
---

# Skill Title

## Purpose
What this skill does.

## Process
1. Step one
2. Step two

## Output
What the skill produces.
```

### Skill vs Command

| Type | Location | Use Case |
|------|----------|----------|
| Skill | `.claude/skills/` | Complex, multi-file, reusable |
| Command | `.claude/commands/` | Simple, single-file, project-specific |

## Best Practices

1. **Clear descriptions** - Help Claude know when to use the skill
2. **Step-by-step process** - Explicit instructions
3. **Define outputs** - What should result from the skill
4. **Include examples** - Show expected usage

## Debugging Skills

If a skill isn't working:
1. Check file exists in correct location
2. Verify YAML frontmatter is valid
3. Check for syntax errors
4. Test with `/skill-name --debug`

## Skill Discovery

```bash
# List project skills
ls .claude/skills/

# List project commands
ls .claude/commands/

# Check global skills
ls ~/.claude/skills/
```
