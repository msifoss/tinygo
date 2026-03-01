"""Deployment event logging for TinyGo CLI."""

import os
from datetime import datetime
from pathlib import Path

from tinygo.config import CONFIG_DIR

LOG_FILE = CONFIG_DIR / "deployments.log"


def _format_size(file_path: str | Path | None) -> str:
    """Return a human-readable file size string, or empty if not applicable."""
    if file_path is None:
        return ""
    try:
        size = Path(file_path).stat().st_size
    except OSError:
        return ""
    if size < 1024:
        return f"{size}B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f}KB"
    else:
        return f"{size / (1024 * 1024):.1f}MB"


def log_event(
    action: str,
    domain: str,
    success: bool,
    file_path: str | None = None,
    url: str | None = None,
    error: str | None = None,
) -> None:
    """Append a deployment event to the log file.

    Fields are tab-separated:
    ``timestamp  ACTION  STATUS  domain  [file]  [size]  [detail]``
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "SUCCESS" if success else "FAIL"
    file_col = Path(file_path).name if file_path else ""
    size_col = _format_size(file_path) if file_path else ""
    detail = url if success and url else (f'"{error}"' if error else "")

    fields = [timestamp, action.upper(), status, domain, file_col, size_col, detail]
    line = "\t".join(fields)

    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def read_log(tail: int | None = None) -> list[str]:
    """Return log lines, optionally only the last *tail* entries."""
    if not LOG_FILE.exists():
        return []
    lines = LOG_FILE.read_text().splitlines()
    if tail is not None:
        lines = lines[-tail:]
    return lines


def clear_log() -> None:
    """Delete the log file."""
    try:
        LOG_FILE.unlink(missing_ok=True)
    except OSError:
        pass
