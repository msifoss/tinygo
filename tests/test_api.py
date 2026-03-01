"""Tests for tinygo.api module."""

from tinygo.api import _normalize_domain


def test_normalize_domain_adds_suffix():
    assert _normalize_domain("my-site") == "my-site.tiiny.site"


def test_normalize_domain_preserves_existing_suffix():
    assert _normalize_domain("my-site.tiiny.site") == "my-site.tiiny.site"


def test_normalize_domain_empty():
    assert _normalize_domain("") == ".tiiny.site"


def test_normalize_domain_with_dots():
    assert _normalize_domain("my.custom.site") == "my.custom.site.tiiny.site"
