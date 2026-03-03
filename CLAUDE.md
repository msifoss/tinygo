# TinyGo

CLI tool for deploying web pages to [tiiny.host](https://tiiny.host) from the terminal.

## What This Project Does

TinyGo wraps the tiiny.host external API, providing command-line deploy, update, delete, list, and profile operations for static HTML files and zip archives. It also supports bundling multi-file HTML projects into a single zip and maintains a local deployment log.

## Architecture

```
tinygo/
├── cli.py         # Click command group — tiiny.host commands and Rich output
├── api.py         # TiinyClient — HTTP wrapper around tiiny.host REST API
├── aws_cli.py     # Click command group — AWS (S3 + CloudFront + Cognito) commands
├── aws_client.py  # AWSClient — boto3 wrapper for S3 uploads, CloudFront invalidation
├── config.py      # Config I/O (~/.tinygo/.env + config.yaml), API key resolution, AWS config, legacy migration
├── bundle.py      # HTML scanning, file staging, path rewriting, zip creation
├── log.py         # Deployment event logging (~/.tinygo/deployments.log)
└── __init__.py    # Version string
```

**Data flow (tiiny.host):** CLI command -> resolve API key (flag > env var > .env file) -> TiinyClient -> tiiny.host API -> Rich output. Bundle and log modules are called from CLI when applicable.

**Data flow (AWS):** CLI command -> resolve AWS config (config.yaml) -> AWSClient -> S3/CloudFront via boto3 -> Rich output. Infrastructure provisioned via SAM (Cognito + Lambda@Edge for auth).

**External API (tiiny.host):** All requests go to `https://ext.tiiny.host` with `x-api-key` header auth. Four endpoints: POST/PUT `/v1/upload`, DELETE `/v1/delete`, GET `/v1/profile`.

**AWS services:** S3 (file hosting), CloudFront (CDN), Cognito (user auth with Hosted UI), Lambda@Edge (cookie-based auth enforcement).

## Project Structure

```
tinygo/                  # Repository root
├── tinygo/              # Python package (8 modules, ~1410 lines)
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
- **Dependencies:** click >= 8.0, python-dotenv >= 1.0, pyyaml >= 6.0, requests >= 2.28, rich >= 13.0; optional: boto3 >= 1.28 (for AWS features, `pip install tinygo[aws]`)

## Conventions

- **CLI framework:** Click with `@click.group()` pattern
- **Output:** Rich console for all user-facing output (tables, status spinners, colored text)
- **Error handling:** `TiinyError` exception with status_code and detail; caught in CLI, printed with `[red]`, exits with code 1
- **Config location:** `~/.tinygo/` directory (.env for secrets, config.yaml for settings, deployments.log)
- **Domain normalization:** `.tiiny.site` suffix auto-appended if missing
- **Imports:** stdlib only for bundle.py and log.py; third-party (click, requests, rich) in cli.py and api.py; (python-dotenv, pyyaml) in config.py

## Current Status

- **Version:** 0.5.0
- **Features:** deploy, update, delete, list, profile, config, bundle (default on), log, auto noindex + password protection; AWS backend (S3 + CloudFront + Cognito auth with Hosted UI login)
- **Tests:** 111 passing (pytest — test_api, test_aws_cli, test_aws_client, test_bundle, test_config, test_lambda_auth, test_log)
- **CI/CD:** None (manual install and deploy)
- **Deployments:** Manual via `tinygo deploy` (tiiny.host) or `tinygo aws deploy` (AWS)
