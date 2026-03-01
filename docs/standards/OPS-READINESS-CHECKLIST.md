# Ops Readiness Checklist

Scored assessment of operational readiness for TinyGo CLI.

**Last scored:** 2026-03-01
**Score:** 8/20 (40%)

---

## Deployment & Distribution

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1 | Install procedure documented | PASS | README covers venv + pip install -e . |
| 2 | Entry point defined in pyproject.toml | PASS | `tinygo = "tinygo.cli:main"` |
| 3 | Version pinned in pyproject.toml | PASS | 0.1.0 |
| 4 | Dependencies pinned with minimum versions | PASS | click>=8.0, requests>=2.28, rich>=13.0 |
| 5 | Published to PyPI | FAIL | Not yet published |
| 6 | CI pipeline runs on push | FAIL | No CI configured |
| 7 | Automated tests run before release | FAIL | No test automation |

## Error Handling & Resilience

| # | Item | Status | Notes |
|---|------|--------|-------|
| 8 | API errors surfaced to user with actionable messages | PASS | TiinyError caught in all commands |
| 9 | Network timeout configured | FAIL | Using requests defaults |
| 10 | Retry logic for transient failures | FAIL | No retries |
| 11 | Temp file cleanup on failure | PASS | Bundle uses try/finally |
| 12 | Graceful handling of missing config | PASS | Clear message + guidance |

## Observability

| # | Item | Status | Notes |
|---|------|--------|-------|
| 13 | Deployment events logged locally | PASS | deployments.log via log.py |
| 14 | Verbose/debug mode available | FAIL | No --verbose flag |
| 15 | Version visible via --version | PASS | Click version_option configured |

## Security

| # | Item | Status | Notes |
|---|------|--------|-------|
| 16 | API key masked in output | PASS | mask_key() shows first/last 4 |
| 17 | HTTPS enforced | PASS | BASE_URL uses https:// |
| 18 | Config file permissions restricted | FAIL | Not enforced |
| 19 | No secrets in logs | PASS | Log records domain/file only |
| 20 | Dependency vulnerability scanning | FAIL | No scanning configured |

---

## Summary

- **Passing:** 11/20
- **Failing:** 9/20
- **Score:** 55%

### Priority fixes
1. Add CI pipeline with test + lint
2. Add request timeout to TiinyClient
3. Restrict config file permissions
4. Add --verbose flag for debugging
