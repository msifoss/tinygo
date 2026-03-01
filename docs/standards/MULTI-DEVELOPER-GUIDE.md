# Multi-Developer Guide

## Current State

TinyGo is currently a solo+AI project. This guide prepares for future contributors.

## Branch Strategy

- `main` — stable, releasable code
- Feature branches — `feature/<name>` for new work
- Bug fix branches — `fix/<name>` for patches

## Code Review Process

1. Open a PR against `main`
2. CI must pass (lint + tests)
3. At least one review required
4. Squash merge preferred

## Shared Context Management

- `CLAUDE.md` is the source of truth for project context
- Update CLAUDE.md when making architectural changes
- Captain's logs document session-specific decisions

## Onboarding Checklist

- [ ] Clone the repo
- [ ] Create virtualenv: `python3 -m venv .venv && source .venv/bin/activate`
- [ ] Install in editable mode: `pip install -e .`
- [ ] Read CLAUDE.md and README.md
- [ ] Run tests: `pytest tests/`
- [ ] Get a tiiny.host API key for testing
- [ ] Run `tinygo config set-key` to configure
