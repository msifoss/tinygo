"""Tests for tinygo.config module."""

import json
import os

import pytest

from tinygo.config import get_api_key, get_config, mask_key, set_api_key


@pytest.fixture()
def config_dir(tmp_path, monkeypatch):
    """Redirect config to a temp directory."""
    import tinygo.config as cfg

    monkeypatch.setattr(cfg, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(cfg, "CONFIG_FILE", tmp_path / "config.json")
    return tmp_path


def test_set_and_get_api_key(config_dir):
    set_api_key("test-key-123")
    config_file = config_dir / "config.json"
    assert config_file.exists()
    data = json.loads(config_file.read_text())
    assert data["api_key"] == "test-key-123"


def test_get_api_key_from_config(config_dir):
    set_api_key("from-config")
    assert get_api_key() == "from-config"


def test_get_api_key_cli_flag_takes_priority(config_dir):
    set_api_key("from-config")
    assert get_api_key("from-flag") == "from-flag"


def test_get_api_key_env_takes_priority_over_config(config_dir, monkeypatch):
    set_api_key("from-config")
    monkeypatch.setenv("TIINY_API_KEY", "from-env")
    assert get_api_key() == "from-env"


def test_get_api_key_cli_flag_beats_env(config_dir, monkeypatch):
    monkeypatch.setenv("TIINY_API_KEY", "from-env")
    assert get_api_key("from-flag") == "from-flag"


def test_get_api_key_returns_none_when_nothing_set(config_dir, monkeypatch):
    monkeypatch.delenv("TIINY_API_KEY", raising=False)
    assert get_api_key() is None


def test_get_config_empty(config_dir):
    assert get_config() == {}


def test_get_config_after_set(config_dir):
    set_api_key("abc")
    cfg = get_config()
    assert cfg["api_key"] == "abc"


def test_mask_key_long():
    assert mask_key("abcdefghijklmnop") == "abcd...mnop"


def test_mask_key_short():
    assert mask_key("abcd") == "****"


def test_mask_key_exactly_8():
    assert mask_key("12345678") == "****"


def test_mask_key_9_chars():
    assert mask_key("123456789") == "1234...6789"
