# Cost Management Guide

## Overview

TinyGo is a free, open-source CLI tool. Costs are limited to the tiiny.host hosting service and development tooling.

## Cost Model

| Component | Cost | Notes |
|-----------|------|-------|
| TinyGo CLI | Free | Open source, no license fees |
| tiiny.host free tier | $0/month | 5 sites, 75MB max file size |
| tiiny.host paid plans | Varies | See [tiiny.host pricing](https://tiiny.host/pricing) |
| Python dependencies | Free | click, requests, rich — all MIT/BSD |
| GitHub hosting | Free | Public repository |

## Budget

No recurring infrastructure costs. The tool runs locally on the user's machine.

### User-facing costs

Users should be aware of their tiiny.host plan limits:
- `tinygo profile` shows current quota usage
- `tinygo list` shows site count vs max

## AI/Development Costs

| Item | Cost per session | Notes |
|------|-----------------|-------|
| Claude Code (development) | Usage-based | Anthropic API pricing |
| GitHub Actions CI (future) | Free tier | 2,000 minutes/month for public repos |

## Alert Thresholds

Not applicable — no infrastructure to monitor. Users manage their own tiiny.host account limits.

## Review Cadence

Review this document when:
- Adding infrastructure (CI/CD, hosting, etc.)
- Considering paid tiiny.host tiers
- Adding paid dependencies or services
