"""API-key auth and per-workspace rate limiting."""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.auth import generate_api_key, hash_api_key
from app.api.ratelimit import RateLimiter
from app.main import app as fastapi_app
from app.store.models import DEFAULT_WORKSPACE_ID


def _wire(runtime, session_factory, settings, capacity: int | None = None):
    fastapi_app.state.runtime = runtime
    fastapi_app.state.session_factory = session_factory
    fastapi_app.state.settings = settings
    fastapi_app.state.rate_limiter = RateLimiter(
        capacity=capacity if capacity is not None else settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )


@pytest_asyncio.fixture
async def anon_client(runtime, session_factory, settings):
    """A client with no key, against a server that permits anonymous use."""
    settings.allow_anonymous_access = True
    _wire(runtime, session_factory, settings)
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app), base_url="http://test"
    ) as client:
        yield client


@pytest_asyncio.fixture
async def strict_client(runtime, session_factory, settings):
    """A client with no key, against a server that requires one."""
    settings.allow_anonymous_access = False
    _wire(runtime, session_factory, settings)
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app), base_url="http://test"
    ) as client:
        yield client


def _payload(batch):
    return {"raw_feedback": batch}


# --------------------------------------------------------------------------
# Auth
# --------------------------------------------------------------------------


async def test_analyze_requires_a_key_by_default(strict_client, feedback_batch):
    """Anonymous access must be off unless explicitly enabled: /analyze spends
    real money on every call."""
    response = await strict_client.post("/analyze", json=_payload(feedback_batch))
    assert response.status_code == 401
    assert "X-API-Key" in response.json()["detail"]


async def test_reads_require_a_key_too(strict_client):
    assert (await strict_client.get("/themes")).status_code == 401
    assert (await strict_client.get("/runs")).status_code == 401


async def test_invalid_key_is_rejected(strict_client, feedback_batch):
    response = await strict_client.post(
        "/analyze",
        json=_payload(feedback_batch),
        headers={"X-API-Key": "sk_not-a-real-key"},
    )
    assert response.status_code == 401


async def test_health_and_graph_stay_open(strict_client):
    """Unauthenticated so a load balancer can probe them."""
    assert (await strict_client.get("/health")).status_code == 200
    assert (await strict_client.get("/graph")).status_code == 200


async def test_anonymous_mode_maps_to_the_default_workspace(
    anon_client, runtime, feedback_batch
):
    from app.store import repo

    response = await anon_client.post("/analyze", json=_payload(feedback_batch))
    assert response.status_code == 200

    async with runtime.session_factory() as session:
        runs = await repo.list_runs(session, workspace_id=DEFAULT_WORKSPACE_ID)

    assert len(runs) == 1


async def test_a_valid_key_resolves_to_its_own_workspace(
    runtime, session_factory, settings, workspace, feedback_batch
):
    from app.store import repo

    _wire(runtime, session_factory, settings)
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://test",
        headers={"X-API-Key": workspace.api_key},
    ) as client:
        assert (
            await client.post("/analyze", json=_payload(feedback_batch))
        ).status_code == 200

    async with session_factory() as session:
        runs = await repo.list_runs(session, workspace_id=workspace.id)
        default_runs = await repo.list_runs(
            session, workspace_id=DEFAULT_WORKSPACE_ID
        )

    assert len(runs) == 1
    assert default_runs == []


def test_keys_are_only_ever_stored_hashed():
    key = generate_api_key()
    digest = hash_api_key(key)

    assert key not in digest
    assert len(digest) == 64
    assert hash_api_key(key) == digest, "hashing must be deterministic"


# --------------------------------------------------------------------------
# Rate limiting
# --------------------------------------------------------------------------


def test_bucket_allows_capacity_then_refuses():
    from fastapi import HTTPException

    limiter = RateLimiter(capacity=2, window_seconds=60)

    limiter.check("ws")
    limiter.check("ws")

    with pytest.raises(HTTPException) as excinfo:
        limiter.check("ws")

    assert excinfo.value.status_code == 429
    assert "Retry-After" in excinfo.value.headers


def test_buckets_are_per_workspace():
    limiter = RateLimiter(capacity=1, window_seconds=60)

    limiter.check("workspace-a")
    # A different workspace has its own allowance and must not be affected.
    limiter.check("workspace-b")


def test_zero_capacity_disables_the_limiter():
    limiter = RateLimiter(capacity=0, window_seconds=60)
    for _ in range(50):
        limiter.check("ws")


async def test_analyze_returns_429_once_the_bucket_is_empty(
    runtime, session_factory, settings, workspace, feedback_batch
):
    _wire(runtime, session_factory, settings, capacity=1)

    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://test",
        headers={"X-API-Key": workspace.api_key},
    ) as client:
        first = await client.post("/analyze", json=_payload(feedback_batch))
        second = await client.post("/analyze", json=_payload(feedback_batch))

        # Reads stay unthrottled: they cost nothing.
        listed = await client.get("/themes")

    assert first.status_code == 200
    assert second.status_code == 429
    assert listed.status_code == 200
