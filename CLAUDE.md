# TinyGo

CLI tool for deploying web pages to [tiiny.host](https://tiiny.host) from the terminal.

## What This Project Does

TinyGo wraps the tiiny.host external API, providing command-line deploy, update, delete, list, and profile operations for static HTML files and zip archives. It also supports bundling multi-file HTML projects into a single zip and maintains a local deployment log.

## Architecture

```
tinygo/
├── cli.py       # Click command group — all user-facing commands and Rich output
├── api.py       # TiinyClient — HTTP wrapper around tiiny.host REST API
├── config.py    # Config file I/O (~/.tinygo/config.json), API key resolution
├── bundle.py    # HTML scanning, file staging, path rewriting, zip creation
├── log.py       # Deployment event logging (~/.tinygo/deployments.log)
└── __init__.py  # Version string
```

**Data flow:** CLI command -> resolve API key (flag > env > config file) -> TiinyClient -> tiiny.host API -> Rich output. Bundle and log modules are called from CLI when applicable.

**External API:** All requests go to `https://ext.tiiny.host` with `x-api-key` header auth. Four endpoints: POST/PUT `/v1/upload`, DELETE `/v1/delete`, GET `/v1/profile`.

## Project Structure

```
tinygo/                  # Repository root
├── tinygo/              # Python package (6 modules, ~695 lines)
├── tests/               # Pytest test suite
├── docs/                # Documentation (requirements, standards, PM)
├── pyproject.toml       # Package metadata, deps, entry point
├── README.md            # User-facing documentation
├── SECURITY.md          # Security model and vulnerability reporting
├── CLAUDE.md            # This file — AI context
└── .gitignore
```

## Dev Environment

- **Python:** 3.9+
- **Virtual env:** `.venv/` (activate with `source .venv/bin/activate`)
- **Install:** `pip install -e .` (editable mode)
- **Run:** `tinygo <command>` after install
- **Test:** `pytest tests/` from repo root
- **Dependencies:** click >= 8.0, requests >= 2.28, rich >= 13.0 (no dev deps yet)

## Conventions

- **CLI framework:** Click with `@click.group()` pattern
- **Output:** Rich console for all user-facing output (tables, status spinners, colored text)
- **Error handling:** `TiinyError` exception with status_code and detail; caught in CLI, printed with `[red]`, exits with code 1
- **Config location:** `~/.tinygo/` directory (config.json, deployments.log)
- **Domain normalization:** `.tiiny.site` suffix auto-appended if missing
- **Imports:** stdlib only for bundle.py and log.py; third-party (click, requests, rich) only in cli.py and api.py

## Current Status

- **Version:** 0.1.0
- **Features:** deploy, update, delete, list, profile, config, bundle (--bundle flag), log
- **Tests:** 39 passing (pytest — test_api, test_bundle, test_config, test_log)
- **CI/CD:** None (manual install and deploy)
- **Deployments:** Manual via `tinygo deploy`
