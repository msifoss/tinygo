# Infrastructure Playbook

## Overview

TinyGo has minimal infrastructure — it is a local CLI tool that calls an external API.

## Components

| Component | Provider | Notes |
|-----------|----------|-------|
| Source code | GitHub | Public repo at github.com/msifoss/tinygo |
| Package registry | PyPI (future) | Not yet published |
| CI/CD | GitHub Actions (future) | See CICD-DEPLOYMENT-PROPOSAL.md |
| API backend | tiiny.host | External service, not managed by us |

## IaC Tooling

Not applicable — no cloud infrastructure to manage.

## Networking

All outbound requests go to `https://ext.tiiny.host` over HTTPS. No inbound connections.

## IAM Patterns

- tiiny.host API key per user, stored in `~/.tinygo/.env`
- GitHub repo access managed via GitHub settings

## Monitoring

- Local deployment log at `~/.tinygo/deployments.log`
- No remote monitoring (CLI tool)

## Disaster Recovery

- Code: GitHub repository with git history
- User config: `~/.tinygo/` directory (user responsibility to back up)
- No server-side state managed by TinyGo
