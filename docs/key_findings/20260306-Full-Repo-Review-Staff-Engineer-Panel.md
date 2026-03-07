# Full Repo Review — Staff Engineer Panel Analysis

**Date:** 2026-03-06
**Panel:** Tim (SpaceX), Rob (Roblox), Fran (Meta), Al (AWS Lambda@Edge/Secrets Manager), Will Larson (Moderator)
**Trigger:** `/staff-panel full repo review ... improve, clean, remove` after Bolt 9 completion

---

## Problem Statement

Full repo review of TinyGo (1,490 lines source, 1,627 lines tests, 486 lines Lambda@Edge) at the end of Bolt 9. The codebase has grown from a single-backend CLI to a dual-backend system (tiiny.host + AWS) across 9 bolts in 5 days. The mandate: improve, clean, remove.

| Metric | Value |
|--------|-------|
| Source modules | 8 (+ 1 Lambda@Edge) |
| Total source lines | ~1,976 |
| Test count | 118 passing |
| Commits | 23 |
| Open security items | 0 |
| Dead code (per ruff) | 0 |

---

## Panel Analysis

### Tim — Staff Engineer, SpaceX

**Risk assessment (P x C matrix):**

| Item | P | C | Score | Verdict |
|------|---|---|-------|---------|
| deploy/update drift in aws_cli.py | 0.6 | Medium | 3.0 | Fix |
| deploy/update drift in cli.py | 0.4 | Medium | 2.0 | Fix |
| `_format_size()` duplication | 0.2 | Low | 0.4 | Skip |
| Missing type hints in aws_cli.py | 0.1 | Low | 0.1 | Skip |
| Broad `except Exception` in auth.py | 0.3 | Medium | 1.5 | Fix |

**Key quote:** "You have 1,976 lines of working code and 118 passing tests. The best cleanup is the one that doesn't break that."

**Recommendation:** Extract deploy/update helper in aws_cli.py, narrow auth.py exceptions. 50 min.

**Unique contribution:** Spotted redundant `from pathlib import Path` inside function bodies in aws_cli.py — Path is already imported at module level.

---

### Rob — Staff Engineer, Roblox

**Risk assessment:** The deploy/update duplication is worse than cosmetic. Four copies of "bundle, call, log, output, cleanup" exist across cli.py and aws_cli.py. The real risk is not the duplication itself — it's that the copies WILL diverge as features are added to one and not the other.

**Key quote:** "You don't have a code duplication problem. You have a deploy-vs-update divergence risk. Fix the risk, not the aesthetic."

**Recommendation:** Extract helper in aws_cli.py (25 min) + cli.py (20 min). 45 min total.

**Unique contribution:** Explicitly rejected `_format_size()` as duplication — different signatures, different inputs, different call sites. Merging would create a worse API.

---

### Fran — Staff Engineer, Meta

**Risk assessment — two buckets:**

Fix yesterday: aws_cli.py deploy/update (40 identical lines), cli.py deploy/update (20 identical lines)

Don't care: `_format_size()`, type hints, `is_temp` patterns, broad exceptions in auth.py, magic TTLs

**Key quote:** "Pre-commit is a developer convenience; CI is the contract. Your ruff + pytest CI already catches real issues."

**Recommendation:** Extract both helpers, remove redundant imports. 37 min.

**Unique contribution:** Identified that `except Exception` in auth.py is actually a BEST PRACTICE for Lambda@Edge — resilience > observability at CDN edge. Narrowing exceptions is an anti-pattern for edge compute.

---

### Al — Staff Engineer, AWS (Lambda@Edge / Secrets Manager)

**Risk assessment:** Lambda@Edge code is textbook. Lazy boto3 import, cache-with-fallback, HMAC-signed state — all recommended patterns.

**Key quote:** "I've reviewed thousands of customer implementations worse than this. The Lambda@Edge code is textbook."

**Recommendation:** Fix `tempfile.mktemp()` (deprecated TOCTOU), move stdlib `import time` to module level, extract helpers. 36 min.

