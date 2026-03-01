# Security

## Security Model

TinyGo is a CLI client that communicates with the tiiny.host external API. It does not run a server, accept network connections, or process untrusted input beyond local HTML files.

### Threat Surface

| Surface | Risk | Mitigation |
|---------|------|------------|
| API key storage | Key stored in plaintext at `~/.tinygo/config.json` | File is in user's home directory; masked in all CLI output (REQ-SEC-001) |
| API communication | Man-in-the-middle | All requests use HTTPS (REQ-SEC-003) |
| Bundle mode file access | Path traversal | Only follows references found in HTML; skips remote URLs |
| Deployment log | Sensitive data leakage | Log records domain and filename only — no API keys, passwords, or file contents (REQ-SEC-004) |

### Authentication

- API key is provided via `--api-key` flag, `TIINY_API_KEY` environment variable, or `~/.tinygo/config.json`
- Key is sent as `x-api-key` HTTP header over HTTPS
- Key is masked to first 4 and last 4 characters in all display output

### Data Protection

- No data is stored beyond the config file and deployment log
- Config file: `~/.tinygo/config.json` — contains API key
- Deployment log: `~/.tinygo/deployments.log` — contains timestamps, domains, filenames, and URLs only
- Bundle temp files are created in the system temp directory and cleaned up in a `finally` block

## Known Limitations

- Config file does not enforce restrictive file permissions (REQ-SEC-002 — not yet implemented)
- Bundle mode does not guard against symlink traversal (REQ-SEC-005 — not yet implemented)

## Vulnerability Reporting

If you discover a security vulnerability, please report it privately:

1. **Do not** open a public GitHub issue
2. Email the maintainer directly with details of the vulnerability
3. Include steps to reproduce and potential impact

We will acknowledge receipt within 48 hours and aim to provide a fix or mitigation plan within 7 days.

## Audit History

| Date | Type | Scope | Findings |
|------|------|-------|----------|
| 2026-03-01 | Initial assessment | All modules | 2 open items (REQ-SEC-002, REQ-SEC-005) |
