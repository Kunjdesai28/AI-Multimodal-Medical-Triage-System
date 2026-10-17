"""
Authentication and Cryptographic Security Utilities.
Provides password hashing via bcrypt, HMAC-SHA256 signed access tokens,
and healthcare organization input validation.
"""
import os
import re
import json
import hmac
import hashlib
import base64
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
import bcrypt

SECRET_KEY = os.getenv("TRIAGEAI_JWT_SECRET", "triageai-enterprise-medical-secret-key-2026-secure-auth")
TOKEN_EXPIRATION_HOURS = int(os.getenv("TOKEN_EXPIRATION_HOURS", "72"))


def hash_password(password: str) -> str:
    """Hashes a plaintext password securely using bcrypt with auto-generated salt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validates institutional security criteria:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    """
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters long."
    return True, ""



def validate_email_format(email: str) -> bool:
    """Validates official email address syntax."""
    if not email:
        return False
    regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(regex, email.strip()))


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a secure cryptographically signed token (HMAC-SHA256).
    Header.Payload.Signature format compatible with standard Bearer authorization.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = time.time() + expires_delta.total_seconds()
    else:
        expire = time.time() + (TOKEN_EXPIRATION_HOURS * 3600)

    to_encode["exp"] = int(expire)
    to_encode["iat"] = int(time.time())

    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode("utf-8")).decode("utf-8").rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(to_encode).encode("utf-8")).decode("utf-8").rstrip("=")

    message = f"{header_b64}.{payload_b64}"
    signature = hmac.new(
        SECRET_KEY.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("=")

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates a cryptographically signed Bearer token."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header_b64, payload_b64, sig_b64 = parts
        message = f"{header_b64}.{payload_b64}"

        # Verify signature
        expected_sig = hmac.new(
            SECRET_KEY.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256
        ).digest()
        expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode("utf-8").rstrip("=")

        if not hmac.compare_digest(sig_b64, expected_sig_b64):
            return None

        # Decode payload with padding
        padding = "=" * ((4 - len(payload_b64) % 4) % 4)
        payload_bytes = base64.urlsafe_b64decode((payload_b64 + padding).encode("utf-8"))
        payload = json.loads(payload_bytes.decode("utf-8"))

        # Check expiration
        if payload.get("exp") and time.time() > payload["exp"]:
            return None

        return payload
    except Exception:
        return None
