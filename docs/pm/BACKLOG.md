# Backlog

**Last groomed:** 2026-03-02

## Must

| ID | Item | Size | Status |
|----|------|------|--------|
| B-001 | Publish to PyPI | M | Executable |
| B-002 | Add CI pipeline (GitHub Actions) | M | Executable |

## Should

| ID | Item | Size | Status |
|----|------|------|--------|
| B-005 | Add --verbose flag for debug output | S | Executable |
| B-007 | Add dependency vulnerability scanning | S | Blocked (needs CI first) |
| B-011 | Migrate Cognito client secret to Secrets Manager (REQ-SEC-006) | M | Executable |
| B-012 | Custom Lambda@Edge IAM policy (REQ-SEC-014) | S | Executable |

## Could

| ID | Item | Size | Status |
|----|------|------|--------|
| B-008 | Custom domain support in CLI | M | Executable |
| B-009 | `tinygo open` command to open site in browser | S | Executable |
| B-010 | Tab completion for shell | M | Executable |

## Done (Bolt 7)

| ID | Item | Bolt |
|----|------|------|
| B-003 | Enforce .env file permissions (REQ-SEC-002) | 7 |
| B-004 | Add request timeout to TiinyClient | 7 |
| B-006 | Guard against symlink traversal in bundle mode (REQ-SEC-005) | 7 |
