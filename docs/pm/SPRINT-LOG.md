# Sprint Log

## Bolt 3 — Config Migration to .env + YAML (2026-03-01)

**Size:** M
**Scope:** Migrate config from plaintext JSON to .env (secrets) + YAML (settings) with backward-compatible auto-migration.

**Completed:**
- Rewrote `tinygo/config.py` — secrets in `.env` via python-dotenv, settings in `config.yaml` via pyyaml
- Auto-migration from legacy `config.json` (moves key to `.env`, renames to `.json.bak`)
- YAML scaffold with commented-out setting suggestions
- Updated `tinygo/cli.py` — `config show` displays both file paths
- Added `python-dotenv>=1.0` and `pyyaml>=6.0` dependencies
- 8 new config tests (47 total)
- Created CHANGELOG.md (v0.1.0 + v0.2.0)
- Updated README.md, SECURITY.md, CLAUDE.md to reference new config format
- Version bump to 0.2.0

**Metrics:**
- Commits: 3
- Tests: 39 → 47 (+8)
- Files changed: 9
- Lines: +257 / -42

**Retro:**
- Plan-first approach (plan mode) caught all file changes upfront
- Bolt review caught 3 stale docs — worth running every time
- Config migration pattern (lazy migrate + .bak rename) is clean and non-destructive

---

## Bolt 2 — DLC Framework Bootstrap (2026-03-01)

**Size:** M
**Scope:** Create all foundational AI-DLC documents, test suite, and captain's log.

**Completed:**
- Created CLAUDE.md (AI context file)
- Created docs/REQUIREMENTS.md (22 FRs, 5 NFRs, 5 SECs)
- Created docs/USER-STORIES.md (8 user stories)
- Created docs/TRACEABILITY-MATRIX.md (full REQ-to-code mapping)
- Created SECURITY.md (security model, audit history)
- Created docs/standards/ (6 standards documents)
- Created docs/pm/ (framework, backlog, sprint tracking)
- Created test suite for all modules
- Created initial captain's log entry

**Retro:**
- Starting from zero DLC docs to full framework in one bolt is feasible but large
- Should have been sized as L, not M
- Test suite adds confidence for future changes

---

## Bolt 1 — Bundle Deploy & Deployment Logging (2026-03-01)

**Size:** M
**Scope:** Add `--bundle` flag to deploy/update and `tinygo log` command.

**Completed:**
- Created `tinygo/bundle.py` — HTML scanning, staging, path rewriting, zip creation
- Created `tinygo/log.py` — deployment event logging
- Modified `tinygo/cli.py` — added --bundle flag, log_event calls, tinygo log command
- Updated README.md with new features

**Retro:**
- Clean implementation — bundle and log modules use only stdlib
- try/finally pattern for temp file cleanup works well
- Plan-first approach avoided rework
