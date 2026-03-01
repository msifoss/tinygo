"""Configuration management for TinyGo CLI."""

import json
import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".tinygo"
CONFIG_FILE = CONFIG_DIR / "config.json"


def _load_config() -> dict:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def _save_config(config: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2) + "\n")


def get_api_key(cli_key: str | None = None) -> str | None:
    """Resolve API key with priority: CLI flag > env var > config file."""
    if cli_key:
        return cli_key
    env_key = os.environ.get("TIINY_API_KEY")
    if env_key:
        return env_key
    config = _load_config()
    return config.get("api_key")


def set_api_key(key: str) -> None:
    """Save API key to config file."""
    config = _load_config()
    config["api_key"] = key
    _save_config(config)


def get_config() -> dict:
    """Return the full config dict."""
    return _load_config()


def mask_key(key: str) -> str:
    """Mask an API key for display, showing only first 4 and last 4 chars."""
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}...{key[-4:]}"
