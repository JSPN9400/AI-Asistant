import base64
import hashlib
import hmac
import json
import time
from hashlib import sha256

from fastapi import HTTPException

from app.config import settings


def hash_text(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def create_access_token(payload: dict[str, str], expires_in_seconds: int = 60 * 60 * 12) -> str:
    body = {
        **payload,
        "exp": int(time.time()) + expires_in_seconds,
    }
    encoded_payload = _b64encode(json.dumps(body, separators=(",", ":")).encode("utf-8"))
    signature = _sign(encoded_payload)
    return f"{encoded_payload}.{signature}"


def verify_access_token(token: str) -> dict[str, str]:
    try:
        encoded_payload, provided_signature = token.split(".", 1)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid token format") from exc

    expected_signature = _sign(encoded_payload)
    if not hmac.compare_digest(provided_signature, expected_signature):
        raise HTTPException(status_code=401, detail="Invalid token signature")

    try:
        payload = json.loads(_b64decode(encoded_payload).decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid token payload") from exc

    if int(payload.get("exp", 0)) < int(time.time()):
        raise HTTPException(status_code=401, detail="Token expired")

    return payload


def _sign(value: str) -> str:
    digest = hmac.new(
        settings.jwt_secret.encode("utf-8"),
        value.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return _b64encode(digest)


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("utf-8").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)
