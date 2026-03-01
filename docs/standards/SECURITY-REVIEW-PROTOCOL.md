# Security Review Protocol

## Review Cadence

- **Per-phase:** Before each production-facing change (new feature, API change)
- **Quarterly:** Full review of all modules
- **On demand:** After any security-relevant code change

## Five-Persona Review Process

Security reviews use five analyst personas to ensure coverage:

1. **Attacker** — How can this be exploited? What are the attack vectors?
2. **Defender** — Are the right controls in place? Are they configured correctly?
3. **Auditor** — Is there a trail? Can we prove compliance?
4. **User** — Can a user accidentally expose themselves? Is the UX safe?
5. **Operator** — Can the system fail in a way that creates security exposure?

## Finding Severity Levels

| Severity | Definition | SLA |
|----------|-----------|-----|
| Critical | Active exploitation possible, data at risk | Fix within 24 hours |
| High | Exploitable with moderate effort | Fix within 7 days |
| Medium | Requires specific conditions to exploit | Fix within 30 days |
| Low | Theoretical risk, defense in depth | Fix at next release |
| Info | Observation, no direct risk | Track for awareness |

## Disposition Workflow

Each finding gets a disposition:
- **Fixed** — Code change resolves the issue
- **Accepted** — Risk acknowledged, documented rationale
- **Deferred** — Will fix later, tracked with timeline
- **Won't Fix** — Not applicable, documented compensating controls

## Review Archive

Reviews are stored in `docs/security/` with date-prefixed filenames:
- `docs/security/2026-03-01-initial-assessment.md`

## Current Findings

See `SECURITY.md` for the current finding tracker.
