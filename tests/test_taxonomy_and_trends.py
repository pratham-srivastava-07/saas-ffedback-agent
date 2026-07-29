"""Taxonomy persistence and trend detection — the memory half of the product."""

from __future__ import annotations

from app.graph.nodes.taxonomy import resolve_taxonomy
from app.graph.nodes.trends import detect_trends
from app.store import repo
from tests.fakes import FakeEmbeddings

EMBEDDER = FakeEmbeddings()


async def test_recurring_cluster_matches_its_stored_theme(runtime, config):
    """The core fix: a theme seen before keeps its identity and its name
    instead of being invented again on every run."""
    centroid = EMBEDDER.embed_query("signup is broken")

    async with runtime.session_factory() as session:
        stored = await repo.create_theme(
            session,
            name="Signup failures",
            description="Users cannot complete signup.",
            centroid=centroid,
            run_id="run-1",
            mentions=3,
        )

    result = await resolve_taxonomy(
        {
            "run_id": "run-2",
            "clusters": [{"index": 0, "item_ids": ["a", "b"], "centroid": centroid}],
        },
        config,
    )

    theme = result["themes"][0]
    assert theme["is_new"] is False
    assert theme["id"] == stored.id
    assert theme["name"] == "Signup failures"


async def test_unrelated_cluster_becomes_a_new_theme(runtime, config):
    async with runtime.session_factory() as session:
        await repo.create_theme(
            session,
            name="Signup failures",
            description="",
            centroid=EMBEDDER.embed_query("signup is broken"),
            run_id="run-1",
            mentions=3,
        )

    result = await resolve_taxonomy(
        {
            "run_id": "run-2",
            "clusters": [
                {
                    "index": 0,
                    "item_ids": ["x"],
                    "centroid": EMBEDDER.embed_query("billing is wrong"),
                }
            ],
        },
        config,
    )

    assert result["themes"][0]["is_new"] is True
    assert result["themes"][0]["id"] is None


async def test_one_stored_theme_cannot_absorb_two_clusters(runtime, config):
    """Otherwise two distinct clusters collapse into one theme and we lose the
    distinction clustering just found."""
    centroid = EMBEDDER.embed_query("signup is broken")

    async with runtime.session_factory() as session:
        await repo.create_theme(
            session,
            name="Signup failures",
            description="",
            centroid=centroid,
            run_id="run-1",
            mentions=1,
        )

    result = await resolve_taxonomy(
        {
            "run_id": "run-2",
            "clusters": [
                {"index": 0, "item_ids": ["a"], "centroid": centroid},
                {"index": 1, "item_ids": ["b"], "centroid": centroid},
            ],
        },
        config,
    )

    matched = [t for t in result["themes"] if not t["is_new"]]
    assert len(matched) == 1


# --------------------------------------------------------------------------
# Trends
# --------------------------------------------------------------------------


async def _seed_history(session_factory, theme_id: str, shares: list[float]) -> None:
    async with session_factory() as session:
        for index, share in enumerate(shares):
            await repo.save_snapshot(
                session,
                theme_id=theme_id,
                run_id=f"old-run-{index}",
                count=int(share * 100),
                share=share,
                avg_severity=3.0,
                positive=0,
                neutral=0,
                negative=1,
                churn_risk_count=0,
            )


async def test_new_theme_is_reported_as_emerging(runtime, config):
    async with runtime.session_factory() as session:
        theme = await repo.create_theme(
            session, name="Export bug", description="", centroid=[1.0],
            run_id="run-1", mentions=2,
        )

    result = await detect_trends(
        {
            "run_id": "run-1",
            "themes": [{"id": theme.id, "name": "Export bug", "is_new": True, "share": 0.4, "count": 2}],
        },
        config,
    )

    assert result["trends"][0]["direction"] == "emerging"


async def test_thin_history_reports_insufficient_rather_than_a_percentage(
    runtime, config
):
    """Two data points is not a trend. Saying so is the honest answer."""
    async with runtime.session_factory() as session:
        theme = await repo.create_theme(
            session, name="Signup", description="", centroid=[1.0],
            run_id="run-0", mentions=1,
        )

    await _seed_history(runtime.session_factory, theme.id, [0.1, 0.1])

    result = await detect_trends(
        {
            "run_id": "run-9",
            "themes": [{"id": theme.id, "name": "Signup", "is_new": False, "share": 0.9, "count": 9}],
        },
        config,
    )

    trend = result["trends"][0]
    assert trend["direction"] == "insufficient_history"
    assert trend["change_ratio"] is None


async def test_spike_detected_once_history_is_deep_enough(runtime, config):
    async with runtime.session_factory() as session:
        theme = await repo.create_theme(
            session, name="Signup", description="", centroid=[1.0],
            run_id="run-0", mentions=1,
        )

    await _seed_history(runtime.session_factory, theme.id, [0.10, 0.12, 0.08])

    result = await detect_trends(
        {
            "run_id": "run-9",
            "themes": [{"id": theme.id, "name": "Signup", "is_new": False, "share": 0.5, "count": 5}],
        },
        config,
    )

    trend = result["trends"][0]
    assert trend["direction"] == "spiking"
    assert trend["change_ratio"] > 2.0


async def test_declining_theme_detected(runtime, config):
    async with runtime.session_factory() as session:
        theme = await repo.create_theme(
            session, name="Signup", description="", centroid=[1.0],
            run_id="run-0", mentions=1,
        )

    await _seed_history(runtime.session_factory, theme.id, [0.40, 0.44, 0.36])

    result = await detect_trends(
        {
            "run_id": "run-9",
            "themes": [{"id": theme.id, "name": "Signup", "is_new": False, "share": 0.05, "count": 1}],
        },
        config,
    )

    assert result["trends"][0]["direction"] == "declining"


async def test_current_run_snapshot_is_recorded_for_future_comparison(
    runtime, config
):
    async with runtime.session_factory() as session:
        theme = await repo.create_theme(
            session, name="Signup", description="", centroid=[1.0],
            run_id="run-0", mentions=1,
        )

    await detect_trends(
        {
            "run_id": "run-current",
            "themes": [
                {
                    "id": theme.id,
                    "name": "Signup",
                    "is_new": False,
                    "share": 0.25,
                    "count": 2,
                    "avg_severity": 4.0,
                    "sentiment_breakdown": {"positive": 0, "neutral": 0, "negative": 2},
                    "churn_risk_count": 1,
                }
            ],
        },
        config,
    )

    async with runtime.session_factory() as session:
        history = await repo.theme_history(session, theme.id)

    assert len(history) == 1
    assert history[0].share == 0.25
    assert history[0].churn_risk_count == 1
