"""Reading back the evidence: items behind a theme, and past run results.

The product promises a ranked list "with the evidence attached". Before these
endpoints you could see that 34 people complained and never read what any of
them said.
"""

from __future__ import annotations

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.ratelimit import RateLimiter
from app.main import app as fastapi_app


@pytest_asyncio.fixture
async def client(runtime, session_factory, settings, workspace):
    fastapi_app.state.runtime = runtime
    fastapi_app.state.session_factory = session_factory
    fastapi_app.state.settings = settings
    fastapi_app.state.rate_limiter = RateLimiter(
        capacity=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://test",
        headers={"X-API-Key": workspace.api_key},
    ) as async_client:
        yield async_client


@pytest_asyncio.fixture
async def analyzed(client, feedback_batch):
    response = await client.post("/analyze", json={"raw_feedback": feedback_batch})
    assert response.status_code == 200
    return response.json()


async def test_theme_items_returns_the_feedback_behind_a_theme(client, analyzed):
    signup = next(t for t in analyzed["themes"] if "Signup" in t["name"])

    response = await client.get(f"/themes/{signup['id']}/items")
    assert response.status_code == 200
    body = response.json()

    assert body["theme"]["id"] == signup["id"]
    assert body["total"] == 3
    assert len(body["items"]) == 3

    texts = {item["text"] for item in body["items"]}
    assert any("Signup is broken" in text for text in texts)
    # Each carries its analysis, not just the raw text.
    assert all(item["sentiment"] for item in body["items"])


async def test_theme_items_paginate(client, analyzed):
    signup = next(t for t in analyzed["themes"] if "Signup" in t["name"])

    first = (await client.get(f"/themes/{signup['id']}/items?limit=2")).json()
    second = (
        await client.get(f"/themes/{signup['id']}/items?limit=2&offset=2")
    ).json()

    assert len(first["items"]) == 2
    assert len(second["items"]) == 1
    assert first["total"] == second["total"] == 3

    ids = {item["id"] for item in first["items"]} | {
        item["id"] for item in second["items"]
    }
    assert len(ids) == 3, "pages overlapped"


async def test_unknown_theme_is_404(client):
    assert (await client.get("/themes/nope/items")).status_code == 404


async def test_another_workspace_cannot_read_a_theme(
    runtime, session_factory, settings, other_workspace, analyzed
):
    """Scoping is enforced at the endpoint, not just in the query helper."""
    signup = next(t for t in analyzed["themes"] if "Signup" in t["name"])

    fastapi_app.state.rate_limiter = RateLimiter(capacity=100, window_seconds=60)
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://test",
        headers={"X-API-Key": other_workspace.api_key},
    ) as intruder:
        response = await intruder.get(f"/themes/{signup['id']}/items")

    assert response.status_code == 404


async def test_run_result_rebuilds_the_full_past_result(client, analyzed):
    response = await client.get(f"/runs/{analyzed['run_id']}/result")
    assert response.status_code == 200
    body = response.json()

    assert body["id"] == analyzed["run_id"]
    assert len(body["analyzed"]) == len(analyzed["analyzed"])
    assert len(body["themes"]) == len(analyzed["themes"])
    assert body["recommendations"] == analyzed["recommendations"]

    # Ranked the way the run itself ranked them.
    scores = [theme["impact_score"] for theme in body["themes"]]
    assert scores == sorted(scores, reverse=True)


async def test_stored_trends_preserve_the_emerging_verdict(client, analyzed):
    """Trends are persisted rather than recomputed because "emerging" depends
    on whether a theme was new *at the time*, which snapshots cannot recover."""
    body = (await client.get(f"/runs/{analyzed['run_id']}/result")).json()

    directions = {trend["direction"] for trend in body["trends"]}
    assert directions, "no trends were persisted"
    assert directions == {
        trend["direction"] for trend in analyzed["trends"]
    }


async def test_run_result_404s_for_another_workspace(
    runtime, session_factory, settings, other_workspace, analyzed
):
    fastapi_app.state.rate_limiter = RateLimiter(capacity=100, window_seconds=60)
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://test",
        headers={"X-API-Key": other_workspace.api_key},
    ) as intruder:
        response = await intruder.get(f"/runs/{analyzed['run_id']}/result")

    assert response.status_code == 404


async def test_stale_runs_are_reaped(runtime):
    """A crash mid-run leaves rows stuck at "running" with nothing to clear
    them, so they accumulate as ghosts in every run list."""
    from datetime import timedelta

    from app.store import repo
    from app.store.models import Run, _utcnow

    async with runtime.session_factory() as session:
        await repo.create_run(session, "fresh-run")
        stale = await repo.create_run(session, "stale-run")

        aged = await session.get(Run, stale.id)
        aged.created_at = _utcnow() - timedelta(hours=2)
        await session.commit()

        reaped = await repo.reap_stale_runs(session, older_than_minutes=30)

        assert reaped == 1
        assert (await session.get(Run, "stale-run")).status == "failed"
        # The in-flight one is untouched.
        assert (await session.get(Run, "fresh-run")).status == "running"
