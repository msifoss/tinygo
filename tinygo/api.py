"""API client for the tiiny.host external API."""

import json
import secrets
import string
from pathlib import Path

import requests

BASE_URL = "https://ext.tiiny.host"
DEFAULT_SUFFIX = ".tiiny.site"


def _normalize_domain(domain: str) -> str:
    """Ensure domain has the .tiiny.site suffix."""
    if not domain.endswith(DEFAULT_SUFFIX):
        return domain + DEFAULT_SUFFIX
    return domain


_PASSWORD_ALPHABET = string.ascii_letters + string.digits + string.punctuation


def generate_password(length: int = 15) -> str:
    """Generate a cryptographically strong random password."""
    return "".join(secrets.choice(_PASSWORD_ALPHABET) for _ in range(length))


class TiinyError(Exception):
    """Raised when the tiiny.host API returns an error."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")


class TiinyClient:
    """Wrapper around the tiiny.host external API."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers["x-api-key"] = api_key

    def _raise_for_error(self, resp: requests.Response) -> None:
        if not resp.ok:
            try:
                detail = resp.json().get("message", resp.text)
            except (ValueError, KeyError):
                detail = resp.text
            raise TiinyError(resp.status_code, detail)

    def create(
        self,
        file_path: str,
        domain: str | None = None,
        password: str | None = None,
    ) -> tuple[dict, str]:
        """Create a new site via POST /v1/upload.

        Returns a tuple of (response_dict, password_used).
        """
        path = Path(file_path)
        password_used = password or generate_password()
        site_settings: dict = {
            "passwordProtected": True,
            "password": password_used,
            "noIndex": True,
        }

        with open(path, "rb") as f:
            files = {"files": (path.name, f)}
            data: dict = {"siteSettings": json.dumps(site_settings)}
            if domain:
                data["domain"] = _normalize_domain(domain)
            resp = self.session.post(f"{BASE_URL}/v1/upload", files=files, data=data)

        self._raise_for_error(resp)
        return resp.json(), password_used

    def update(
        self,
        file_path: str,
        domain: str,
        password: str | None = None,
    ) -> tuple[dict, str]:
        """Update an existing site via PUT /v1/upload.

        Returns a tuple of (response_dict, password_used).
        """
        path = Path(file_path)
        password_used = password or generate_password()
        site_settings: dict = {
            "passwordProtected": True,
            "password": password_used,
            "noIndex": True,
        }

        with open(path, "rb") as f:
            files = {"files": (path.name, f)}
            data: dict = {
                "domain": _normalize_domain(domain),
                "siteSettings": json.dumps(site_settings),
            }
            resp = self.session.put(f"{BASE_URL}/v1/upload", files=files, data=data)

        self._raise_for_error(resp)
        return resp.json(), password_used

    def delete(self, domain: str) -> dict:
        """Delete a site via DELETE /v1/delete."""
        resp = self.session.delete(
            f"{BASE_URL}/v1/delete",
            files={"domain": (None, _normalize_domain(domain))},
        )
        self._raise_for_error(resp)
        return resp.json()

    def profile(self) -> dict:
        """Fetch account profile via GET /v1/profile."""
        resp = self.session.get(f"{BASE_URL}/v1/profile")
        self._raise_for_error(resp)
        return resp.json()
