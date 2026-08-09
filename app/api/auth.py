"""API-key auth resolving a request to a workspace.

Only the SHA-256 of a key is ever stored. The key itself is printed once by
``scripts/create_workspace.py`` and is not recoverable, so a leaked database
does not hand over working credentials.

The keys are high-entropy random tokens, not user-chosen secrets, so a plain
unsalted hash is adequate here — there is nothing to brute-force. A password
would need bcrypt/argon2; this does not.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

from fastapi import Header, HTTPException, Request

from app.store import repo
from app.store.models import DEFAULT_WORKSPACE_ID

API_KEY_HEADER = "X-API-Key"

MIN_PASSWORD_LENGTH = 8
PASSWORD_RULES = (
    f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
)

# scrypt work factors. n=2**14 with r=8 costs roughly 16MB and ~50ms per
# hash, which is slow enough to matter to an attacker and fast enough that a
# login is not noticeable.
_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SCRYPT_DKLEN = 64


def generate_api_key() -> str:
    return f"sk_{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------
# Passwords
# --------------------------------------------------------------------------


def generate_salt() -> str:
    return secrets.token_hex(16)


def hash_password(password: str, salt: str) -> str:
    """scrypt from the standard library — no bcrypt/argon2 dependency.

    Unlike the API keys (high-entropy random tokens, where a plain SHA-256 is
    fine), passwords are user-chosen and low-entropy, so they need a slow
    salted KDF.
    """
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=bytes.fromhex(salt),
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_SCRYPT_DKLEN,
    )
    return digest.hex()


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    try:
        candidate = hash_password(password, salt)
    except ValueError:
        return False
    return hmac.compare_digest(candidate, expected_hash)


def waste_time_like_a_password_check() -> None:
    """Burn the same work as a real verification.

    Without this, an unknown email returns noticeably faster than a wrong
    password, which turns the login endpoint into an account enumerator.
    """
    hash_password("dummy-password", generate_salt())


async def workspace_dep(
    request: Request,
    x_api_key: str | None = Header(default=None, alias=API_KEY_HEADER),
) -> str:
    """Resolve the calling workspace, or refuse the request."""
    settings = request.app.state.settings
    session_factory = request.app.state.session_factory

    if not x_api_key:
        if settings.allow_anonymous_access:
            return DEFAULT_WORKSPACE_ID
        raise HTTPException(
            status_code=401,
            detail=(
                f"Missing {API_KEY_HEADER}. Create a workspace with "
                "`python scripts/create_workspace.py <name>`, or set "
                "ALLOW_ANONYMOUS_ACCESS=true for local single-user use."
            ),
        )

    async with session_factory() as session:
        workspace = await repo.workspace_by_key_hash(session, hash_api_key(x_api_key))

    if workspace is None:
        raise HTTPException(status_code=401, detail="Invalid API key.")

    return workspace.id
