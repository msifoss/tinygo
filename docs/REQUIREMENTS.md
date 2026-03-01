# Requirements

## Purpose

Formal requirements for the TinyGo CLI tool. Each requirement has a unique ID for traceability.

---

## Functional Requirements

### Core Deployment

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-001 | Users can deploy an HTML file or zip archive to a new tiiny.host site via `tinygo deploy <file>` | Must |
| FR-002 | Users can update an existing tiiny.host site with new content via `tinygo update <file>` | Must |
| FR-003 | Users can delete a tiiny.host site via `tinygo delete --domain <name>` with confirmation prompt | Must |
| FR-004 | Users can list all their tiiny.host sites with quota usage via `tinygo list` | Must |
| FR-005 | Users can view their account profile via `tinygo profile` | Should |

### Authentication & Configuration

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-006 | Users can save their API key interactively via `tinygo config set-key` | Must |
| FR-007 | Users can view current config (API key masked) via `tinygo config show` | Should |
| FR-008 | API key resolves with priority: `--api-key` flag > `TIINY_API_KEY` env var > config file | Must |

### Bundle Deploy

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-009 | `--bundle` flag on deploy/update scans HTML for local file references (href, src, CSS url()) | Must |
| FR-010 | Bundle mode recursively scans linked HTML files for their own dependencies | Must |
| FR-011 | Bundle mode rewrites absolute paths to relative paths in staged HTML | Must |
| FR-012 | Bundle mode creates a zip of all staged files and deploys it | Must |
| FR-013 | Bundle mode cleans up temp files after deploy (success or failure) | Must |
| FR-014 | Bundle mode silently skips missing files and remote URLs | Should |

### Deployment Logging

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-015 | Every deploy, update, and delete (success or failure) appends to a local log file | Must |
| FR-016 | `tinygo log` displays deployment history as a formatted table | Must |
| FR-017 | `tinygo log -n <N>` shows only the last N entries | Should |
| FR-018 | `tinygo log --clear` deletes the log file | Should |

### User Experience

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-019 | Domain names are auto-normalized with `.tiiny.site` suffix | Should |
| FR-020 | Deploy prompts for subdomain if `--domain` is omitted | Should |
| FR-021 | Delete requires confirmation unless `--yes` is passed | Must |
| FR-022 | Sites can be password-protected via `--password` flag | Should |

---

## Non-Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-001 | CLI responds within 1 second for local operations (config, log display) | Should |
| NFR-002 | All user-facing output uses Rich formatting (colors, tables, spinners) | Should |
| NFR-003 | Error messages are clear and actionable (include what to do next) | Must |
| NFR-004 | Works on Python 3.9+ across macOS, Linux, and Windows | Must |
| NFR-005 | Only stdlib imports in bundle.py and log.py (no added third-party deps) | Should |

---

## Security Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-SEC-001 | API key is never displayed in full — always masked in output | Must |
| REQ-SEC-002 | API key config file has restrictive permissions (user-only read/write) | Should |
| REQ-SEC-003 | All API communication uses HTTPS | Must |
| REQ-SEC-004 | No secrets are logged to the deployment log | Must |
| REQ-SEC-005 | Bundle mode does not follow symlinks outside the project | Should |
