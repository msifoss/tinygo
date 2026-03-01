"""Configuration management for TinyGo CLI."""

import json
import os
from pathlib import Path

import yaml
from dotenv import dotenv_values, set_key as dotenv_set_key

CONFIG_DIR = Path.home() / ".tinygo"
ENV_FILE = CONFIG_DIR / ".env"
CONFIG_YAML_FILE = CONFIG_DIR / "config.yaml"
LEGACY_CONFIG_FILE = CONFIG_DIR / "config.json"

_YAML_SCAFFOLD = """\
# TinyGo configuration
# default_domain: my-site
# log_level: info
# auto_open: false
# default_password:
"""


def _migrate_legacy_config() -> None:
    """Move api_key from legacy config.json to .env, then rename to .json.bak."""
    if not LEGACY_CONFIG_FILE.exists():
        return

    try:
        data = json.loads(LEGACY_CONFIG_FILE.read_text())
    except (json.JSONDecodeError, ValueError):
        # Corrupt JSON — rename it out of the way without migrating
        LEGACY_CONFIG_FILE.rename(LEGACY_CONFIG_FILE.with_suffix(".json.bak"))
        return

    key = data.get("api_key")
    if key and not _load_env_key():
        _save_env_key(key)

    LEGACY_CONFIG_FILE.rename(LEGACY_CONFIG_FILE.with_suffix(".json.bak"))


def _load_env_key() -> str | None:
    """Read TIINY_API_KEY from the .env file."""
    if not ENV_FILE.exists():
        return None
    values = dotenv_values(ENV_FILE)
    return values.get("TIINY_API_KEY")


def _save_env_key(key: str) -> None:
    """Write TIINY_API_KEY to the .env file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not ENV_FILE.exists():
        ENV_FILE.touch()
    dotenv_set_key(str(ENV_FILE), "TIINY_API_KEY", key)


def _load_yaml_config() -> dict:
    """Load settings from config.yaml."""
    if not CONFIG_YAML_FILE.exists():
        return {}
    text = CONFIG_YAML_FILE.read_text()
    data = yaml.safe_load(text)
    if data is None:
        return {}
    return data


def _save_yaml_config(config: dict) -> None:
    """Write settings to config.yaml."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_YAML_FILE.write_text(yaml.dump(config, default_flow_style=False))


def _ensure_yaml_exists() -> None:
    """Create config.yaml with commented-out scaffold if it doesn't exist."""
    if CONFIG_YAML_FILE.exists():
        return
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_YAML_FILE.write_text(_YAML_SCAFFOLD)


def get_api_key(cli_key: str | None = None) -> str | None:
    """Resolve API key with priority: CLI flag > env var > .env file."""
    if cli_key:
        return cli_key
    env_key = os.environ.get("TIINY_API_KEY")
    if env_key:
        return env_key
    _migrate_legacy_config()
    return _load_env_key()


def set_api_key(key: str) -> None:
    """Save API key to .env file and ensure config.yaml scaffold exists."""
    _save_env_key(key)
    _ensure_yaml_exists()


def get_config() -> dict:
    """Return merged config: YAML settings + api_key from .env."""
    _migrate_legacy_config()
    config = _load_yaml_config()
    key = _load_env_key()
    if key:
        config["api_key"] = key
    return config


def mask_key(key: str) -> str:
    """Mask an API key for display, showing only first 4 and last 4 chars."""
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}...{key[-4:]}"


# ── AWS configuration ────────────────────────────────────────────────────


def get_aws_config() -> dict | None:
    """Return the ``aws:`` section from config.yaml, or *None* if not set."""
    config = _load_yaml_config()
    aws = config.get("aws")
    if not aws or not isinstance(aws, dict):
        return None
    return aws


def set_aws_config(aws_config: dict) -> None:
    """Write *aws_config* under the ``aws:`` key in config.yaml."""
    config = _load_yaml_config()
    config["aws"] = aws_config
    _save_yaml_config(config)


def is_aws_configured() -> bool:
    """Return *True* if required AWS fields are present in config.yaml."""
    aws = get_aws_config()
    if aws is None:
        return False
    required = {"region", "bucket_name", "distribution_id"}
    return required.issubset(aws.keys())
