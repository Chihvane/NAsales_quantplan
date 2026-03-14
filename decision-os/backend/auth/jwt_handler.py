from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os


SECRET_KEY = os.getenv("JWT_SECRET", "change-me").encode("utf-8")


def create_token(payload: dict) -> str:
    body = json.dumps(payload, sort_keys=True).encode("utf-8")
    signature = hmac.new(SECRET_KEY, body, hashlib.sha256).hexdigest()
    return f"{base64.urlsafe_b64encode(body).decode('utf-8')}.{signature}"


def verify_token(token: str) -> dict:
    encoded, signature = token.split(".", 1)
    body = base64.urlsafe_b64decode(encoded.encode("utf-8"))
    expected = hmac.new(SECRET_KEY, body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise ValueError("Invalid token signature")
    return json.loads(body.decode("utf-8"))


def build_claims(user_id: str, role: str, tenant_id: str, exp: int) -> dict:
    return {
        "user_id": user_id,
        "role": role,
        "tenant_id": tenant_id,
        "exp": exp,
    }
