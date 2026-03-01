# Traceability Matrix

Bidirectional mapping from requirements to user stories, code modules, and tests.

| REQ ID | User Story | Code Module | Test ID | Status |
|--------|-----------|-------------|---------|--------|
| FR-001 | US-001 | `cli.py:deploy`, `api.py:create` | `test_cli.py::test_deploy_*` | Implemented |
| FR-002 | US-002 | `cli.py:update`, `api.py:update` | `test_cli.py::test_update_*` | Implemented |
| FR-003 | US-003 | `cli.py:delete`, `api.py:delete` | `test_cli.py::test_delete_*` | Implemented |
| FR-004 | US-004 | `cli.py:list_sites`, `api.py:profile` | `test_cli.py::test_list_*` | Implemented |
| FR-005 | US-004 | `cli.py:profile`, `api.py:profile` | `test_cli.py::test_profile_*` | Implemented |
| FR-006 | US-005 | `cli.py:config_set_key`, `config.py:set_api_key` | `test_config.py::test_set_key` | Implemented |
| FR-007 | US-005 | `cli.py:config_show`, `config.py:get_config` | `test_config.py::test_show` | Implemented |
| FR-008 | US-005 | `config.py:get_api_key` | `test_config.py::test_key_priority` | Implemented |
| FR-009 | US-006 | `bundle.py:scan_html` | `test_bundle.py::test_scan_*` | Implemented |
| FR-010 | US-006 | `bundle.py:_collect_all_refs` | `test_bundle.py::test_recursive_*` | Implemented |
| FR-011 | US-006 | `bundle.py:_build_staging_dir` | `test_bundle.py::test_rewrite_*` | Implemented |
| FR-012 | US-006 | `bundle.py:create_bundle` | `test_bundle.py::test_create_bundle` | Implemented |
| FR-013 | US-006 | `bundle.py:cleanup_bundle`, `cli.py:deploy` (finally) | `test_bundle.py::test_cleanup` | Implemented |
| FR-014 | US-006 | `bundle.py:scan_html` | `test_bundle.py::test_skip_*` | Implemented |
| FR-015 | US-007 | `log.py:log_event`, `cli.py:deploy/update/delete` | `test_log.py::test_log_event` | Implemented |
| FR-016 | US-007 | `cli.py:log_cmd`, `log.py:read_log` | `test_log.py::test_read_log` | Implemented |
| FR-017 | US-007 | `log.py:read_log(tail=)` | `test_log.py::test_read_tail` | Implemented |
| FR-018 | US-007 | `log.py:clear_log` | `test_log.py::test_clear_log` | Implemented |
| FR-019 | US-001 | `api.py:_normalize_domain` | `test_api.py::test_normalize_*` | Implemented |
| FR-020 | US-001 | `cli.py:deploy` | `test_cli.py::test_deploy_prompt` | Implemented |
| FR-021 | US-003 | `cli.py:delete` | `test_cli.py::test_delete_confirm` | Implemented |
| FR-022 | US-008 | `api.py:create/update` | `test_api.py::test_password_*` | Implemented |
| NFR-001 | — | All modules | — | Met (no network for local ops) |
| NFR-002 | — | `cli.py` | — | Met (Rich used throughout) |
| NFR-003 | — | `cli.py` | — | Met (error messages include guidance) |
| NFR-004 | — | `pyproject.toml` | — | Met (requires-python >= 3.9) |
| NFR-005 | — | `bundle.py`, `log.py` | — | Met (stdlib only) |
| REQ-SEC-001 | — | `config.py:mask_key` | `test_config.py::test_mask_key` | Implemented |
| REQ-SEC-002 | — | `config.py:_save_config` | — | Not implemented |
| REQ-SEC-003 | — | `api.py` (BASE_URL uses https) | — | Met |
| REQ-SEC-004 | — | `log.py:log_event` | `test_log.py::test_no_secrets` | Implemented |
| REQ-SEC-005 | — | `bundle.py` | — | Not implemented |
