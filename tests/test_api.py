"""API surface: contracts, input bounds, and the SSE stream."""

from __future__ import annotations

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.ratelimit import RateLimiter
from app.main import app as fastapi_app


@pytest_asyncio.fixture
async def client(runtime, session_factory, settings, workspace):
    """Authenticated client. Bypasses the lifespan, which would build a real
    runtime and demand provider keys."""
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


def _payload(batch):
    return {"raw_feedback": batch}


async def test_health(client):
    assert (await client.get("/health")).json() == {"status": "ok"}


async def test_analyze_returns_themes_and_recommendations(client, feedback_batch):
    response = await client.post("/analyze", json=_payload(feedback_batch))

    assert response.status_code == 200
    body = response.json()

    assert body["run_id"]
    assert body["summary"]
    assert len(body["analyzed"]) == 5
    assert body["themes"]
    assert body["themes"][0]["impact_score"] > 0
    # Analysed items carry the theme they were assigned to.
    assert any(item["theme_id"] for item in body["analyzed"])


async def test_empty_batch_is_rejected(client):
    assert (await client.post("/analyze", json=_payload([]))).status_code == 422


async def test_oversized_batch_is_rejected(client):
    batch = [{"text": f"feedback number {n}"} for n in range(201)]
    assert (await client.post("/analyze", json=_payload(batch))).status_code == 422


async def test_oversized_item_is_rejected(client):
    batch = [{"text": "x" * 5001}]
    assert (await client.post("/analyze", json=_payload(batch))).status_code == 422


async def test_run_is_recorded_and_listable(client, feedback_batch):
    run_id = (await client.post("/analyze", json=_payload(feedback_batch))).json()[
        "run_id"
    ]

    listed = (await client.get("/runs")).json()
    assert any(run["id"] == run_id for run in listed)

    detail = (await client.get(f"/runs/{run_id}")).json()
    assert detail["status"] == "completed"
    assert detail["item_count"] == 5
    assert detail["theme_count"] >= 1


async def test_unknown_run_is_404(client):
    assert (await client.get("/runs/does-not-exist")).status_code == 404


async def test_themes_accumulate_across_runs(client, feedback_batch):
    await client.post("/analyze", json=_payload(feedback_batch))
    await client.post(
        "/analyze",
        json=_payload(
            [{"text": "Signup keeps failing on the second step", "user_type": "paid"}]
        ),
    )

    themes = (await client.get("/themes")).json()
    signup = [theme for theme in themes if "Signup" in theme["name"]]

    # One stable theme that has now been seen in two runs, not two themes.
    assert len(signup) == 1
    assert signup[0]["run_count"] == 2

    trends = (await client.get("/themes/trends")).json()
    tracked = next(t for t in trends if t["id"] == signup[0]["id"])
    assert len(tracked["history"]) == 2


async def test_stream_emits_node_events_then_completes(client, feedback_batch):
    events: list[str] = []

    async with client.stream(
        "POST", "/analyze/stream", json=_payload(feedback_batch)
    ) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        async for line in response.aiter_lines():
            if line.startswith("event: "):
                events.append(line.removeprefix("event: ").strip())

    assert events[0] == "run_start"
    assert events[-1] == "complete"
    assert "node_start" in events
    assert "node_end" in events


async def test_graph_topology_endpoint_reflects_the_real_graph(client):
    mermaid = (await client.get("/graph")).json()["mermaid"]

    for node in ("normalize", "triage", "analyze_one", "cluster", "critique"):
        assert node in mermaid
