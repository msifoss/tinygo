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

    cfg.set_aws_config(
        {
            "region": "us-east-1",
            "bucket_name": "test-bucket",
            "distribution_id": "E123",
            "cloudfront_domain": "d111.cloudfront.net",
        }
    )
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


# ── init ────────────────────────────────────────────────────────────────


def test_init_requires_domain_prefix(runner):
    result = runner.invoke(aws, ["init"])
    assert result.exit_code != 0
    assert "domain-prefix" in result.output.lower() or "Missing" in result.output


@patch("tinygo.aws_cli.shutil.which", return_value="/usr/bin/sam")
@patch("tinygo.aws_cli._sam_build")
@patch("tinygo.aws_cli._sam_deploy")
@patch("tinygo.aws_cli._read_stack_outputs")
@patch("tinygo.aws_cli._get_client_secret")
@patch("tinygo.aws_cli._store_client_secret_in_sm", return_value=True)
@patch("tinygo.aws_cli._write_lambda_config")
@patch("tinygo.aws_cli.set_aws_config")
def test_init_two_phase_deploy(
    mock_set_config,
    mock_write_config,
    mock_store_sm,
    mock_secret,
    mock_outputs,
    mock_deploy,
    mock_build,
    mock_which,
    runner,
    tmp_path,
    monkeypatch,
):
    """init performs two-phase deploy: placeholder then real config."""
    import tinygo.aws_cli as aws_mod

    # Fake infra dir with template
    infra_dir = tmp_path / "infra"
    infra_dir.mkdir()
    (infra_dir / "template.yaml").write_text("AWSTemplateFormatVersion: 2010")
    (infra_dir / "lambda_edge").mkdir()
    monkeypatch.setattr(
        aws_mod,
        "Path",
        lambda x: (
            type("P", (), {"parent": type("PP", (), {"parent": tmp_path})()})()
            if x == aws_mod.__file__
            else __import__("pathlib").Path(x)
        ),
    )
    # Simpler: just patch the infra_dir resolution
    monkeypatch.setattr(aws_mod.Path, "__new__", __import__("pathlib").Path.__new__)

    mock_outputs.return_value = {
        "BucketName": "tinygo-sites-123",
        "DistributionId": "E123",
        "CloudFrontDomain": "d111.cloudfront.net",
        "UserPoolId": "us-east-1_ABC",
        "UserPoolClientId": "client123",
        "CognitoDomainPrefix": "myapp",
        "CognitoClientSecretArn": "arn:aws:secretsmanager:us-east-1:123:secret:tinygo/test",
    }
    mock_secret.return_value = "super-secret-value"

    runner.invoke(
        aws,
        [
            "init",
            "--domain-prefix",
            "myapp",
            "--region",
            "us-east-1",
        ],
    )

    # Build called twice (phase 1 + phase 2)
    assert mock_build.call_count == 2
    # Deploy called twice
    assert mock_deploy.call_count == 2
    # Config written twice (placeholder + real)
    assert mock_write_config.call_count == 2
    # Client secret retrieved
    mock_secret.assert_called_once_with("us-east-1", "us-east-1_ABC", "client123")
    # Secret stored in Secrets Manager
    mock_store_sm.assert_called_once_with(
        "us-east-1",
        "arn:aws:secretsmanager:us-east-1:123:secret:tinygo/test",
        "super-secret-value",
    )


@patch("tinygo.aws_cli.shutil.which", return_value="/usr/bin/sam")
@patch("tinygo.aws_cli._sam_build")
@patch("tinygo.aws_cli._sam_deploy")
@patch("tinygo.aws_cli._read_stack_outputs")
@patch("tinygo.aws_cli._get_client_secret")
@patch("tinygo.aws_cli._store_client_secret_in_sm", return_value=True)
@patch("tinygo.aws_cli._write_lambda_config")
@patch("tinygo.aws_cli.set_aws_config")
def test_init_saves_cognito_domain_prefix(
    mock_set_config,
    mock_write_config,
    mock_store_sm,
    mock_secret,
    mock_outputs,
    mock_deploy,
    mock_build,
    mock_which,
    runner,
    tmp_path,
    monkeypatch,
):
    """init saves cognito_domain_prefix to config."""
    mock_outputs.return_value = {
        "BucketName": "tinygo-sites-123",
        "DistributionId": "E123",
        "CloudFrontDomain": "d111.cloudfront.net",
        "UserPoolId": "us-east-1_ABC",
        "UserPoolClientId": "client123",
        "CognitoDomainPrefix": "myprefix",
        "CognitoClientSecretArn": "arn:aws:secretsmanager:us-east-1:123:secret:tinygo/test",
    }
    mock_secret.return_value = "secret"

    runner.invoke(
        aws,
        [
            "init",
            "--domain-prefix",
            "myprefix",
            "--region",
            "us-east-1",
        ],
    )

    # Check that set_aws_config was called with cognito_domain_prefix
    config_saved = mock_set_config.call_args[0][0]
    assert config_saved["cognito_domain_prefix"] == "myprefix"
    assert config_saved["cognito_secret_arn"] == "arn:aws:secretsmanager:us-east-1:123:secret:tinygo/test"


