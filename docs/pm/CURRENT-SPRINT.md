# Current Sprint

## Bolt 9 — Security Foundation + Team Infrastructure Backlog (2026-03-04)

**Status:** Complete
**Size:** M
**Scope:** Migrate Cognito client secret to Secrets Manager (B-011), add custom IAM policy for Lambda@Edge (B-012), add team infrastructure backlog tickets (B-013, B-014, B-015).

### Items
- **B-011:** Migrate Cognito client secret from Lambda@Edge deployment package to AWS Secrets Manager
- **B-012:** Custom IAM inline policy for Lambda@Edge role — scoped to single secret ARN

### Completed
- [x] Secrets Manager resource added to SAM template (`CognitoClientSecret`)
- [x] Custom IAM inline policy (`TinyGoAuthSecrets`) on `AuthFunctionRole`
- [x] `_get_client_secret()` with SM caching + backward-compat fallback in `auth.py`
- [x] 3 callsites updated to use `_get_client_secret()` instead of `config.get("client_secret")`
- [x] `config.json` updated: `secret_arn` replaces `client_secret`
- [x] `_store_client_secret_in_sm()` helper added to `aws_cli.py`
- [x] `init()` updated: stores secret in SM, writes `secret_arn` in phase 2 config
- [x] 7 new tests (5 for `_get_client_secret`, 2 for `_store_client_secret_in_sm`)
- [x] Existing init tests updated with SM mock chain
- [x] B-013, B-014, B-015 added to backlog
- [x] CHANGELOG, SECURITY, BACKLOG, SPRINT-LOG updated
