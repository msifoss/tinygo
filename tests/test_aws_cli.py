"""Tests for tinygo.aws_cli module."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from tinygo.aws_cli import aws


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def aws_config(tmp_path, monkeypatch):
    """Redirect config to temp dir and set up AWS config."""
    import tinygo.config as cfg

    monkeypatch.setattr(cfg, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(cfg, "ENV_FILE", tmp_path / ".env")
    monkeypatch.setattr(cfg, "CONFIG_YAML_FILE", tmp_path / "config.yaml")
    monkeypatch.setattr(cfg, "LEGACY_CONFIG_FILE", tmp_path / "config.json")

    cfg.set_aws_config({
        "region": "us-east-1",
        "bucket_name": "test-bucket",
        "distribution_id": "E123",
        "cloudfront_domain": "d111.cloudfront.net",
    })
    return tmp_path


# ── status ───────────────────────────────────────────────────────────────


def test_status_shows_config(runner, aws_config):
    result = runner.invoke(aws, ["status"])
    assert result.exit_code == 0
    assert "us-east-1" in result.output
    assert "test-bucket" in result.output


def test_status_not_configured(runner, tmp_path, monkeypatch):
    import tinygo.config as cfg

    monkeypatch.setattr(cfg, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(cfg, "CONFIG_YAML_FILE", tmp_path / "config.yaml")
    monkeypatch.setattr(cfg, "LEGACY_CONFIG_FILE", tmp_path / "config.json")

    result = runner.invoke(aws, ["status"])
    assert result.exit_code == 0
    assert "not configured" in result.output.lower()


# ── list ─────────────────────────────────────────────────────────────────


@patch("tinygo.aws_cli._get_aws_client")
def test_list_shows_sites(mock_client, runner, aws_config):
    client = MagicMock()
    client.list_sites.return_value = [
        {"name": "alpha", "file_count": 3, "total_size": 1500},
        {"name": "beta", "file_count": 1, "total_size": 500},
    ]
    mock_client.return_value = client

    result = runner.invoke(aws, ["list"])
    assert result.exit_code == 0
    assert "alpha" in result.output
    assert "beta" in result.output


@patch("tinygo.aws_cli._get_aws_client")
def test_list_empty(mock_client, runner, aws_config):
    client = MagicMock()
    client.list_sites.return_value = []
    mock_client.return_value = client

    result = runner.invoke(aws, ["list"])
    assert result.exit_code == 0
    assert "No sites found" in result.output


# ── deploy ───────────────────────────────────────────────────────────────


@patch("tinygo.aws_cli._get_aws_client")
def test_deploy_success(mock_client, runner, aws_config, tmp_path):
    html_file = tmp_path / "index.html"
    html_file.write_text("<html>Hello</html>")

    client = MagicMock()
    client.site_exists.return_value = False
    client.upload_site.return_value = ["sites/test/index.html"]
    client.invalidate_cache.return_value = "INV1"
    mock_client.return_value = client

    result = runner.invoke(aws, ["deploy", str(html_file), "--site", "test"])
    assert result.exit_code == 0
    assert "Deployed" in result.output


@patch("tinygo.aws_cli._get_aws_client")
def test_deploy_rejects_existing_site(mock_client, runner, aws_config, tmp_path):
    html_file = tmp_path / "index.html"
    html_file.write_text("<html>Hello</html>")

    client = MagicMock()
    client.site_exists.return_value = True
    mock_client.return_value = client

    result = runner.invoke(aws, ["deploy", str(html_file), "--site", "existing"])
    assert result.exit_code == 1
    assert "already exists" in result.output


# ── update ───────────────────────────────────────────────────────────────


@patch("tinygo.aws_cli._get_aws_client")
def test_update_success(mock_client, runner, aws_config, tmp_path):
    html_file = tmp_path / "index.html"
    html_file.write_text("<html>Updated</html>")

    client = MagicMock()
    client.site_exists.return_value = True
    client.upload_site.return_value = ["sites/test/index.html"]
    client.invalidate_cache.return_value = "INV2"
    mock_client.return_value = client

    result = runner.invoke(aws, ["update", str(html_file), "--site", "test"])
    assert result.exit_code == 0
    assert "Updated" in result.output


@patch("tinygo.aws_cli._get_aws_client")
def test_update_rejects_nonexistent_site(mock_client, runner, aws_config, tmp_path):
    html_file = tmp_path / "index.html"
    html_file.write_text("<html>Hello</html>")

    client = MagicMock()
    client.site_exists.return_value = False
    mock_client.return_value = client

    result = runner.invoke(aws, ["update", str(html_file), "--site", "nope"])
    assert result.exit_code == 1
    assert "does not exist" in result.output


# ── delete ───────────────────────────────────────────────────────────────


@patch("tinygo.aws_cli._get_aws_client")
def test_delete_with_confirm(mock_client, runner, aws_config):
    client = MagicMock()
    client.delete_site.return_value = 5
    mock_client.return_value = client

    result = runner.invoke(aws, ["delete", "--site", "test", "--yes"])
    assert result.exit_code == 0
    assert "Deleted" in result.output
    assert "5" in result.output


@patch("tinygo.aws_cli._get_aws_client")
def test_delete_no_files(mock_client, runner, aws_config):
    client = MagicMock()
    client.delete_site.return_value = 0
    mock_client.return_value = client

    result = runner.invoke(aws, ["delete", "--site", "empty", "--yes"])
    assert result.exit_code == 0
    assert "No files found" in result.output
