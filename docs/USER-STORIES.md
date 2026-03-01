# User Stories

## Format

Each story follows: **As a [role], I want [capability], so that [benefit].**
Acceptance criteria use Given/When/Then format.

---

## US-001: Deploy a site

**As a** developer, **I want** to deploy an HTML file to tiiny.host from my terminal, **so that** I can publish a page without opening a browser.

**Acceptance Criteria:**
- Given I have a valid API key and an HTML file, when I run `tinygo deploy index.html --domain my-site`, then a new site is created and the URL is printed.
- Given I omit `--domain`, when I run `tinygo deploy index.html`, then I am prompted for a subdomain.
- Given the API returns an error, when I deploy, then the error message is printed and the process exits with code 1.

**Traces:** FR-001, FR-019, FR-020

---

## US-002: Update a site

**As a** developer, **I want** to update an existing site with new content, **so that** I can iterate without deleting and redeploying.

**Acceptance Criteria:**
- Given a site exists at `my-site.tiiny.site`, when I run `tinygo update index.html --domain my-site`, then the site content is replaced.

**Traces:** FR-002

---

## US-003: Delete a site

**As a** developer, **I want** to delete a site I no longer need, **so that** I free up my quota.

**Acceptance Criteria:**
- Given I run `tinygo delete --domain my-site`, when prompted, then I must confirm before deletion occurs.
- Given I pass `--yes`, when I run the delete, then the confirmation is skipped.

**Traces:** FR-003, FR-021

---

## US-004: List sites

**As a** developer, **I want** to see all my deployed sites and quota usage, **so that** I know what I have deployed and how much capacity remains.

**Acceptance Criteria:**
- Given I run `tinygo list`, when my account has sites, then a table is displayed with domain, type, and created date plus quota info.

**Traces:** FR-004

---

## US-005: Configure API key

**As a** developer, **I want** to save my API key once and have it persist, **so that** I don't have to pass it on every command.

**Acceptance Criteria:**
- Given I run `tinygo config set-key`, when I enter a key, then it is saved to `~/.tinygo/config.json`.
- Given I have a saved key, when I run any command, then the saved key is used automatically.
- Given I pass `--api-key` or set `TIINY_API_KEY`, when I run a command, then that key takes precedence.

**Traces:** FR-006, FR-007, FR-008

---

## US-006: Bundle deploy

**As a** developer, **I want** to deploy an HTML file that references local files from other directories, **so that** I don't have to manually copy and rewrite paths.

**Acceptance Criteria:**
- Given my HTML links to files via absolute paths, when I run `tinygo deploy index.html --bundle`, then all referenced files are bundled into a zip with rewritten relative paths.
- Given a linked file is missing, when I bundle, then the missing file is skipped silently.
- Given the deploy succeeds or fails, when the command finishes, then temp files are cleaned up.

**Traces:** FR-009, FR-010, FR-011, FR-012, FR-013, FR-014

---

## US-007: Deployment history

**As a** developer, **I want** to see a history of my deploys, updates, and deletes, **so that** I have a record of what I've done.

**Acceptance Criteria:**
- Given I have deployed and deleted sites, when I run `tinygo log`, then a table shows all events with timestamps, actions, status, and details.
- Given I pass `-n 5`, when I run `tinygo log -n 5`, then only the last 5 entries are shown.
- Given I run `tinygo log --clear`, then the log file is deleted.

**Traces:** FR-015, FR-016, FR-017, FR-018

---

## US-008: Password protection

**As a** developer, **I want** to password-protect a deployed site, **so that** only people with the password can view it.

**Acceptance Criteria:**
- Given I pass `--password s3cret`, when I deploy or update, then the site requires that password to access.

**Traces:** FR-022
