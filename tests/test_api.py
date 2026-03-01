"""Tests for tinygo.api module."""

import string

from tinygo.api import _normalize_domain, generate_password


def test_normalize_domain_adds_suffix():
    assert _normalize_domain("my-site") == "my-site.tiiny.site"


def test_normalize_domain_preserves_existing_suffix():
    assert _normalize_domain("my-site.tiiny.site") == "my-site.tiiny.site"


def test_normalize_domain_empty():
    assert _normalize_domain("") == ".tiiny.site"


def test_normalize_domain_with_dots():
    assert _normalize_domain("my.custom.site") == "my.custom.site.tiiny.site"


# ── generate_password ────────────────────────────────────────────────────


def test_generate_password_length():
    pw = generate_password()
    assert len(pw) == 15


def test_generate_password_character_set():
    allowed = set(string.ascii_letters + string.digits + "!#$%&*+-=?@^_")
    pw = generate_password()
    assert all(c in allowed for c in pw)


def test_generate_password_uniqueness():
    assert generate_password() != generate_password()
