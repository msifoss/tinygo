# Solo+AI Workflow Guide

## Overview

TinyGo is developed by a solo developer working with AI assistance (Claude Code). This guide documents the workflow patterns used.

## Bolt-Driven Development

Work is organized into **bolts** — focused, time-boxed sprints with clear scope.

### Bolt structure
1. **Plan** — Define scope, identify files to create/modify
2. **Execute** — Implement changes, write tests
3. **Review** — Verify functionality, run tests
4. **Retro** — Log what worked, what didn't, update docs

### Sizing convention
| Size | Scope | Example |
|------|-------|---------|
| S | 1-2 files, < 1 hour | Add a CLI flag |
| M | 3-5 files, 1-3 hours | Add bundle feature |
| L | 5+ files, half day | Major refactor |
| XL | Avoid | Break into smaller bolts |

## Five Questions Pattern

Before starting work on a feature, surface assumptions by answering:
1. What exactly are we building?
2. What are the inputs and outputs?
3. What are the edge cases?
4. What could go wrong?
5. How will we verify it works?

## Context Hygiene

- Keep `CLAUDE.md` updated with current project state
- Captain's logs capture session-specific decisions and learnings
- Don't duplicate information between CLAUDE.md and README
- CLAUDE.md is for AI context; README is for human users

## Captain's Logs

After each significant work session, write a captain's log entry at `docs/captains_log/YYYY-MM-DD.md` covering:
- What was accomplished
- Decisions made and rationale
- Issues encountered
- What's next

## Session Lifecycle

1. **Orient** — Read CLAUDE.md, check recent captain's logs
2. **Plan** — Use `/dlc-audit` or review backlog
3. **Execute** — Work in bolts
4. **Close** — Update CLAUDE.md, write captain's log, commit
