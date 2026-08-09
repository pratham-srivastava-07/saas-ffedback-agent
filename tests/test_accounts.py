"""Email/password signup and login."""

from __future__ import annotations

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.auth import (
    generate_salt,
    hash_password,
    verify_password,
)
from app.api.ratelimit import RateLimiter
from app.main import app as fastapi_app


@pytest_asyncio.fixture
async def client(runtime, session_factory, settings):
    fastapi_app.state.runtime = runtime
    fastapi_app.state.session_factory = session_factory
    fastapi_app.state.settings = settings
    fastapi_app.state.rate_limiter = RateLimiter(
        capacity=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app), base_url="http://test"
    ) as async_client:
        yield async_client


CREDENTIALS = {"email": "pm@acme.com", "password": "correct-horse-battery"}


# --------------------------------------------------------------------------
# Password hashing
# --------------------------------------------------------------------------


def test_password_hash_is_salted_and_verifiable():
    salt = generate_salt()
    digest = hash_password("correct-horse-battery", salt)

    assert verify_password("correct-horse-battery", salt, digest)
    assert not verify_password("wrong-password", salt, digest)
    # The password itself never appears in the stored value.
    assert "correct-horse-battery" not in digest


def test_same_password_hashes_differently_under_different_salts():
    """Without a per-user salt, identical passwords share a digest and one
    rainbow table breaks every account at once."""
    first = generate_salt()
    second = generate_salt()

    assert first != second
    assert hash_password("same-password", first) != hash_password(
        "same-password", second
    )


def test_verify_rejects_a_malformed_salt_instead_of_raising():
    assert verify_password("password", "not-hex", "deadbeef") is False


# --------------------------------------------------------------------------
# Signup
# --------------------------------------------------------------------------


async def test_signup_creates_user_workspace_and_key(client):
    response = await client.post("/auth/signup", json=CREDENTIALS)

    assert response.status_code == 201
    body = response.json()

    assert body["email"] == "pm@acme.com"
    assert body["api_key"].startswith("sk_")
    assert body["workspace"]["id"]
    assert body["workspace"]["name"]


async def test_signup_accepts_a_workspace_name(client):
    response = await client.post(
        "/auth/signup", json={**CREDENTIALS, "workspace_name": "Acme Product"}
    )
    assert response.json()["workspace"]["name"] == "Acme Product"


async def test_the_returned_key_works_immediately(client, feedback_batch):
    api_key = (await client.post("/auth/signup", json=CREDENTIALS)).json()["api_key"]

    response = await client.post(
        "/analyze",
        json={"raw_feedback": feedback_batch},
        headers={"X-API-Key": api_key},
    )
    assert response.status_code == 200


async def test_duplicate_email_is_409(client):
    await client.post("/auth/signup", json=CREDENTIALS)
    response = await client.post("/auth/signup", json=CREDENTIALS)

    assert response.status_code == 409


async def test_email_is_normalised_so_case_cannot_duplicate_an_account(client):
    await client.post("/auth/signup", json=CREDENTIALS)
    response = await client.post(
        "/auth/signup", json={**CREDENTIALS, "email": "PM@Acme.COM"}
    )

    assert response.status_code == 409


async def test_short_password_is_422_and_says_the_rule(client):
    response = await client.post(
        "/auth/signup", json={"email": "x@acme.com", "password": "short"}
    )

    assert response.status_code == 422
    assert "8" in str(response.json()["detail"])


async def test_invalid_email_is_422(client):
    response = await client.post(
        "/auth/signup", json={"email": "not-an-email", "password": "long-enough-pw"}
    )
    assert response.status_code == 422


async def test_signup_workspace_is_isolated_from_other_accounts(
    client, feedback_batch
):
    """Two signups must not see each other's themes."""
    first = (await client.post("/auth/signup", json=CREDENTIALS)).json()
    second = (
        await client.post(
            "/auth/signup",
            json={"email": "other@acme.com", "password": "another-long-password"},
        )
    ).json()

    await client.post(
        "/analyze",
        json={"raw_feedback": feedback_batch},
        headers={"X-API-Key": first["api_key"]},
    )

    themes = await client.get(
        "/themes", headers={"X-API-Key": second["api_key"]}
    )
    assert themes.json() == []


# --------------------------------------------------------------------------
# Login
# --------------------------------------------------------------------------


async def test_login_returns_a_working_key(client):
    await client.post("/auth/signup", json=CREDENTIALS)

    response = await client.post("/auth/login", json=CREDENTIALS)
    assert response.status_code == 200

    api_key = response.json()["api_key"]
    me = await client.get("/auth/me", headers={"X-API-Key": api_key})
    assert me.status_code == 200
    assert me.json()["email"] == "pm@acme.com"


async def test_login_keeps_the_same_workspace(client):
    signed_up = (await client.post("/auth/signup", json=CREDENTIALS)).json()
    logged_in = (await client.post("/auth/login", json=CREDENTIALS)).json()

    assert logged_in["workspace"]["id"] == signed_up["workspace"]["id"]


async def test_login_rotates_the_key_and_retires_the_old_one(client):
    """Only the hash is stored, so the previous key cannot be handed back —
    logging in necessarily issues a fresh one and invalidates the old."""
    old_key = (await client.post("/auth/signup", json=CREDENTIALS)).json()["api_key"]
    new_key = (await client.post("/auth/login", json=CREDENTIALS)).json()["api_key"]

    assert new_key != old_key
    assert (await client.get("/auth/me", headers={"X-API-Key": new_key})).status_code == 200
    assert (await client.get("/auth/me", headers={"X-API-Key": old_key})).status_code == 401


async def test_wrong_password_is_401(client):
    await client.post("/auth/signup", json=CREDENTIALS)

    response = await client.post(
        "/auth/login", json={**CREDENTIALS, "password": "wrong-password-here"}
    )
    assert response.status_code == 401


async def test_unknown_email_and_wrong_password_are_indistinguishable(client):
    """Different responses would turn login into an account enumerator."""
    await client.post("/auth/signup", json=CREDENTIALS)

    unknown = await client.post(
        "/auth/login",
        json={"email": "nobody@acme.com", "password": "correct-horse-battery"},
    )
    wrong = await client.post(
        "/auth/login", json={**CREDENTIALS, "password": "wrong-password-here"}
    )

    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json() == wrong.json()


# --------------------------------------------------------------------------
# /auth/me
# --------------------------------------------------------------------------


async def test_me_requires_a_valid_key(client):
    assert (await client.get("/auth/me")).status_code == 401
    assert (
        await client.get("/auth/me", headers={"X-API-Key": "sk_nope"})
    ).status_code == 401


async def test_me_reports_null_email_for_a_cli_created_workspace(
    client, workspace
):
    """Workspaces from scripts/create_workspace.py have a key but no user."""
    response = await client.get(
        "/auth/me", headers={"X-API-Key": workspace.api_key}
    )

    assert response.status_code == 200
    assert response.json()["email"] is None
    assert response.json()["workspace"]["id"] == workspace.id
