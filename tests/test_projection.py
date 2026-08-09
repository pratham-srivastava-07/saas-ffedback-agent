"""3D projection and the cluster-explorer scatter endpoint."""

from __future__ import annotations

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.ratelimit import RateLimiter
from app.main import app as fastapi_app
from app.projection import project_to_3d
from tests.fakes import FakeEmbeddings

EMBEDDER = FakeEmbeddings()


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


def _embeddings(texts: dict[str, str]) -> dict[str, list[float]]:
    return {key: EMBEDDER.embed_query(text) for key, text in texts.items()}


# --------------------------------------------------------------------------
# Projection
# --------------------------------------------------------------------------


def test_projects_to_three_normalised_coordinates():
    points = project_to_3d(
        _embeddings(
            {
                "1": "signup is broken",
                "2": "billing charged twice",
                "3": "the dashboard is slow",
                "4": "export to csv missing",
                "5": "mobile app crashes",
            }
        )
    )

    assert len(points) == 5
    for coords in points.values():
        assert len(coords) == 3
        assert all(-1.0001 <= value <= 1.0001 for value in coords), coords

    # Something must actually reach the edge, or the normalisation is wrong.
    assert max(abs(v) for coords in points.values() for v in coords) > 0.99


def test_related_items_project_closer_than_unrelated_ones():
    """The plot is only meaningful if the geometry survives the projection."""
    points = project_to_3d(
        _embeddings(
            {
                "a": "signup is broken",
                "b": "signup fails every time",
                "c": "billing charged twice",
                "d": "billing is wrong",
            }
        )
    )

    def distance(left: str, right: str) -> float:
        return sum(
            (points[left][i] - points[right][i]) ** 2 for i in range(3)
        ) ** 0.5

    assert distance("a", "b") < distance("a", "c")
    assert distance("c", "d") < distance("c", "a")


def test_empty_input_returns_nothing():
    assert project_to_3d({}) == {}


def test_single_item_sits_at_the_origin():
    """One point has no position relative to anything, and PCA has no
    variance to find."""
    points = project_to_3d(_embeddings({"only": "signup is broken"}))
    assert points == {"only": (0.0, 0.0, 0.0)}


def test_two_items_pad_the_missing_axis_rather_than_raising():
    """Two samples yield at most one component; the frontend still needs
    three coordinates."""
    points = project_to_3d(
        _embeddings({"1": "signup is broken", "2": "billing is wrong"})
    )

    assert len(points) == 2
    assert all(len(coords) == 3 for coords in points.values())


def test_identical_vectors_collapse_to_the_origin_without_dividing_by_zero():
    """Zero variance means zero scale. The honest picture is one dot, not a
    crash."""
    vector = EMBEDDER.embed_query("signup is broken")
    points = project_to_3d({"1": vector, "2": list(vector), "3": list(vector)})

    assert len(points) == 3
    assert all(coords == (0.0, 0.0, 0.0) for coords in points.values())


def test_empty_vectors_are_skipped():
    points = project_to_3d({"1": [], "2": EMBEDDER.embed_query("signup broken")})
    assert list(points) == ["2"]


def test_low_dimensional_vectors_are_handled():
    """Fewer features than components available."""
    points = project_to_3d({"1": [1.0, 0.0], "2": [0.0, 1.0], "3": [0.5, 0.5]})

    assert len(points) == 3
    assert all(len(coords) == 3 for coords in points.values())


# --------------------------------------------------------------------------
# Endpoint
# --------------------------------------------------------------------------


@pytest_asyncio.fixture
async def analyzed(client, feedback_batch):
    response = await client.post("/analyze", json={"raw_feedback": feedback_batch})
    assert response.status_code == 200
    return response.json()


async def test_scatter_returns_a_point_per_item(client, analyzed):
    response = await client.get(f"/runs/{analyzed['run_id']}/scatter")

    assert response.status_code == 200
    body = response.json()

    assert len(body["points"]) == 5
    assert body["themes"]

    point = body["points"][0]
    assert set(point) == {
        "item_id",
        "theme_id",
        "theme_name",
        "x",
        "y",
        "z",
        "sentiment",
        "severity",
        "text",
    }


async def test_scatter_coordinates_are_within_range(client, analyzed):
    body = (await client.get(f"/runs/{analyzed['run_id']}/scatter")).json()

    for point in body["points"]:
        for axis in ("x", "y", "z"):
            assert -1.0001 <= point[axis] <= 1.0001


async def test_scatter_points_carry_their_theme(client, analyzed):
    body = (await client.get(f"/runs/{analyzed['run_id']}/scatter")).json()

    named = [p for p in body["points"] if p["theme_id"]]
    assert named, "no point was assigned a theme"
    assert all(p["theme_name"] for p in named)

    # Theme counts agree with how many points carry that theme.
    counts = {theme["id"]: theme["count"] for theme in body["themes"]}
    signup = next(t for t in body["themes"] if "Signup" in t["name"])
    plotted = [p for p in body["points"] if p["theme_id"] == signup["id"]]
    assert len(plotted) == counts[signup["id"]] == 3


async def test_scatter_404s_for_an_unknown_run(client):
    assert (await client.get("/runs/nope/scatter")).status_code == 404


async def test_scatter_404s_across_workspaces(
    runtime, session_factory, settings, other_workspace, analyzed
):
    fastapi_app.state.rate_limiter = RateLimiter(capacity=100, window_seconds=60)
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://test",
        headers={"X-API-Key": other_workspace.api_key},
    ) as intruder:
        response = await intruder.get(f"/runs/{analyzed['run_id']}/scatter")

    assert response.status_code == 404


async def test_scatter_is_empty_but_valid_for_a_run_with_nothing_analysed(client):
    """A batch of pure noise short-circuits the pipeline, so there is nothing
    to plot. The endpoint must still answer cleanly."""
    noise = [
        {"id": "1", "text": "ok", "user_type": "free", "source": "support"},
        {"id": "2", "text": "?!?!?!", "user_type": "free", "source": "support"},
    ]
    run_id = (
        await client.post("/analyze", json={"raw_feedback": noise})
    ).json()["run_id"]

    response = await client.get(f"/runs/{run_id}/scatter")

    assert response.status_code == 200
    assert response.json() == {"points": [], "themes": []}
