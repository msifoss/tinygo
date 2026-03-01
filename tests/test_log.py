"""Tests for tinygo.log module."""

import pytest

from tinygo.log import _format_size, clear_log, log_event, read_log


@pytest.fixture(autouse=True)
def isolated_log(tmp_path, monkeypatch):
    """Redirect log file to a temp directory."""
    import tinygo.log as log_mod

    monkeypatch.setattr(log_mod, "LOG_FILE", tmp_path / "deployments.log")
    # Also patch CONFIG_DIR so mkdir doesn't fail
    monkeypatch.setattr(log_mod, "CONFIG_DIR", tmp_path)
    return tmp_path


def test_log_event_creates_file(isolated_log):
    log_event("DEPLOY", "my-site", success=True, url="https://my-site.tiiny.site")
    log_file = isolated_log / "deployments.log"
    assert log_file.exists()
    content = log_file.read_text()
    assert "DEPLOY" in content
    assert "SUCCESS" in content
    assert "my-site" in content
    assert "https://my-site.tiiny.site" in content


def test_log_event_failure(isolated_log):
    log_event("DEPLOY", "bad-site", success=False, error="Domain not valid")
    content = (isolated_log / "deployments.log").read_text()
    assert "FAIL" in content
    assert '"Domain not valid"' in content


def test_log_event_with_file_path(isolated_log):
    # Create a test file to get its size
    test_file = isolated_log / "index.html"
    test_file.write_text("<html></html>")
    log_event("DEPLOY", "my-site", success=True, file_path=str(test_file))
    content = (isolated_log / "deployments.log").read_text()
    assert "index.html" in content


def test_read_log_empty(isolated_log):
    assert read_log() == []


def test_read_log_returns_lines(isolated_log):
    log_event("DEPLOY", "site-1", success=True)
    log_event("DELETE", "site-1", success=True)
    lines = read_log()
    assert len(lines) == 2
    assert "DEPLOY" in lines[0]
    assert "DELETE" in lines[1]


def test_read_log_tail(isolated_log):
    for i in range(10):
        log_event("DEPLOY", f"site-{i}", success=True)
    lines = read_log(tail=3)
    assert len(lines) == 3
    assert "site-7" in lines[0]
    assert "site-8" in lines[1]
    assert "site-9" in lines[2]


def test_clear_log(isolated_log):
    log_event("DEPLOY", "my-site", success=True)
    assert (isolated_log / "deployments.log").exists()
    clear_log()
    assert not (isolated_log / "deployments.log").exists()


def test_clear_log_when_no_file(isolated_log):
    """clear_log should not raise if log doesn't exist."""
    clear_log()


def test_log_event_no_secrets(isolated_log):
    """Verify API keys and passwords are never written to the log."""
    log_event(
        "DEPLOY", "my-site", success=True,
        file_path=None, url="https://my-site.tiiny.site"
    )
    content = (isolated_log / "deployments.log").read_text()
    # Log should not contain any key-like patterns
    assert "api_key" not in content.lower()
    assert "password" not in content.lower()


def test_format_size_none():
    assert _format_size(None) == ""


def test_format_size_bytes(tmp_path):
    f = tmp_path / "tiny.txt"
    f.write_text("hi")
    result = _format_size(str(f))
    assert result.endswith("B")
    assert "K" not in result


def test_format_size_kilobytes(tmp_path):
    f = tmp_path / "medium.txt"
    f.write_text("x" * 2048)
    result = _format_size(str(f))
    assert "KB" in result


def test_format_size_missing_file():
    assert _format_size("/nonexistent/file.txt") == ""
