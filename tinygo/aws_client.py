"""AWS client for S3 + CloudFront site hosting."""

from __future__ import annotations

import mimetypes
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

# Extra MIME types not always in the default database.
_EXTRA_TYPES = {
    ".woff2": "font/woff2",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
    ".wasm": "application/wasm",
    ".mjs": "application/javascript",
}

S3_PREFIX = "sites"


class AWSError(Exception):
    """Raised when an AWS operation fails."""

    def __init__(self, detail: str, original: Exception | None = None):
        self.detail = detail
        self.original = original
        super().__init__(detail)


def _content_type(path: Path) -> str:
    """Resolve MIME type for a file path."""
    ct = _EXTRA_TYPES.get(path.suffix.lower())
    if ct:
        return ct
    ct, _ = mimetypes.guess_type(str(path))
    return ct or "application/octet-stream"


class AWSClient:
    """Upload, delete, and list static sites on S3 with CloudFront invalidation."""

    def __init__(self, region: str, bucket_name: str, distribution_id: str):
        self.region = region
        self.bucket_name = bucket_name
        self.distribution_id = distribution_id
        self.s3 = boto3.client("s3", region_name=region)
        self.cf = boto3.client("cloudfront", region_name=region)

    def upload_site(self, site_name: str, staging_dir: Path) -> list[str]:
        """Upload all files from *staging_dir* to ``sites/{site_name}/``.

        Returns a list of S3 keys that were uploaded.
        """
        staging_dir = Path(staging_dir)
        keys: list[str] = []
        try:
            for file_path in staging_dir.rglob("*"):
                if not file_path.is_file():
                    continue
                relative = file_path.relative_to(staging_dir)
                key = f"{S3_PREFIX}/{site_name}/{relative}"
                self.s3.upload_file(
                    str(file_path),
                    self.bucket_name,
                    key,
                    ExtraArgs={"ContentType": _content_type(file_path)},
                )
                keys.append(key)
        except ClientError as e:
            raise AWSError(f"S3 upload failed: {e}", original=e) from e
        return keys

    def invalidate_cache(self, site_name: str) -> str:
        """Create a CloudFront invalidation for ``/sites/{site_name}/*``.

        Returns the invalidation ID.
        """
        import time

        try:
            resp = self.cf.create_invalidation(
                DistributionId=self.distribution_id,
                InvalidationBatch={
                    "Paths": {
                        "Quantity": 1,
                        "Items": [f"/{S3_PREFIX}/{site_name}/*"],
                    },
                    "CallerReference": str(int(time.time())),
                },
            )
        except ClientError as e:
            raise AWSError(f"CloudFront invalidation failed: {e}", original=e) from e
        return resp["Invalidation"]["Id"]

    def delete_site(self, site_name: str) -> int:
        """Delete all objects under ``sites/{site_name}/``.

        Returns the number of objects deleted.
        """
        prefix = f"{S3_PREFIX}/{site_name}/"
        deleted = 0
        try:
            paginator = self.s3.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
                objects = page.get("Contents", [])
                if not objects:
                    continue
                delete_req = {"Objects": [{"Key": obj["Key"]} for obj in objects]}
                self.s3.delete_objects(Bucket=self.bucket_name, Delete=delete_req)
                deleted += len(objects)
        except ClientError as e:
            raise AWSError(f"S3 delete failed: {e}", original=e) from e
        return deleted

    def list_sites(self) -> list[dict]:
        """List all sites, aggregated by prefix.

        Returns a list of dicts with keys: ``name``, ``file_count``, ``total_size``.
        """
        prefix = f"{S3_PREFIX}/"
        sites: dict[str, dict] = {}
        try:
            paginator = self.s3.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
                for obj in page.get("Contents", []):
                    key = obj["Key"]
                    # key looks like sites/my-site/index.html
                    parts = key.split("/", 2)
                    if len(parts) < 3:
                        continue
                    name = parts[1]
                    if name not in sites:
                        sites[name] = {"name": name, "file_count": 0, "total_size": 0}
                    sites[name]["file_count"] += 1
                    sites[name]["total_size"] += obj.get("Size", 0)
        except ClientError as e:
            raise AWSError(f"S3 list failed: {e}", original=e) from e
        return list(sites.values())

    def site_exists(self, site_name: str) -> bool:
        """Return *True* if at least one object exists under ``sites/{site_name}/``."""
        prefix = f"{S3_PREFIX}/{site_name}/"
        try:
            resp = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix, MaxKeys=1)
        except ClientError as e:
            raise AWSError(f"S3 check failed: {e}", original=e) from e
        return resp.get("KeyCount", 0) > 0
