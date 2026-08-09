"""Email/password signup and login.

Deliberately thin. Login returns the workspace's **API key** rather than
minting a session token, so the key auth the rest of the API already uses
stays the single source of truth and there is no second credential system to
keep in sync.

The trade: the frontend holds no server session, so the key is returned on
every login and the client stores it. That means the key is only as safe as
the client's storage, and revoking it means rotating the workspace key.
Acceptable for a single-tenant-per-user product; a multi-device or
token-revocation story would need real sessions.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.exc import IntegrityError

from app.api.auth import (
    MIN_PASSWORD_LENGTH,
    PASSWORD_RULES,
    generate_api_key,
    generate_salt,
    hash_api_key,
    hash_password,
    verify_password,
    waste_time_like_a_password_check,
    workspace_dep,
)
from app.api.deps import session_factory_dep
from app.store import repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# Identical for an unknown email and a wrong password: telling them apart
# turns this endpoint into an account enumerator.
_BAD_CREDENTIALS = "Incorrect email or password."


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=MIN_PASSWORD_LENGTH)
    workspace_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class WorkspaceOut(BaseModel):
    id: str
    name: str


class AuthResponse(BaseModel):
    api_key: str
    email: str
    workspace: WorkspaceOut


class MeResponse(BaseModel):
    email: str | None
    workspace: WorkspaceOut


@router.post("/signup", response_model=AuthResponse, status_code=201)
async def signup(payload: SignupRequest, session_factory=Depends(session_factory_dep)):
    """Create a user, their workspace and its API key in one transaction."""
    email = payload.email.strip().lower()

    if len(payload.password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(status_code=422, detail=PASSWORD_RULES)

    api_key = generate_api_key()
    salt = generate_salt()

    async with session_factory() as session:
        if await repo.get_user_by_email(session, email) is not None:
            raise HTTPException(
                status_code=409, detail="That email is already registered."
            )

        try:
            user, workspace = await repo.create_user_with_workspace(
                session,
                email=email,
                password_hash=hash_password(payload.password, salt),
                salt=salt,
                workspace_name=payload.workspace_name or f"{email}'s workspace",
                api_key_hash=hash_api_key(api_key),
            )
        except IntegrityError:
            # Lost a race against a concurrent signup for the same email.
            await session.rollback()
            raise HTTPException(
                status_code=409, detail="That email is already registered."
            ) from None

    return AuthResponse(
        api_key=api_key,
        email=user.email,
        workspace=WorkspaceOut(id=workspace.id, name=workspace.name),
    )


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest, session_factory=Depends(session_factory_dep)):
    """Verify the password and hand back the workspace's API key.

    The key is re-issued rather than retrieved: only its hash is stored, so
    logging in rotates it. Any other client holding the old key is logged out.
    """
    email = payload.email.strip().lower()

    async with session_factory() as session:
        user = await repo.get_user_by_email(session, email)

        if user is None:
            # Spend the same time a real verification would.
            waste_time_like_a_password_check()
            raise HTTPException(status_code=401, detail=_BAD_CREDENTIALS)

        if not verify_password(payload.password, user.salt, user.password_hash):
            raise HTTPException(status_code=401, detail=_BAD_CREDENTIALS)

        workspace = await repo.get_workspace(session, user.workspace_id)
        if workspace is None:
            logger.error("User %s has no workspace", user.id)
            raise HTTPException(status_code=500, detail="Account is misconfigured.")

        api_key = generate_api_key()
        workspace.api_key_hash = hash_api_key(api_key)
        session.add(workspace)
        await session.commit()

        return AuthResponse(
            api_key=api_key,
            email=user.email,
            workspace=WorkspaceOut(id=workspace.id, name=workspace.name),
        )


@router.get("/me", response_model=MeResponse)
async def me(
    request: Request,
    session_factory=Depends(session_factory_dep),
    workspace_id: str = Depends(workspace_dep),
):
    """Who the current API key belongs to.

    ``email`` is null for workspaces created by ``scripts/create_workspace.py``,
    which have a key but no user attached.
    """
    async with session_factory() as session:
        workspace = await repo.get_workspace(session, workspace_id)
        if workspace is None:
            raise HTTPException(status_code=401, detail="Unknown workspace.")
        user = await repo.get_user_for_workspace(session, workspace_id)

    return MeResponse(
        email=user.email if user else None,
        workspace=WorkspaceOut(id=workspace.id, name=workspace.name),
    )
