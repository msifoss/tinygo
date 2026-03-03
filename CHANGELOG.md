# Changelog

All notable changes to TinyGo will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed
- `.env` file now created with `0o600` permissions — owner-only read/write (REQ-SEC-002)
- Symlinks resolving outside the entry HTML's directory are now rejected during bundling (REQ-SEC-005)
- JWKS cache in Lambda@Edge now refreshes after 1 hour instead of persisting for Lambda lifetime (REQ-SEC-012)
- OAuth2 callback state parameter is now HMAC-signed with a cryptographic nonce to prevent CSRF (REQ-SEC-013)

### Changed
- All TiinyClient HTTP calls now have a 30-second timeout (B-004)
- Test count: 110 → 111

## [0.5.0] - 2026-03-01

### Added
- AWS backend: deploy sites to S3 + CloudFront via `tinygo aws deploy`
- AWS infrastructure provisioning via SAM (`tinygo aws init`) — creates S3 bucket, CloudFront distribution, Cognito user pool, and Lambda@Edge auth
- Cognito Hosted UI login with cookie-based authentication for browser users
- AWS commands: `aws init`, `aws deploy`, `aws update`, `aws delete`, `aws list`, `aws status`
- `AWSClient` module (`aws_client.py`) — boto3 wrapper for S3 uploads, CloudFront invalidation, site listing
- `AWSError` exception for AWS-specific error handling
- Lambda@Edge auth handler for viewer-request authentication
- AWS user guide (`docs/AWS-USER-GUIDE.md`)
- `boto3 >= 1.28` as optional dependency (`pip install tinygo[aws]`)
- 60 new tests (test_aws_cli, test_aws_client, test_lambda_auth)

### Changed
- `config.py` extended with `get_aws_config()`, `set_aws_config()`, `is_aws_configured()` for AWS config in `config.yaml`
- `bundle.py` updated to support `create_bundle_dir()` / `cleanup_bundle_dir()` for AWS deploy flow
- `cli.py` registers `aws` subcommand group
- Test count: 50 → 110

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
