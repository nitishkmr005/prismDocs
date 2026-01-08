# Git Worktree Guide

## Table of Contents
- [Overview](#overview)
- [Creating a Worktree](#creating-a-worktree)
- [Working with Worktrees](#working-with-worktrees)
- [Merging Worktree Branch to Main](#merging-worktree-branch-to-main)
- [Cleaning Up](#cleaning-up)
- [Complete Example Workflow](#complete-example-workflow)
- [Tips](#tips)

## Overview

Git worktrees allow you to check out multiple branches simultaneously in separate directories. This enables parallel development without switching branches in your main working directory.

**Use cases:**
- Work on a feature while keeping main branch accessible
- Review or test another branch without stashing current work
- Run long processes on one branch while developing on another

## Creating a Worktree

```bash
# Create worktree with a new branch
git worktree add <path> -b <new-branch>

# Create worktree from an existing branch
git worktree add <path> <existing-branch>

# Create worktree in a hidden directory (recommended)
git worktree add .trees/<feature-name> -b <feature-branch>
```

## Working with Worktrees

```bash
# List all worktrees
git worktree list

# Run git commands in a worktree without changing directory
git -C <worktree-path> status
git -C <worktree-path> diff
git -C <worktree-path> log --oneline -5

# Stage and commit in worktree
git -C <worktree-path> add <files>
git -C <worktree-path> commit -m "commit message"

# Push worktree branch to remote
git -C <worktree-path> push -u origin <branch-name>
```

## Merging Worktree Branch to Main

### Step 1: Commit and Push Feature Branch

```bash
git -C <worktree-path> add <files>
git -C <worktree-path> commit -m "commit message"
git -C <worktree-path> push -u origin <feature-branch>
```

### Step 2: Merge to Main

```bash
# From main repository directory
git checkout main
git fetch origin
git merge origin/<feature-branch> -m "Merge <feature-branch>: description"
```

### Step 3: Resolve Conflicts (if any)

```bash
# Keep main branch version
git checkout --ours <file>

# Keep feature branch version
git checkout --theirs <file>

# After resolving
git add <resolved-files>
git commit -m "Merge <feature-branch>: description"
```

### Step 4: Push to Remote

```bash
git push origin main
```

## Cleaning Up

```bash
# Remove worktree
git worktree remove <worktree-path>

# Force remove (if untracked/modified files exist)
git worktree remove --force <worktree-path>

# Delete local branch
git branch -d <feature-branch>

# Delete remote branch
git push origin --delete <feature-branch>

# Prune stale worktree references
git worktree prune
```

## Complete Example Workflow

```bash
# 1. Create worktree
git worktree add .trees/feature-x -b feature-x

# 2. Make changes and commit
git -C .trees/feature-x add .
git -C .trees/feature-x commit -m "Add feature X"

# 3. Push feature branch
git -C .trees/feature-x push -u origin feature-x

# 4. Merge to main
git fetch origin
git merge origin/feature-x -m "Merge feature-x"

# 5. Push main
git push origin main

# 6. Clean up
git worktree remove --force .trees/feature-x
git branch -d feature-x
git push origin --delete feature-x
```

## Tips

- Add worktree directory (e.g., `.trees/`) to `.gitignore`
- Use consistent naming between worktree folder and branch
- Fetch before merging to get latest remote changes
- Remove worktree before deleting its associated branch
