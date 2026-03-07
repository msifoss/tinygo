# Security

## Security Model

TinyGo is a CLI client that communicates with the tiiny.host external API and optionally deploys to AWS (S3 + CloudFront + Cognito). The tiiny.host path does not run a server. The AWS path provisions infrastructure with Lambda@Edge for cookie-based authentication.

### Threat Surface

| Surface | Risk | Mitigation |
|---------|------|------------|
| API key storage | Key stored in `~/.tinygo/.env` | File is in user's home directory; separated from settings; masked in all CLI output (REQ-SEC-001) |
| API communication | Man-in-the-middle | All requests use HTTPS (REQ-SEC-003) |
| Bundle mode file access | Path traversal | Only follows references found in HTML; skips remote URLs |
| Deployment log | Sensitive data leakage | Log records domain and filename only — no API keys, passwords, or file contents (REQ-SEC-004) |
| AWS credentials | IAM access | Uses default AWS credential chain (aws configure / env vars); no credentials stored by TinyGo |
| Cognito client secret | Secret exposure | Stored in AWS Secrets Manager; Lambda@Edge fetches via API with 1-hour cache; config.json contains only the secret ARN (REQ-SEC-006) |
| Lambda@Edge IAM role | Over-privileged access | Custom inline policy scoped to single Secrets Manager secret ARN; managed policy limited to basic execution (REQ-SEC-014) |
| Lambda@Edge JWT auth | Token bypass | RS256 signature verification against Cognito JWKS; validates exp, iss, aud claims (REQ-SEC-007) |
| Cookie-based auth | Session hijacking | Cookies set with Secure, HttpOnly, SameSite=Lax attributes (REQ-SEC-008) |
| OAuth2 callback | CSRF / code injection | State parameter encodes original URI; authorization code exchanged server-side (REQ-SEC-009) |
| S3 bucket | Public access | All public access blocked; access only via CloudFront OAC (REQ-SEC-010) |
| SAM CLI invocation | Command injection | Arguments passed as list (not shell string); only trusted values from stack outputs (REQ-SEC-011) |

### Authentication

**tiiny.host path:**
- API key is provided via `--api-key` flag, `TIINY_API_KEY` environment variable, or `~/.tinygo/.env`
- Key is sent as `x-api-key` HTTP header over HTTPS
- Key is masked to first 4 and last 4 characters in all display output

**AWS path:**
- AWS credentials resolved via default boto3 credential chain (environment, profile, IAM role)
- Browser users authenticate via Cognito Hosted UI (OAuth2 authorization code flow)
- Lambda@Edge validates JWT tokens (RS256 with JWKS verification)
- Auth cookies: `tinygo_id_token`, `tinygo_access_token` (1h TTL), `tinygo_refresh_token` (30d TTL)

### Data Protection

- No data is stored beyond the config file and deployment log
- Secrets file: `~/.tinygo/.env` — contains API key
- Settings file: `~/.tinygo/config.yaml` — contains non-sensitive settings
- Deployment log: `~/.tinygo/deployments.log` — contains timestamps, domains, filenames, and URLs only
- Bundle temp files are created in the system temp directory and cleaned up in a `finally` block

## Known Limitations

No known security limitations at this time. All previously open items (REQ-SEC-006, REQ-SEC-014) have been resolved.

## Vulnerability Reporting

If you discover a security vulnerability, please report it privately:

1. **Do not** open a public GitHub issue
2. Email the maintainer directly with details of the vulnerability
3. Include steps to reproduce and potential impact

We will acknowledge receipt within 48 hours and aim to provide a fix or mitigation plan within 7 days.

## Audit History

| Date | Type | Scope | Findings |
|------|------|-------|----------|
| 2026-03-04 | Secrets Manager + IAM | template.yaml, auth.py, aws_cli.py | Resolved REQ-SEC-006 (client secret moved to Secrets Manager with caching), REQ-SEC-014 (custom IAM policy scoped to single secret ARN); 0 open items |
| 2026-03-02 | Security hardening | config.py, bundle.py, auth.py, api.py | Fixed REQ-SEC-002 (.env permissions), REQ-SEC-005 (symlink guard), REQ-SEC-012 (JWKS TTL), REQ-SEC-013 (CSRF nonce); added request timeout (B-004); 2 open items remain (REQ-SEC-006, REQ-SEC-014) |
| 2026-03-02 | AWS module review | aws_cli.py, aws_client.py, Lambda@Edge auth, SAM template | 4 new items (REQ-SEC-006, REQ-SEC-012, REQ-SEC-013, REQ-SEC-014); 6 new controls documented (REQ-SEC-006–011) |
| 2026-03-01 | Initial assessment | All modules | 2 open items (REQ-SEC-002, REQ-SEC-005) |