**Unique contribution:**
1. `tempfile.mktemp()` at bundle.py:213 is deprecated with a TOCTOU race condition — the only actual correctness bug in the repo
2. `import time` inside `invalidate_cache()` at aws_client.py:80 is needless lazy-loading of stdlib (unlike auth.py's boto3 which has genuine cold start cost)
3. Subprocess-based AWS CLI calls in init are fine — init already requires SAM CLI

---

## Consensus Matrix

| Question | Tim | Rob | Fran | Al |
|----------|-----|-----|------|-----|
| Extract aws_cli deploy/update helper | YES | YES | YES | YES |
| Extract cli.py deploy/update helper | NO | YES | YES | NO |
| Fix `_format_size()` duplication | NO | NO | NO | NO |
| Narrow `except Exception` in auth.py | YES | - | NO | NO |
| Add type hints to aws_cli.py | NO | NO | NO | NO |
| Fix `tempfile.mktemp()` | - | - | - | YES |
| Move `import time` in aws_client.py | - | - | - | YES |
| Remove redundant Path imports | YES | - | YES | - |
| Architectural refactor | NO | NO | NO | NO |

**Unanimous (4-of-4):** Extract aws_cli helper. No cross-module refactor. No type hints. No `_format_size()` merge.

**Majority (3-of-4):** Extract cli.py helper (Tim dissents). Do NOT narrow auth.py exceptions (Tim dissents).

---

## Clarifying Questions

| Question | Answer | Impact |
|----------|--------|--------|
| cli.py deploy/update change frequency? | 7 commits, stable since Bolt 5 | Weakens refactor case |
| aws_cli.py deploy/update change frequency? | 4 commits, actively changing (Bolt 6, 7, 9) | Strengthens refactor case |
| Is `tempfile.mktemp()` exploitable? | Low severity for CLI tool (requires local attacker + timing) | Still fix — it's deprecated |
| Does ruff catch redundant Path import? | No | Confirms it's a genuine wart |
| Any other deprecated stdlib calls? | No — only `tempfile.mktemp()` | Isolated issue |

---

## Will Larson's Decision

**Scope:** Rob's approach + Tim's discipline + Al's platform findings.

| Step | What | Why | Effort |
|------|------|-----|--------|
| 1 | Extract `_upload_site_flow()` in aws_cli.py | Unanimous: actively changing, 65% identical | 25 min |
| 2 | Extract `_deploy_or_update()` in cli.py | 3-of-4: cheap fix, consistent pattern | 15 min |
| 3 | Replace `tempfile.mktemp()` in bundle.py | Al: deprecated TOCTOU, 2-line fix | 5 min |
| 4 | Move `import time` to module level in aws_client.py | Al: pointless lazy import | 2 min |
| 5 | Remove redundant Path imports in aws_cli.py | Tim + Fran: already at module level | 2 min |
| 6 | Update tests | Safety net | 10 min |

**Total: ~60 minutes.**

### What's Explicitly Deferred

| Item | Rationale | Revisit |
|------|-----------|---------|
| `_format_size()` merge | 4-of-4 reject: different contracts | Never |
| Type hints on aws_cli helpers | 4-of-4 reject: zero risk reduction | If mypy adopted |
| Narrow auth.py exceptions | 3-of-4 reject: broad catches correct for edge | Never |
| Cross-module abstractions | 4-of-4 reject: backends share no runtime path | Third backend |
| subprocess to boto3 in init | Al: init requires SAM CLI anyway | Never |

---

## Key Takeaways

1. **Not all duplication is debt.** `_format_size()` with different signatures is NOT a problem.
2. **Change frequency predicts divergence risk.** aws_cli.py (4 commits) > cli.py (7 commits, stable).
3. **Lambda@Edge has different best practices.** Broad exception handling is correct for edge compute.
4. **Deprecated stdlib calls are real bugs.** `tempfile.mktemp()` is the only correctness issue in 1,976 lines.

---

## Files Referenced

| File | Lines | Role |
|------|-------|------|
| tinygo/aws_cli.py | 483 | AWS CLI commands — deploy/update duplication, redundant imports |
| tinygo/cli.py | 275 | tiiny.host CLI — deploy/update duplication |
| tinygo/bundle.py | 230 | HTML bundler — deprecated `tempfile.mktemp()` |
| tinygo/aws_client.py | 149 | AWS boto3 wrapper — unnecessary lazy `import time` |
| infra/lambda_edge/auth.py | 486 | Lambda@Edge auth — broad exceptions (CORRECT per panel) |
| tinygo/log.py | 72 | Deployment logging — `_format_size()` (NOT duplication per panel) |
| tinygo/api.py | 131 | tiiny.host API client — clean, no findings |
| tinygo/config.py | 147 | Config management — clean, no findings |

---

## Findings to Fix

| # | File | Lines | Description | Fix |
|---|------|-------|-------------|-----|
| F1 | tinygo/aws_cli.py | 305-356, 367-417 | deploy() and update() share 65% identical code | Extract `_upload_site_flow()` helper |
| F2 | tinygo/cli.py | 45-74, 86-113 | deploy() and update() share bundling/logging/cleanup | Extract `_deploy_or_update()` helper |
| F3 | tinygo/bundle.py | 213 | `tempfile.mktemp()` is deprecated (TOCTOU race) | Use `tempfile.NamedTemporaryFile(delete=False)` |
| F4 | tinygo/aws_client.py | 80 | `import time` inside function body (pointless lazy import) | Move to module level |
| F5 | tinygo/aws_cli.py | 307, 369 | `from pathlib import Path` re-imported inside function bodies | Remove (already imported at line 8) |
