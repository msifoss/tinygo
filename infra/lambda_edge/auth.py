"""Lambda@Edge viewer-request handler — validates Cognito JWT tokens.

Supports two auth flows:
1. Bearer token (CLI/API clients) — Authorization: Bearer <token>
2. Cookie-based (browser) — tinygo_id_token cookie set after Cognito Hosted UI login

Unauthenticated browser requests are redirected to the Cognito Hosted UI.
The /_auth/callback path handles the OAuth2 authorization code exchange.
"""

import base64
import hashlib
import hmac
import json
import os
import re
import struct
import time
import urllib.parse
import urllib.request
from pathlib import Path

# Config is baked into the deployment package during sam build.
_CONFIG_PATH = Path(__file__).parent / "config.json"
_CONFIG = None
_JWKS_CACHE = None
_JWKS_CACHE_TIME = 0
_JWKS_TTL = 3600  # Re-fetch JWKS after 1 hour


def _load_config():
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = json.loads(_CONFIG_PATH.read_text())
    return _CONFIG


def _get_jwks(region, user_pool_id):
    """Fetch and cache the Cognito JWKS (refreshed after TTL expires)."""
    global _JWKS_CACHE, _JWKS_CACHE_TIME
    if _JWKS_CACHE is not None and (time.time() - _JWKS_CACHE_TIME) < _JWKS_TTL:
        return _JWKS_CACHE
    url = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"
    with urllib.request.urlopen(url, timeout=3) as resp:
        _JWKS_CACHE = json.loads(resp.read())
    _JWKS_CACHE_TIME = time.time()
    return _JWKS_CACHE


def _base64url_decode(s):
    """Decode a base64url-encoded string."""
    s = s.replace("-", "+").replace("_", "/")
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.b64decode(s)


