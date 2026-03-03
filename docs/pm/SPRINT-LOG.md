# Sprint Log

## Bolt 7 — Security Hardening & Doc Hygiene (2026-03-02)

**Size:** M
**Scope:** Fix all open security items not blocked by architecture decisions, add request timeout, backfill stale documentation (CHANGELOG, Sprint Log, CLAUDE.md), and run Mother Hen compliance sweep.

**Completed:**
- REQ-SEC-002: `.env` file created with `0o600` permissions (owner-only) in `config.py`
- REQ-SEC-005: Symlink traversal guard in `bundle.py` — rejects symlinks resolving outside entry HTML's directory
- REQ-SEC-012: JWKS cache in Lambda@Edge now has 1-hour TTL (`auth.py`)
- REQ-SEC-013: OAuth2 state parameter now HMAC-signed with nonce; callback verifies signature (`auth.py`)
- B-004: 30-second request timeout on all TiinyClient HTTP calls (`api.py`)
- Backfilled CHANGELOG v0.5.0 entry
- Backfilled Sprint Log Bolts 4, 5, 6
- Updated CLAUDE.md (version, module count, line count, test count, architecture)
- Updated SECURITY.md (AWS threat surfaces, resolved limitations, audit history)
- Updated CURRENT-SPRINT.md and BACKLOG.md
- Created git tags v0.1.0 through v0.5.0
- 1 new test (`test_callback_invalid_state_returns_401`), 4 tests updated for signed state

**Metrics:**
- Tests: 110 → 111 (+1)
- Files changed: 12
- Lines: +247 / -61
- Security items resolved: 4 (REQ-SEC-002, 005, 012, 013)
- Security items remaining: 2 (REQ-SEC-006, 014)

**Retro:**
- Mother Hen sweep was effective at catching all drift in one pass — 5 FAIL, 1 WARN out of 7 checks
- Doc backfill was the most time-consuming part; keeping sprint log current avoids this debt
- Security fixes were all small, focused changes — confirms the value of filing specific REQ-SEC items

---

## Bolt 6 — AWS S3 + CloudFront + Cognito Backend (2026-03-01)

**Size:** L
**Scope:** Add AWS deployment backend with S3 hosting, CloudFront CDN, Cognito user auth, and Lambda@Edge cookie-based authentication.

**Completed:**
- Created `tinygo/aws_client.py` — boto3 wrapper for S3 upload, CloudFront invalidation, site listing/deletion
- Created `tinygo/aws_cli.py` — Click command group: `aws init`, `aws deploy`, `aws update`, `aws delete`, `aws list`, `aws status`
- Two-phase SAM deployment in `aws init` (placeholder config → real config after stack outputs)
- Cognito Hosted UI login with Lambda@Edge cookie-based auth enforcement
- Extended `config.py` with `get_aws_config()`, `set_aws_config()`, `is_aws_configured()`
- Extended `bundle.py` with `create_bundle_dir()` / `cleanup_bundle_dir()` for AWS deploy flow
- Registered `aws` subcommand group in `cli.py`
- Created SAM infrastructure template (`infra/template.yaml`) and Lambda@Edge auth handler (`infra/lambda_edge/auth.py`)
- Created AWS user guide (`docs/AWS-USER-GUIDE.md`)
- Added `boto3 >= 1.28` as optional dependency
- 60 new tests (test_aws_cli, test_aws_client, test_lambda_auth)
- Version bump to 0.5.0

**Metrics:**
- Commits: 3
- Tests: 50 → 110 (+60)
- Files changed: 21
- Lines: +2,591 / -102

**Retro:**
- Largest bolt to date — should have been split into two (S3/CF infra + Cognito auth)
- Two-phase SAM deploy pattern handles the chicken-and-egg problem of stack outputs needed by Lambda config
- Lambda@Edge cookie auth adds significant surface area that needs security review

---

## Bolt 5 — Auto-Bundling by Default (2026-03-01)

**Size:** S
**Scope:** Make bundling the default behavior for deploy and update; switch from `--bundle` opt-in to `--no-bundle` opt-out.

**Completed:**
- Modified `tinygo/cli.py` — reversed bundle flag logic
- Updated CHANGELOG, CLAUDE.md, README.md
- Version bump to 0.4.0

**Metrics:**
- Commits: 3
- Tests: 50 (no change)
- Files changed: 5
- Lines: +23 / -17

**Retro:**
- Clean, small bolt — exactly the right scope
- No new tests needed since bundling logic was already tested

---

## Bolt 4 — Secure Defaults (2026-03-01)

**Size:** M
**Scope:** Auto-generate passwords and enable noIndex on all deployments; restrict password alphabet to web-safe characters.

**Completed:**
- Modified `tinygo/api.py` — auto-generated 15-char password, noIndex flag, siteSettings always populated
- `create()` and `update()` now return `(response_dict, password_used)` tuple
- Restricted password alphabet to web-safe special characters (`!#$%&*+-=?@^_`)
- Password displayed in console, never written to deployment log
- 3 new password tests + 1 alphabet fix
- Updated CHANGELOG, README, SECURITY.md, CLAUDE.md
- Version bumps: 0.3.0, 0.3.1

**Metrics:**
- Commits: 5
- Tests: 47 → 50 (+3)
- Files changed: 12
- Lines: +147 / -45

**Retro:**
- Quick hotfix cycle (0.3.0 → 0.3.1) for password alphabet issue — caught by real-world testing against tiiny.host
- Good pattern: security defaults baked in rather than optional

---

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
