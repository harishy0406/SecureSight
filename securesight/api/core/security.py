from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
import jwt

from securesight.api.core.config import Settings, get_settings
from securesight.api.core.logging import new_request_id


__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "create_token_pair",
    "decode_token",
    "decode_access_token",
    "decode_refresh_token",
    "generate_api_key",
    "hash_api_key",
    "verify_api_key",
    "generate_request_id",
    "generate_secure_token",
    "constant_time_compare",
    "new_request_id",
]


_RESERVED_CLAIMS = frozenset({"sub", "iat", "nbf", "exp", "iss", "aud", "jti", "type"})
_UNVERIFIED_OPTIONS = {
    "verify_signature": False,
    "verify_exp": False,
    "verify_nbf": False,
    "verify_iat": False,
    "verify_aud": False,
    "verify_iss": False,
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _signing_key(settings: Settings) -> str:
    if settings.effective_jwt_algorithm == "HS256":
        return settings.secret_key
    return settings.jwt_private_key


def _verifying_key(settings: Settings) -> str:
    if settings.effective_jwt_algorithm == "HS256":
        return settings.secret_key
    return settings.jwt_public_key


def _algorithms(settings: Settings) -> list[str]:
    return [settings.effective_jwt_algorithm]


def hash_password(plain: str) -> str:
    if not isinstance(plain, str) or not plain:
        raise ValueError("password must be a non-empty string")
    settings = get_settings()
    salt = bcrypt.gensalt(rounds=settings.bcrypt_rounds)
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    if not isinstance(plain, str) or not isinstance(hashed, str):
        return False
    if not plain or not hashed:
        return False
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def _build_claims(
    subject: str,
    token_type: str,
    expires_delta: timedelta,
    extra_claims: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    settings = get_settings()
    now = _utcnow()
    claims: dict[str, Any] = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "jti": uuid.uuid4().hex,
        "type": token_type,
    }
    if extra_claims:
        for key, value in extra_claims.items():
            if key in _RESERVED_CLAIMS:
                continue
            claims[key] = value
    return claims


def create_access_token(
    subject: str,
    *,
    extra_claims: Optional[dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    settings = get_settings()
    delta = expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes)
    claims = _build_claims(subject, "access", delta, extra_claims)
    return jwt.encode(claims, _signing_key(settings), algorithm=settings.effective_jwt_algorithm)


def create_refresh_token(
    subject: str,
    *,
    extra_claims: Optional[dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    settings = get_settings()
    delta = expires_delta or timedelta(days=settings.jwt_refresh_token_expire_days)
    claims = _build_claims(subject, "refresh", delta, extra_claims)
    return jwt.encode(claims, _signing_key(settings), algorithm=settings.effective_jwt_algorithm)


def create_token_pair(
    subject: str,
    *,
    extra_claims: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    settings = get_settings()
    access_token = create_access_token(subject, extra_claims=extra_claims)
    refresh_token = create_refresh_token(subject, extra_claims=extra_claims)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.jwt_access_token_expire_minutes * 60,
    }


def decode_token(
    token: str,
    *,
    expected_type: Optional[str] = "access",
    verify: bool = True,
) -> dict[str, Any]:
    if not isinstance(token, str) or not token:
        raise jwt.InvalidTokenError("token must be a non-empty string")
    settings = get_settings()
    if verify:
        claims = jwt.decode(
            token,
            _verifying_key(settings),
            algorithms=_algorithms(settings),
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
            options={"require": ["exp", "iat", "sub"]},
        )
    else:
        claims = jwt.decode(token, options=_UNVERIFIED_OPTIONS)
    if expected_type is not None:
        token_type = claims.get("type")
        if token_type != expected_type:
            raise jwt.InvalidTokenError(
                f"invalid token type: expected {expected_type!r}, got {token_type!r}"
            )
    return claims


def decode_access_token(token: str) -> dict[str, Any]:
    return decode_token(token, expected_type="access")


def decode_refresh_token(token: str) -> dict[str, Any]:
    return decode_token(token, expected_type="refresh")


def _api_key_prefix(settings: Settings) -> str:
    return "ss_live_" if settings.is_production else "ss_test_"


def generate_api_key(*, length: int = 32) -> str:
    settings = get_settings()
    body = secrets.token_urlsafe(length)
    return f"{_api_key_prefix(settings)}{body}"


def hash_api_key(raw: str) -> str:
    if not isinstance(raw, str) or not raw:
        raise ValueError("api key must be a non-empty string")
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def verify_api_key(raw: str, hashed: str) -> bool:
    if not isinstance(raw, str) or not isinstance(hashed, str):
        return False
    if not raw or not hashed:
        return False
    return constant_time_compare(hash_api_key(raw), hashed)


def generate_request_id() -> str:
    return uuid.uuid4().hex


def generate_secure_token(*, length: int = 32) -> str:
    return secrets.token_urlsafe(length)


def constant_time_compare(a: str, b: str) -> bool:
    if not isinstance(a, str) or not isinstance(b, str):
        return False
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))
