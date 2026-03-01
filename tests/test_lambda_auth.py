"""Tests for infra/lambda_edge/auth.py — Lambda@Edge JWT + cookie auth."""

import base64
import json
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add the lambda_edge directory to sys.path so we can import auth
LAMBDA_DIR = Path(__file__).parent.parent / "infra" / "lambda_edge"
sys.path.insert(0, str(LAMBDA_DIR))

import auth  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_globals():
    """Reset module-level caches between tests."""
    auth._CONFIG = None
    auth._JWKS_CACHE = None
    yield
    auth._CONFIG = None
    auth._JWKS_CACHE = None


SAMPLE_CONFIG = {
    "region": "us-east-1",
    "user_pool_id": "us-east-1_TestPool",
    "client_id": "test-client-id",
    "client_secret": "test-client-secret",
    "cognito_domain": "https://myapp.auth.us-east-1.amazoncognito.com",
    "callback_url": "https://d111.cloudfront.net/_auth/callback",
    "cloudfront_domain": "d111.cloudfront.net",
}


def _make_event(uri="/", headers=None, querystring=""):
    """Build a minimal CloudFront viewer-request event."""
    return {
        "Records": [{
            "cf": {
                "request": {
                    "uri": uri,
                    "headers": headers or {},
                    "querystring": querystring,
                }
            }
        }]
    }


def _base64url_encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _make_jwt(payload_overrides=None, kid="test-kid"):
    """Build a fake JWT (not cryptographically valid) for testing."""
    header = {"alg": "RS256", "kid": kid}
    payload = {
        "sub": "user-123",
        "iss": f"https://cognito-idp.us-east-1.amazonaws.com/us-east-1_TestPool",
        "aud": "test-client-id",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
    }
    if payload_overrides:
        payload.update(payload_overrides)
    h = _base64url_encode(json.dumps(header).encode())
    p = _base64url_encode(json.dumps(payload).encode())
    s = _base64url_encode(b"fake-signature")
    return f"{h}.{p}.{s}"


# ── Config loading ────────────────────────────────────────────────────────


def test_handler_returns_401_when_config_missing():
    """Handler returns 401 when config.json is not found."""
    with patch.object(auth, "_load_config", side_effect=FileNotFoundError):
        result = auth.handler(_make_event(), None)
    assert result["status"] == "401"
    assert "configuration missing" in result["body"]


def test_handler_returns_401_when_config_incomplete():
    """Handler returns 401 when config is missing required fields."""
    incomplete = {"region": "us-east-1"}
    with patch.object(auth, "_load_config", return_value=incomplete):
        result = auth.handler(_make_event(), None)
    assert result["status"] == "401"
    assert "incomplete" in result["body"]


# ── Bearer token auth ────────────────────────────────────────────────────


def test_bearer_token_valid():
    """Valid Bearer token forwards the request."""
    token = _make_jwt()
    headers = {"authorization": [{"value": f"Bearer {token}"}]}
    event = _make_event(headers=headers)

    with patch.object(auth, "_load_config", return_value=SAMPLE_CONFIG), \
         patch.object(auth, "_validate_jwt", return_value=({"alg": "RS256"}, {"sub": "u"})):
        result = auth.handler(event, None)

    # Should return the request object (forwarded to origin)
    assert "uri" in result
    assert result["uri"] == "/"


def test_bearer_token_invalid():
    """Invalid Bearer token returns 401."""
    headers = {"authorization": [{"value": "Bearer bad-token"}]}
    event = _make_event(headers=headers)

    with patch.object(auth, "_load_config", return_value=SAMPLE_CONFIG), \
         patch.object(auth, "_validate_jwt", return_value=None):
        result = auth.handler(event, None)

    assert result["status"] == "401"
    assert "Invalid token" in result["body"]


# ── Cookie-based auth ────────────────────────────────────────────────────


def test_cookie_auth_valid():
    """Valid cookie token forwards the request."""
    token = _make_jwt()
    headers = {"cookie": [{"value": f"tinygo_id_token={token}; other=val"}]}
    event = _make_event(headers=headers)

    with patch.object(auth, "_load_config", return_value=SAMPLE_CONFIG), \
         patch.object(auth, "_validate_jwt", return_value=({"alg": "RS256"}, {"sub": "u"})):
        result = auth.handler(event, None)

    assert "uri" in result


def test_cookie_auth_invalid_redirects_to_login():
    """Invalid/expired cookie token redirects to Cognito login."""
    headers = {"cookie": [{"value": "tinygo_id_token=expired-token"}]}
    event = _make_event(uri="/page.html", headers=headers)

    with patch.object(auth, "_load_config", return_value=SAMPLE_CONFIG), \
         patch.object(auth, "_validate_jwt", return_value=None):
        result = auth.handler(event, None)

    assert result["status"] == "302"
    location = result["headers"]["location"][0]["value"]
    assert "myapp.auth.us-east-1.amazoncognito.com/login" in location


# ── Login redirect ────────────────────────────────────────────────────────


def test_no_auth_redirects_to_login():
    """No auth header and no cookie redirects to Cognito Hosted UI."""
    event = _make_event(uri="/sites/mysite/index.html")

    with patch.object(auth, "_load_config", return_value=SAMPLE_CONFIG):
        result = auth.handler(event, None)

    assert result["status"] == "302"
    location = result["headers"]["location"][0]["value"]
    assert "myapp.auth.us-east-1.amazoncognito.com/login" in location
    assert "response_type=code" in location
    assert "client_id=test-client-id" in location
    assert "state=" in location


