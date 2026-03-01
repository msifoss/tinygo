# Changelog

All notable changes to TinyGo will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.4.0] - 2026-03-01

### Changed
- Bundling is now on by default for `deploy` and `update` — linked local files are automatically packaged into a zip
- Replaced `--bundle` / `-b` opt-in flag with `--no-bundle` opt-out flag

## [0.3.1] - 2026-03-01

### Fixed
- Restricted password alphabet to web-safe special characters (`!#$%&*+-=?@^_`), replacing full `string.punctuation` which included backticks, quotes, and backslashes that broke tiiny.host password forms

## [0.3.0] - 2026-03-01

### Added
- Auto-generated 15-character password on every deploy and update (cryptographically strong via `secrets`)
- `noIndex` flag set on all deployments to block search engine indexing
- Password displayed in console output after successful deploy/update
- 3 new tests for password generation (length, character set, uniqueness)

### Changed
- `create()` and `update()` now return `(response_dict, password_used)` tuple
- `siteSettings` always includes `passwordProtected`, `password`, and `noIndex`
- Password is never written to the deployment log
- Test count: 47 → 50

## [0.2.0] - 2026-03-01

### Changed
- Migrated config from `config.json` to split format: secrets in `~/.tinygo/.env`, settings in `~/.tinygo/config.yaml`
- `config show` now displays both secrets path and config path
- Added `python-dotenv` and `pyyaml` as dependencies
- Test count: 39 → 47

### Added
- Automatic migration from legacy `config.json` — API key moved to `.env`, old file renamed to `.json.bak`
- YAML config scaffold with commented-out setting suggestions (`default_domain`, `log_level`, `auto_open`, `default_password`)

## [0.1.0] - 2026-03-01

### Added
- CLI commands: `deploy`, `update`, `delete`, `list`, `profile`, `config set-key`, `config show`
- `--bundle` flag to auto-zip multi-file HTML projects with linked assets
- Deployment event logging to `~/.tinygo/deployments.log` with `log` and `log --clear` commands
- API key resolution priority: CLI flag > `TIINY_API_KEY` env var > config file
- Rich console output with tables, status spinners, and colored text
- Domain normalization — auto-appends `.tiiny.site` suffix
- Password protection support via `--password` flag
- README, SECURITY.md, and project documentation

### Fixed
- Password protection now correctly includes `passwordProtected` flag in `siteSettings`
