# PM Framework

## Sprint Model

Work is organized into **bolts** — focused sprints with defined scope, typically 1-3 hours.

### Bolt lifecycle
1. Plan scope and acceptance criteria
2. Execute implementation
3. Verify (tests, manual check)
4. Retro (captain's log entry)

## Sizing Convention

| Size | Files | Duration | Risk |
|------|-------|----------|------|
| S | 1-2 | < 1 hour | Low |
| M | 3-5 | 1-3 hours | Medium |
| L | 5+ | Half day | High |
| XL | Avoid — split into smaller bolts | | |

## Backlog Management

- Backlog tracked in `docs/pm/BACKLOG.md`
- Items are prioritized: Must > Should > Could
- Each item has a size estimate
- Review and groom backlog at session start

## Blocker Tracking

Blockers are tracked inline in `docs/pm/CURRENT-SPRINT.md` with:
- Description
- Days open
- Mitigation or workaround

## Retrospectives

Captured in captain's log entries after each bolt:
- What went well
- What didn't
- Action items for next bolt