def test_login_redirect_state_encodes_original_uri():
    """State parameter in login redirect contains the original URI."""
    event = _make_event(uri="/sites/mysite/page.html")

    with patch.object(auth, "_load_config", return_value=SAMPLE_CONFIG):
        result = auth.handler(event, None)

    location = result["headers"]["location"][0]["value"]
    # Extract state param
    import urllib.parse
    parsed = urllib.parse.urlparse(location)
    params = urllib.parse.parse_qs(parsed.query)
    state = params["state"][0]

    # Decode state
    decoded = auth._base64url_decode(state).decode("utf-8")
    assert decoded == "/sites/mysite/page.html"


# ── Callback handler ─────────────────────────────────────────────────────


def test_callback_missing_code_returns_401():
    """Callback without authorization code returns 401."""
    event = _make_event(uri="/_auth/callback", querystring="state=abc")

    with patch.object(auth, "_load_config", return_value=SAMPLE_CONFIG):
        result = auth.handler(event, None)

    assert result["status"] == "401"
    assert "Missing authorization code" in result["body"]


def test_callback_exchange_failure_returns_401():
    """Callback returns 401 when token exchange fails."""
    event = _make_event(
        uri="/_auth/callback",
        querystring="code=auth-code-123&state=abc",
    )

    with patch.object(auth, "_load_config", return_value=SAMPLE_CONFIG), \
         patch.object(auth, "_exchange_code_for_tokens", return_value=None):
        result = auth.handler(event, None)

    assert result["status"] == "401"
    assert "Token exchange failed" in result["body"]


def test_callback_success_sets_cookies_and_redirects():
    """Successful callback sets cookie and redirects to original URI."""
    original_uri = "/sites/mysite/index.html"
    state = _base64url_encode(original_uri.encode("utf-8"))
    event = _make_event(
        uri="/_auth/callback",
        querystring=f"code=auth-code-123&state={state}",
    )

    token_response = {
        "id_token": "id-token-value",
        "access_token": "access-token-value",
        "refresh_token": "refresh-token-value",
        "expires_in": 3600,
    }

    with patch.object(auth, "_load_config", return_value=SAMPLE_CONFIG), \
         patch.object(auth, "_exchange_code_for_tokens", return_value=token_response):
        result = auth.handler(event, None)

    assert result["status"] == "302"

    # Check redirect location
    location = result["headers"]["location"][0]["value"]
    assert location == f"https://d111.cloudfront.net{original_uri}"

    # Check cookies
    cookie_values = [c["value"] for c in result["headers"]["set-cookie"]]
    assert any("tinygo_id_token=id-token-value" in c for c in cookie_values)
    assert any("tinygo_access_token=access-token-value" in c for c in cookie_values)
    assert any("tinygo_refresh_token=refresh-token-value" in c for c in cookie_values)

    # Check cookie attributes
    id_cookie = [c for c in cookie_values if "tinygo_id_token" in c][0]
    assert "Secure" in id_cookie
    assert "HttpOnly" in id_cookie
    assert "SameSite=Lax" in id_cookie
    assert "Max-Age=3600" in id_cookie


def test_callback_no_state_redirects_to_root():
    """Callback without state param redirects to /."""
    event = _make_event(
        uri="/_auth/callback",
        querystring="code=auth-code-123",
    )

    token_response = {
        "id_token": "id-token-value",
        "access_token": "access-token-value",
        "expires_in": 3600,
    }

    with patch.object(auth, "_load_config", return_value=SAMPLE_CONFIG), \
         patch.object(auth, "_exchange_code_for_tokens", return_value=token_response):
        result = auth.handler(event, None)

    assert result["status"] == "302"
    location = result["headers"]["location"][0]["value"]
    assert location == "https://d111.cloudfront.net/"


# ── Helper functions ──────────────────────────────────────────────────────


def test_parse_cookies():
    """_parse_cookies correctly parses multiple cookies."""
    headers = {"cookie": [{"value": "a=1; b=2; c=3"}]}
    cookies = auth._parse_cookies(headers)
    assert cookies == {"a": "1", "b": "2", "c": "3"}


def test_parse_cookies_empty():
    """_parse_cookies returns empty dict for no cookies."""
    assert auth._parse_cookies({}) == {}


def test_validate_jwt_claims_expired():
    """_validate_jwt_claims rejects expired tokens."""
    payload = {
        "exp": int(time.time()) - 100,
        "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_TestPool",
        "aud": "test-client-id",
    }
    assert auth._validate_jwt_claims(payload, SAMPLE_CONFIG) is False


def test_validate_jwt_claims_wrong_issuer():
    """_validate_jwt_claims rejects tokens with wrong issuer."""
    payload = {
        "exp": int(time.time()) + 3600,
        "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_WrongPool",
        "aud": "test-client-id",
    }
    assert auth._validate_jwt_claims(payload, SAMPLE_CONFIG) is False


def test_validate_jwt_claims_wrong_client():
    """_validate_jwt_claims rejects tokens with wrong client_id."""
    payload = {
        "exp": int(time.time()) + 3600,
        "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_TestPool",
        "aud": "wrong-client-id",
    }
    assert auth._validate_jwt_claims(payload, SAMPLE_CONFIG) is False


def test_validate_jwt_claims_valid():
    """_validate_jwt_claims accepts valid claims."""
    payload = {
        "exp": int(time.time()) + 3600,
        "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_TestPool",
        "aud": "test-client-id",
    }
    assert auth._validate_jwt_claims(payload, SAMPLE_CONFIG) is True
