# Backlog

**Last groomed:** 2026-03-04

## Must

| ID | Item | Size | Status |
|----|------|------|--------|
| — | No must items remaining | — | — |

## Should

| ID | Item | Size | Status |
|----|------|------|--------|
| B-005 | Add --verbose flag for debug output | S | Executable |
| B-007 | Add dependency vulnerability scanning | S | Executable |
| B-013 | Deploy API endpoint (API Gateway + Lambda) — MCP-callable | L | Blocked (needs B-014) |
| B-014 | Cloud audit log (DynamoDB) | M | Executable |
| B-015 | Multi-tenant site access control | L | Blocked (needs B-012, B-014) |

**B-013:** API Gateway HTTP API + Lambda accepting POST deploy requests with Cognito JWT auth. This is what an MCP server calls to trigger deploys. Returns status + URL.

**B-014:** DynamoDB table for deployment events (timestamp, user, action, site, size). Replaces local-only `deployments.log` as primary record. CLI writes to both. New `tinygo aws log` queries DynamoDB.

**B-015:** DynamoDB ownership records per site (owner, visibility: private/team/public). Lambda@Edge checks ownership before granting access. CLI enforces ownership on update/delete.

## Could

| ID | Item | Size | Status |
|----|------|------|--------|
| B-008 | Custom domain support in CLI | M | Executable |
| B-009 | `tinygo open` command to open site in browser | S | Executable |
| B-010 | Tab completion for shell | M | Executable |

## Done (Bolt 9)

| ID | Item | Bolt |
|----|------|------|
| B-011 | Migrate Cognito client secret to Secrets Manager (REQ-SEC-006) | 9 |
| B-012 | Custom Lambda@Edge IAM policy (REQ-SEC-014) | 9 |

## Done (Bolt 8)

| ID | Item | Bolt |
|----|------|------|
| B-001 | Publish to PyPI | 8 |
| B-002 | Add CI pipeline (GitHub Actions) | 8 |

## Done (Bolt 7)

| ID | Item | Bolt |
|----|------|------|
| B-003 | Enforce .env file permissions (REQ-SEC-002) | 7 |
| B-004 | Add request timeout to TiinyClient | 7 |
| B-006 | Guard against symlink traversal in bundle mode (REQ-SEC-005) | 7 |
