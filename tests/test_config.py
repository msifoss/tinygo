"""Tests for tinygo.config module."""

import json
import os

import pytest

from tinygo.config import (
    get_api_key,
    get_aws_config,
    get_config,
    is_aws_configured,
    mask_key,
    set_api_key,
    set_aws_config,
)


@pytest.fixture()
def config_dir(tmp_path, monkeypatch):
    """Redirect config to a temp directory."""
    import tinygo.config as cfg

    monkeypatch.setattr(cfg, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(cfg, "ENV_FILE", tmp_path / ".env")
    monkeypatch.setattr(cfg, "CONFIG_YAML_FILE", tmp_path / "config.yaml")
    monkeypatch.setattr(cfg, "LEGACY_CONFIG_FILE", tmp_path / "config.json")
    return tmp_path


# ── set / get API key ────────────────────────────────────────────────────


def test_set_and_get_api_key(config_dir):
    set_api_key("test-key-123")
    env_file = config_dir / ".env"
    assert env_file.exists()
    text = env_file.read_text()
    assert "TIINY_API_KEY" in text
    assert "test-key-123" in text


def test_set_api_key_creates_yaml_scaffold(config_dir):
    set_api_key("abc")
    yaml_file = config_dir / "config.yaml"
    assert yaml_file.exists()
    text = yaml_file.read_text()
    assert "# TinyGo configuration" in text
    assert "# default_domain:" in text


def test_get_api_key_from_env_file(config_dir):
    set_api_key("from-config")
    assert get_api_key() == "from-config"


def test_get_api_key_cli_flag_takes_priority(config_dir):
    set_api_key("from-config")
    assert get_api_key("from-flag") == "from-flag"


def test_get_api_key_env_takes_priority_over_env_file(config_dir, monkeypatch):
    set_api_key("from-config")
    monkeypatch.setenv("TIINY_API_KEY", "from-env")
    assert get_api_key() == "from-env"


def test_get_api_key_cli_flag_beats_env(config_dir, monkeypatch):
    monkeypatch.setenv("TIINY_API_KEY", "from-env")
    assert get_api_key("from-flag") == "from-flag"


def test_get_api_key_returns_none_when_nothing_set(config_dir, monkeypatch):
    monkeypatch.delenv("TIINY_API_KEY", raising=False)
    assert get_api_key() is None


# ── get_config ────────────────────────────────────────────────────────────


def test_get_config_empty(config_dir):
    assert get_config() == {}


def test_get_config_after_set(config_dir):
    set_api_key("abc")
    cfg = get_config()
    assert cfg["api_key"] == "abc"


def test_get_config_merges_yaml_and_env_key(config_dir):
    import yaml

    set_api_key("my-key")
    yaml_file = config_dir / "config.yaml"
    yaml_file.write_text(yaml.dump({"default_domain": "my-site"}))

    cfg = get_config()
    assert cfg["api_key"] == "my-key"
    assert cfg["default_domain"] == "my-site"


# ── mask_key ──────────────────────────────────────────────────────────────


def test_mask_key_long():
    assert mask_key("abcdefghijklmnop") == "abcd...mnop"


def test_mask_key_short():
    assert mask_key("abcd") == "****"


def test_mask_key_exactly_8():
    assert mask_key("12345678") == "****"


def test_mask_key_9_chars():
    assert mask_key("123456789") == "1234...6789"


# ── migration ─────────────────────────────────────────────────────────────


def test_migration_moves_key_from_json_to_env(config_dir):
    legacy = config_dir / "config.json"
    legacy.write_text(json.dumps({"api_key": "legacy-key"}))

    key = get_api_key()
    assert key == "legacy-key"

    env_file = config_dir / ".env"
    assert env_file.exists()
    assert "legacy-key" in env_file.read_text()

    assert not legacy.exists()
    assert (config_dir / "config.json.bak").exists()


def test_migration_skips_when_env_already_has_key(config_dir):
    set_api_key("existing-key")
    legacy = config_dir / "config.json"
    legacy.write_text(json.dumps({"api_key": "old-key"}))

    key = get_api_key()
    assert key == "existing-key"

    assert not legacy.exists()
    assert (config_dir / "config.json.bak").exists()


def test_migration_handles_corrupt_json(config_dir):
    legacy = config_dir / "config.json"
    legacy.write_text("{invalid json!!")

    key = get_api_key()
    assert key is None

    assert not legacy.exists()
    assert (config_dir / "config.json.bak").exists()


def test_migration_handles_no_legacy_file(config_dir):
    assert not (config_dir / "config.json").exists()
    key = get_api_key()
    assert key is None


def test_migration_via_get_config(config_dir):
    legacy = config_dir / "config.json"
    legacy.write_text(json.dumps({"api_key": "migrated-key"}))

    cfg = get_config()
    assert cfg["api_key"] == "migrated-key"

    assert not legacy.exists()
    assert (config_dir / "config.json.bak").exists()


def test_migration_json_without_api_key(config_dir):
    legacy = config_dir / "config.json"
    legacy.write_text(json.dumps({"other": "value"}))

    key = get_api_key()
    assert key is None

    assert not legacy.exists()
    assert (config_dir / "config.json.bak").exists()


# ── AWS config ───────────────────────────────────────────────────────────


def test_get_aws_config_returns_none_when_not_set(config_dir):
    assert get_aws_config() is None


def test_set_and_get_aws_config(config_dir):
    aws = {"region": "us-east-1", "bucket_name": "my-bucket", "distribution_id": "E123"}
    set_aws_config(aws)
    result = get_aws_config()
    assert result == aws


def test_set_aws_config_preserves_existing_yaml(config_dir):
    import yaml

    yaml_file = config_dir / "config.yaml"
    yaml_file.write_text(yaml.dump({"default_domain": "my-site"}))

    set_aws_config({"region": "us-east-1", "bucket_name": "b", "distribution_id": "d"})

    cfg = yaml.safe_load(yaml_file.read_text())
    assert cfg["default_domain"] == "my-site"
    assert cfg["aws"]["region"] == "us-east-1"


def test_is_aws_configured_true(config_dir):
    set_aws_config({"region": "us-east-1", "bucket_name": "b", "distribution_id": "d"})
    assert is_aws_configured() is True


def test_is_aws_configured_false_when_missing_fields(config_dir):
    set_aws_config({"region": "us-east-1"})
    assert is_aws_configured() is False
