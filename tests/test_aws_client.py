"""Tests for tinygo.aws_client module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tinygo.aws_client import AWSClient, AWSError, S3_PREFIX, _content_type


# ── helpers ──────────────────────────────────────────────────────────────


@pytest.fixture()
def staging_dir(tmp_path):
    """Create a minimal staging directory."""
    (tmp_path / "index.html").write_text("<html>Hello</html>")
    css = tmp_path / "css"
    css.mkdir()
    (css / "style.css").write_text("body{}")
    return tmp_path


@pytest.fixture()
def aws(staging_dir):
    """Return an AWSClient with mocked boto3 clients."""
    with patch("tinygo.aws_client.boto3") as mock_boto:
        mock_s3 = MagicMock()
        mock_cf = MagicMock()
        mock_boto.client.side_effect = lambda svc, **kw: (
            mock_s3 if svc == "s3" else mock_cf
        )
        client = AWSClient(
            region="us-east-1",
            bucket_name="test-bucket",
            distribution_id="E123",
        )
        client._mock_s3 = mock_s3
        client._mock_cf = mock_cf
        yield client


# ── _content_type ────────────────────────────────────────────────────────


def test_content_type_html():
    assert _content_type(Path("index.html")) == "text/html"


def test_content_type_css():
    assert _content_type(Path("style.css")) == "text/css"


def test_content_type_woff2():
    assert _content_type(Path("font.woff2")) == "font/woff2"


def test_content_type_webp():
    assert _content_type(Path("image.webp")) == "image/webp"


def test_content_type_svg():
    assert _content_type(Path("icon.svg")) == "image/svg+xml"


def test_content_type_wasm():
    assert _content_type(Path("app.wasm")) == "application/wasm"


def test_content_type_unknown():
    assert _content_type(Path("file.xyz123")) == "application/octet-stream"


# ── upload_site ──────────────────────────────────────────────────────────


def test_upload_site_uploads_all_files(aws, staging_dir):
    keys = aws.upload_site("my-site", staging_dir)
    assert len(keys) == 2
    assert f"{S3_PREFIX}/my-site/index.html" in keys
    assert f"{S3_PREFIX}/my-site/css/style.css" in keys
    assert aws._mock_s3.upload_file.call_count == 2


def test_upload_site_sets_content_type(aws, staging_dir):
    aws.upload_site("my-site", staging_dir)
    calls = aws._mock_s3.upload_file.call_args_list
    content_types = [c.kwargs.get("ExtraArgs", c[1].get("ExtraArgs", {})).get("ContentType") for c in calls]
    # Depending on call order, we should see text/html and text/css
    assert "text/html" in content_types
    assert "text/css" in content_types


def test_upload_site_raises_aws_error(aws, staging_dir):
    from botocore.exceptions import ClientError

    aws._mock_s3.upload_file.side_effect = ClientError(
        {"Error": {"Code": "403", "Message": "Forbidden"}}, "PutObject"
    )
    with pytest.raises(AWSError, match="S3 upload failed"):
        aws.upload_site("my-site", staging_dir)


# ── invalidate_cache ─────────────────────────────────────────────────────


def test_invalidate_cache_returns_id(aws):
    aws._mock_cf.create_invalidation.return_value = {
        "Invalidation": {"Id": "INV123"}
    }
    inv_id = aws.invalidate_cache("my-site")
    assert inv_id == "INV123"
    aws._mock_cf.create_invalidation.assert_called_once()


def test_invalidate_cache_sends_correct_path(aws):
    aws._mock_cf.create_invalidation.return_value = {
        "Invalidation": {"Id": "INV1"}
    }
    aws.invalidate_cache("my-site")
    call_args = aws._mock_cf.create_invalidation.call_args
    paths = call_args.kwargs.get("InvalidationBatch", call_args[1].get("InvalidationBatch", {}))["Paths"]["Items"]
    assert paths == [f"/{S3_PREFIX}/my-site/*"]


def test_invalidate_cache_raises_aws_error(aws):
    from botocore.exceptions import ClientError

    aws._mock_cf.create_invalidation.side_effect = ClientError(
        {"Error": {"Code": "403", "Message": "Forbidden"}}, "CreateInvalidation"
    )
    with pytest.raises(AWSError, match="CloudFront invalidation failed"):
        aws.invalidate_cache("my-site")


# ── delete_site ──────────────────────────────────────────────────────────


def test_delete_site_deletes_objects(aws):
    paginator = MagicMock()
    paginator.paginate.return_value = [
        {"Contents": [{"Key": "sites/x/index.html"}, {"Key": "sites/x/style.css"}]}
    ]
    aws._mock_s3.get_paginator.return_value = paginator

    count = aws.delete_site("x")
    assert count == 2
    aws._mock_s3.delete_objects.assert_called_once()


def test_delete_site_returns_zero_when_empty(aws):
    paginator = MagicMock()
    paginator.paginate.return_value = [{"Contents": []}]
    aws._mock_s3.get_paginator.return_value = paginator

    count = aws.delete_site("empty")
    assert count == 0


# ── list_sites ───────────────────────────────────────────────────────────


def test_list_sites_aggregates_by_prefix(aws):
    paginator = MagicMock()
    paginator.paginate.return_value = [
        {
            "Contents": [
                {"Key": "sites/alpha/index.html", "Size": 100},
                {"Key": "sites/alpha/style.css", "Size": 50},
                {"Key": "sites/beta/index.html", "Size": 200},
            ]
        }
    ]
    aws._mock_s3.get_paginator.return_value = paginator

    sites = aws.list_sites()
    assert len(sites) == 2
    alpha = next(s for s in sites if s["name"] == "alpha")
    assert alpha["file_count"] == 2
    assert alpha["total_size"] == 150
    beta = next(s for s in sites if s["name"] == "beta")
    assert beta["file_count"] == 1
    assert beta["total_size"] == 200


def test_list_sites_empty(aws):
    paginator = MagicMock()
    paginator.paginate.return_value = [{"Contents": []}]
    aws._mock_s3.get_paginator.return_value = paginator

    assert aws.list_sites() == []


# ── site_exists ──────────────────────────────────────────────────────────


def test_site_exists_true(aws):
    aws._mock_s3.list_objects_v2.return_value = {"KeyCount": 1}
    assert aws.site_exists("my-site") is True


def test_site_exists_false(aws):
    aws._mock_s3.list_objects_v2.return_value = {"KeyCount": 0}
    assert aws.site_exists("my-site") is False
