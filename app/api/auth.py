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
import secrets

from fastapi import Depends, Header, HTTPException, Request

from app.store import repo
from app.store.models import DEFAULT_WORKSPACE_ID

API_KEY_HEADER = "X-API-Key"


def generate_api_key() -> str:
    return f"sk_{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


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
