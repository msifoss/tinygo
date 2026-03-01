"""Lambda@Edge viewer-request handler — validates Cognito JWT tokens."""

import base64
import hashlib
import hmac
import json
import re
import struct
import time
import urllib.request
from pathlib import Path

# Config is baked into the deployment package during sam build.
_CONFIG_PATH = Path(__file__).parent / "config.json"
_CONFIG = None
_JWKS_CACHE = None


def _load_config():
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = json.loads(_CONFIG_PATH.read_text())
    return _CONFIG


def _get_jwks(region, user_pool_id):
    """Fetch and cache the Cognito JWKS."""
    global _JWKS_CACHE
    if _JWKS_CACHE is not None:
        return _JWKS_CACHE
    url = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"
    with urllib.request.urlopen(url, timeout=3) as resp:
        _JWKS_CACHE = json.loads(resp.read())
    return _JWKS_CACHE


def _base64url_decode(s):
    """Decode a base64url-encoded string."""
    s = s.replace("-", "+").replace("_", "/")
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.b64decode(s)


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


def handler(event, context):
    """Validate JWT from Authorization header on viewer-request."""
    request = event["Records"][0]["cf"]["request"]

    # Extract token from Authorization header
    headers = request.get("headers", {})
    auth_header = headers.get("authorization", [])
    if not auth_header:
        return _unauthorized("Missing Authorization header")

    auth_value = auth_header[0].get("value", "")
    match = re.match(r"^Bearer\s+(.+)$", auth_value, re.IGNORECASE)
    if not match:
        return _unauthorized("Invalid Authorization header format")

    token = match.group(1)

    # Decode and validate
    header, payload = _decode_jwt_unverified(token)
    if header is None or payload is None:
        return _unauthorized("Invalid token format")

    try:
        config = _load_config()
    except FileNotFoundError:
        # Config not baked in — fail open in dev, fail closed in prod
        return _unauthorized("Auth configuration missing")

    region = config.get("region", "us-east-1")
    user_pool_id = config.get("user_pool_id")
    client_id = config.get("client_id")

    if not user_pool_id or not client_id:
        return _unauthorized("Auth configuration incomplete")

    # Check expiry
    exp = payload.get("exp")
    if exp is None or time.time() > exp:
        return _unauthorized("Token expired")

    # Check issuer
    expected_issuer = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"
    if payload.get("iss") != expected_issuer:
        return _unauthorized("Invalid token issuer")

    # Check client_id (in 'aud' or 'client_id' claim depending on token type)
    token_client = payload.get("aud") or payload.get("client_id")
    if token_client != client_id:
        return _unauthorized("Invalid client")

    # Verify kid is in JWKS
    try:
        jwks = _get_jwks(region, user_pool_id)
    except Exception:
        return _unauthorized("Could not fetch signing keys")

    kid = header.get("kid")
    jwks_kids = [k.get("kid") for k in jwks.get("keys", [])]
    if kid not in jwks_kids:
        return _unauthorized("Unknown signing key")

    # Verify signature
    if not _verify_rs256(token, jwks):
        return _unauthorized("Invalid token signature")

    # Token is valid — forward the request
    return request