def _base64url_encode(data):
    """Encode bytes to a base64url string (no padding)."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _decode_jwt_unverified(token):
    """Decode JWT header and payload without signature verification."""
    parts = token.split(".")
    if len(parts) != 3:
        return None, None
    try:
        header = json.loads(_base64url_decode(parts[0]))
        payload = json.loads(_base64url_decode(parts[1]))
    except Exception:
        return None, None
    return header, payload


def _int_from_bytes(b):
    """Convert big-endian bytes to integer."""
    result = 0
    for byte in b:
        result = (result << 8) | byte
    return result


def _verify_rs256(token, jwks):
    """Verify RS256 JWT signature against JWKS keys.

    Uses stdlib only (no cryptography library) — suitable for Lambda@Edge.
    Performs modular exponentiation to verify PKCS#1 v1.5 signature.
    """
    parts = token.split(".")
    if len(parts) != 3:
        return False

    header = json.loads(_base64url_decode(parts[0]))
    kid = header.get("kid")
    if not kid:
        return False

    # Find matching key
    key_data = None
    for key in jwks.get("keys", []):
        if key.get("kid") == kid and key.get("alg") == "RS256":
            key_data = key
            break
    if key_data is None:
        return False

    # Decode RSA public key components
    n = _int_from_bytes(_base64url_decode(key_data["n"]))
    e = _int_from_bytes(_base64url_decode(key_data["e"]))

    # Decode signature
    signature = _int_from_bytes(_base64url_decode(parts[2]))

    # RSA verify: signature^e mod n
    signed_message = parts[0] + "." + parts[1]
    message_hash = hashlib.sha256(signed_message.encode("ascii")).digest()

    # Perform modular exponentiation
    decrypted = pow(signature, e, n)

    # Convert back to bytes (key length)
    key_len = (n.bit_length() + 7) // 8
    decrypted_bytes = decrypted.to_bytes(key_len, byteorder="big")

    # PKCS#1 v1.5 padding: 0x00 0x01 [0xff padding] 0x00 [DigestInfo + hash]
    # SHA-256 DigestInfo prefix
    digest_info_prefix = bytes([
        0x30, 0x31, 0x30, 0x0d, 0x06, 0x09, 0x60, 0x86,
        0x48, 0x01, 0x65, 0x03, 0x04, 0x02, 0x01, 0x05,
        0x00, 0x04, 0x20
    ])
    expected_suffix = digest_info_prefix + message_hash

    # Check padding structure
    if decrypted_bytes[0] != 0x00 or decrypted_bytes[1] != 0x01:
        return False
    if not decrypted_bytes.endswith(expected_suffix):
        return False

    # Check that padding bytes between 0x01 and 0x00 separator are all 0xff
    separator_idx = decrypted_bytes.index(0x00, 2)
    padding_bytes = decrypted_bytes[2:separator_idx]
    if not all(b == 0xff for b in padding_bytes):
        return False

    return True


def _unauthorized(message="Unauthorized"):
    """Return a 401 response."""
    return {
        "status": "401",
        "statusDescription": "Unauthorized",
        "headers": {
            "content-type": [{"key": "Content-Type", "value": "text/plain"}],
            "www-authenticate": [{"key": "WWW-Authenticate", "value": "Bearer"}],
        },
        "body": message,
    }


def _redirect(location, cookies=None):
    """Return a 302 redirect response, optionally setting cookies."""
    headers = {
        "location": [{"key": "Location", "value": location}],
        "cache-control": [{"key": "Cache-Control", "value": "no-cache, no-store"}],
    }
    if cookies:
        headers["set-cookie"] = [
            {"key": "Set-Cookie", "value": c} for c in cookies
        ]
    return {
        "status": "302",
        "statusDescription": "Found",
        "headers": headers,
        "body": "",
    }


def _parse_cookies(headers):
    """Extract cookies from CloudFront request headers into a dict."""
    cookies = {}
    for cookie_header in headers.get("cookie", []):
        for part in cookie_header.get("value", "").split(";"):
            part = part.strip()
            if "=" in part:
                name, _, value = part.partition("=")
                cookies[name.strip()] = value.strip()
    return cookies


def _validate_jwt(token, config):
    """Validate a JWT token against config. Returns (header, payload) or None."""
    header, payload = _decode_jwt_unverified(token)
    if header is None or payload is None:
        return None

    if not _validate_jwt_claims(payload, config):
        return None

    region = config.get("region", "us-east-1")
    user_pool_id = config.get("user_pool_id")

    # Verify kid is in JWKS and signature is valid
    try:
        jwks = _get_jwks(region, user_pool_id)
    except Exception:
        return None

    kid = header.get("kid")
    jwks_kids = [k.get("kid") for k in jwks.get("keys", [])]
    if kid not in jwks_kids:
        return None

    if not _verify_rs256(token, jwks):
        return None

    return header, payload


def _validate_jwt_claims(payload, config):
    """Validate JWT claims (expiry, issuer, client_id). Returns True if valid."""
    region = config.get("region", "us-east-1")
    user_pool_id = config.get("user_pool_id")
    client_id = config.get("client_id")

    if not user_pool_id or not client_id:
        return False

    # Check expiry
    exp = payload.get("exp")
    if exp is None or time.time() > exp:
        return False

    # Check issuer
    expected_issuer = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"
    if payload.get("iss") != expected_issuer:
        return False

    # Check client_id (in 'aud' or 'client_id' claim depending on token type)
    token_client = payload.get("aud") or payload.get("client_id")
    if token_client != client_id:
        return False

    return True


def _build_state(config, request_uri):
    """Build a signed state parameter containing a CSRF nonce and the original URI.

    Format: base64url(JSON({"nonce": ..., "uri": ..., "sig": ...}))
    The sig is HMAC-SHA256(nonce + uri, client_secret).
    """
    client_secret = config.get("client_secret", "")
    nonce = _base64url_encode(os.urandom(16))
    message = f"{nonce}:{request_uri}".encode("utf-8")
    sig = hmac.new(client_secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
    payload = json.dumps({"nonce": nonce, "uri": request_uri, "sig": sig})
    return _base64url_encode(payload.encode("utf-8"))


def _verify_state(config, state):
    """Verify the signed state parameter. Returns the original URI or None."""
    client_secret = config.get("client_secret", "")
    try:
        payload = json.loads(_base64url_decode(state).decode("utf-8"))
    except Exception:
        return None
    nonce = payload.get("nonce", "")
    uri = payload.get("uri", "/")
    sig = payload.get("sig", "")
    message = f"{nonce}:{uri}".encode("utf-8")
    expected = hmac.new(client_secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return None
    return uri


def _build_login_url(config, request_uri):
    """Build the Cognito Hosted UI login URL with signed state parameter."""
    cognito_domain = config["cognito_domain"]
    client_id = config["client_id"]
    callback_url = config["callback_url"]

    state = _build_state(config, request_uri)

    params = urllib.parse.urlencode({
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": callback_url,
        "scope": "openid email profile",
        "state": state,
    })
    return f"{cognito_domain}/login?{params}"


def _exchange_code_for_tokens(code, config):
    """Exchange an authorization code for tokens via Cognito /oauth2/token.

    Returns the parsed JSON response or None on failure.
    """
    cognito_domain = config["cognito_domain"]
    client_id = config["client_id"]
    client_secret = config["client_secret"]
    callback_url = config["callback_url"]

    token_url = f"{cognito_domain}/oauth2/token"
    body = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": callback_url,
        "client_id": client_id,
    })

    # Basic auth header: base64(client_id:client_secret)
    credentials = base64.b64encode(
        f"{client_id}:{client_secret}".encode("utf-8")
    ).decode("ascii")

    req = urllib.request.Request(
        token_url,
        data=body.encode("utf-8"),
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {credentials}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())
    except Exception:
        return None


def _handle_callback(request, config):
    """Handle /_auth/callback — exchange code for tokens, set cookies, redirect."""
    query_string = request.get("querystring", "")
    params = urllib.parse.parse_qs(query_string)

    code = params.get("code", [None])[0]
    state = params.get("state", [None])[0]

    if not code:
        return _unauthorized("Missing authorization code")

    # Verify CSRF nonce in state before exchanging the code
    redirect_uri = "/"
    if state:
        verified_uri = _verify_state(config, state)
        if verified_uri is None:
            return _unauthorized("Invalid state parameter")
        redirect_uri = verified_uri
    else:
        return _unauthorized("Missing state parameter")

    tokens = _exchange_code_for_tokens(code, config)
    if not tokens:
        return _unauthorized("Token exchange failed")

    # Build Set-Cookie headers
    expires_in = tokens.get("expires_in", 3600)
    cookie_attrs = f"Path=/; Secure; HttpOnly; SameSite=Lax; Max-Age={expires_in}"
    cookies = []

    if tokens.get("id_token"):
        cookies.append(f"tinygo_id_token={tokens['id_token']}; {cookie_attrs}")
    if tokens.get("access_token"):
        cookies.append(f"tinygo_access_token={tokens['access_token']}; {cookie_attrs}")
    if tokens.get("refresh_token"):
        # Refresh tokens last longer
        refresh_attrs = f"Path=/; Secure; HttpOnly; SameSite=Lax; Max-Age=2592000"
        cookies.append(f"tinygo_refresh_token={tokens['refresh_token']}; {refresh_attrs}")

    cloudfront_domain = config.get("cloudfront_domain", "")
    redirect_location = f"https://{cloudfront_domain}{redirect_uri}"

    return _redirect(redirect_location, cookies=cookies)


def handler(event, context):
    """Validate JWT from Authorization header or cookie on viewer-request.

    Three cases:
    1. /_auth/callback — exchange authorization code for tokens
    2. Valid Bearer header OR valid cookie — forward request to origin
    3. No auth — redirect to Cognito Hosted UI login
    """
    request = event["Records"][0]["cf"]["request"]
    uri = request.get("uri", "/")
    headers = request.get("headers", {})

    try:
        config = _load_config()
    except FileNotFoundError:
        return _unauthorized("Auth configuration missing")

    region = config.get("region", "us-east-1")
    user_pool_id = config.get("user_pool_id")
    client_id = config.get("client_id")

    if not user_pool_id or not client_id:
        return _unauthorized("Auth configuration incomplete")

    # Case 1: /_auth/callback — handle OAuth2 callback
    if uri == "/_auth/callback":
        return _handle_callback(request, config)

    # Case 2a: Bearer token (CLI/API clients)
    auth_header = headers.get("authorization", [])
    if auth_header:
        auth_value = auth_header[0].get("value", "")
        match = re.match(r"^Bearer\s+(.+)$", auth_value, re.IGNORECASE)
        if match:
            token = match.group(1)
            result = _validate_jwt(token, config)
            if result is not None:
                return request
            return _unauthorized("Invalid token")

    # Case 2b: Cookie-based auth (browser)
    cookies = _parse_cookies(headers)
    id_token = cookies.get("tinygo_id_token")
    if id_token:
        result = _validate_jwt(id_token, config)
        if result is not None:
            return request
        # Cookie token is invalid/expired — fall through to redirect

    # Case 3: No valid auth — redirect to Cognito Hosted UI
    if "cognito_domain" not in config or "callback_url" not in config:
        return _unauthorized("Login not configured")

    login_url = _build_login_url(config, uri)
    return _redirect(login_url)
