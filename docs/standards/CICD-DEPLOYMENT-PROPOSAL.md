# CI/CD Deployment Proposal

## Current State

- **Deployment:** Manual — `pip install -e .` locally, then `tinygo deploy`
- **Testing:** Manual — `pytest tests/` run by developer
- **Linting:** None configured
- **Publishing:** Not published to PyPI

## Proposed Pipeline

### Phase 1: GitHub Actions CI (immediate)

Trigger on push to `main` and pull requests.

```yaml
Jobs:
  lint:    ruff check + ruff format --check
  test:    pytest tests/ on Python 3.9, 3.11, 3.12
```

### Phase 2: Automated release (future)

Trigger on git tag push (`v*`).

```yaml
Jobs:
  test:    full test suite
  build:   python -m build
  publish: twine upload to PyPI
```

## Environments

| Environment | Purpose | Trigger |
|-------------|---------|---------|
| CI | Lint + test on every push | Push to main, PRs |
| Release | Build + publish to PyPI | Tag push (v*) |

## Rollback Strategy

- PyPI: yank the bad version, publish a patch
- CLI tool runs locally — users control their own version

## Prerequisites

- [ ] Test suite exists and passes
- [ ] Linting configured (ruff)
- [ ] PyPI account and API token set up
- [ ] GitHub Actions workflow file created