@patch("tinygo.aws_cli.shutil.which", return_value="/usr/bin/sam")
@patch("tinygo.aws_cli._sam_build")
@patch("tinygo.aws_cli._sam_deploy")
@patch("tinygo.aws_cli._read_stack_outputs")
@patch("tinygo.aws_cli._get_client_secret", return_value=None)
@patch("tinygo.aws_cli._store_client_secret_in_sm", return_value=True)
@patch("tinygo.aws_cli._write_lambda_config")
def test_init_fails_when_secret_unavailable(
    mock_write_config,
    mock_store_sm,
    mock_secret,
    mock_outputs,
    mock_deploy,
    mock_build,
    mock_which,
    runner,
):
    """init exits with error when client secret cannot be retrieved."""
    mock_outputs.return_value = {
        "BucketName": "b",
        "DistributionId": "E1",
        "CloudFrontDomain": "d.cloudfront.net",
        "UserPoolId": "us-east-1_X",
        "UserPoolClientId": "c1",
        "CognitoDomainPrefix": "p",
    }

    result = runner.invoke(
        aws,
        [
            "init",
            "--domain-prefix",
            "myprefix",
        ],
    )
    assert result.exit_code == 1
    assert "client secret" in result.output.lower()


@patch("tinygo.aws_cli.shutil.which", return_value="/usr/bin/sam")
@patch("tinygo.aws_cli._sam_build")
@patch("tinygo.aws_cli._sam_deploy")
@patch("tinygo.aws_cli._read_stack_outputs")
@patch("tinygo.aws_cli._get_client_secret")
@patch("tinygo.aws_cli._store_client_secret_in_sm", return_value=True)
@patch("tinygo.aws_cli._write_lambda_config")
@patch("tinygo.aws_cli.set_aws_config")
def test_init_writes_real_config_in_phase2(
    mock_set_config,
    mock_write_config,
    mock_store_sm,
    mock_secret,
    mock_outputs,
    mock_deploy,
    mock_build,
    mock_which,
    runner,
):
    """Phase 2 config.json has secret_arn (not client_secret) and real CloudFront domain."""
    mock_outputs.return_value = {
        "BucketName": "bucket",
        "DistributionId": "E999",
        "CloudFrontDomain": "abc123.cloudfront.net",
        "UserPoolId": "us-east-1_Pool",
        "UserPoolClientId": "clientXYZ",
        "CognitoDomainPrefix": "myapp",
        "CognitoClientSecretArn": "arn:aws:secretsmanager:us-east-1:123:secret:tinygo/test",
    }
    mock_secret.return_value = "the-real-secret"

    runner.invoke(
        aws,
        [
            "init",
            "--domain-prefix",
            "myapp",
            "--region",
            "us-east-1",
        ],
    )

    # Second call to _write_lambda_config is the real config
    real_config_call = mock_write_config.call_args_list[1]
    config_data = real_config_call[0][1]
    assert "client_secret" not in config_data
    assert config_data["secret_arn"] == "arn:aws:secretsmanager:us-east-1:123:secret:tinygo/test"
    assert config_data["cloudfront_domain"] == "abc123.cloudfront.net"
    assert config_data["callback_url"] == "https://abc123.cloudfront.net/_auth/callback"
    assert config_data["cognito_domain"] == "https://myapp.auth.us-east-1.amazoncognito.com"
    assert config_data["user_pool_id"] == "us-east-1_Pool"


@patch("tinygo.aws_cli.subprocess.run")
def test_store_client_secret_in_sm(mock_run):
    """_store_client_secret_in_sm calls AWS CLI to store the secret."""
    from tinygo.aws_cli import _store_client_secret_in_sm

    mock_run.return_value = MagicMock(returncode=0, stdout="{}")

    result = _store_client_secret_in_sm("us-east-1", "arn:aws:secretsmanager:us-east-1:123:secret:test", "my-secret")

    assert result is True
    args = mock_run.call_args[0][0]
    assert "secretsmanager" in args
    assert "put-secret-value" in args
    assert "my-secret" in args


@patch("tinygo.aws_cli.subprocess.run")
def test_store_client_secret_in_sm_failure(mock_run):
    """_store_client_secret_in_sm returns False on failure."""
    from tinygo.aws_cli import _store_client_secret_in_sm

    mock_run.return_value = MagicMock(returncode=1, stderr="error")

    result = _store_client_secret_in_sm("us-east-1", "arn:secret", "secret")

    assert result is False
