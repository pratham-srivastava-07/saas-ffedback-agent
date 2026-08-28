"""Feature-area rollup.

The second cut of the data: themes say what is wrong, areas say which part of
the product owns it. The dimension was already recorded on every item and
never aggregated, so these tests mostly guard the aggregation itself.
"""

from __future__ import annotations

import pytest

from app.store import repo


async def _seed(session_factory, workspace_id: str, run_id: str, items: list[dict]):
    """Write analysed items straight to the store, skipping the graph.

    The rollup reads stored rows, so driving the pipeline here would test the
    LLM fakes rather than the query.
    """
    async with session_factory() as session:
        await repo.create_run(session, run_id, workspace_id)
        await repo.save_items(session, run_id, items, workspace_id)


def _item(external_id: str, area: str, **overrides):
    base = {
        "id": external_id,
        "text": f"feedback {external_id}",
        "user_type": "paid",
        "source": "support",
        "sentiment": "negative",
        "emotion": "frustrated",
        "intent": "bug-report",
        "severity": 4,
        "feature_area": area,
        "churn_risk": False,
        "status": "ok",
    }
    base.update(overrides)
    return base


@pytest.fixture
async def seeded(session_factory, workspace):
    await _seed(
        session_factory,
        workspace.id,
        "run-areas",
        [
            _item("1", "billing", churn_risk=True, severity=5),
            _item("2", "billing", severity=3),
            _item("3", "billing", sentiment="positive", severity=1),
            _item("4", "signup", severity=4),
            _item("5", "signup", severity=4),
            _item("6", "export", sentiment="neutral", severity=2),
            # Unplaced items are counted, but never ranked as a product area.
            _item("7", "unknown"),
            _item("8", "unknown"),
            # A failed row carries placeholder analysis the model never wrote.
            _item("9", "unknown", status="failed"),
        ],
    )
    return workspace


async def test_areas_are_ranked_by_mentions(client, seeded):
    body = (await client.get("/insights/feature-areas")).json()

    assert [area["name"] for area in body["areas"]] == ["billing", "signup", "export"]
    assert [area["mentions"] for area in body["areas"]] == [3, 2, 1]


async def test_unclassified_is_reported_but_never_ranked(client, seeded):
    """It is usually the largest bucket. Ranking it alongside real product
    areas would misrepresent both its size and its meaning."""
    body = (await client.get("/insights/feature-areas")).json()

    assert "unknown" not in [area["name"] for area in body["areas"]]
    assert body["unclassified"] == 2


async def test_failed_items_are_excluded(client, seeded):
    """A failed item is stored with placeholder analysis, so counting it would
    inflate the unclassified bucket with rows nothing ever read."""
    body = (await client.get("/insights/feature-areas")).json()

    # Eight ok items, not the nine that exist.
    assert body["total_items"] == 8
    assert body["unclassified"] == 2


async def test_per_area_statistics(client, seeded):
    body = (await client.get("/insights/feature-areas")).json()
    billing = next(a for a in body["areas"] if a["name"] == "billing")

    assert billing["avg_severity"] == 3.0  # (5 + 3 + 1) / 3
    assert billing["churn_risk_count"] == 1
    assert billing["sentiment"] == {"positive": 1, "neutral": 0, "negative": 2}
    assert billing["share"] == pytest.approx(3 / 8)


async def test_shares_sum_to_the_classified_portion(client, seeded):
    body = (await client.get("/insights/feature-areas")).json()

    classified = sum(area["share"] for area in body["areas"])
    expected = (body["total_items"] - body["unclassified"]) / body["total_items"]
    assert classified == pytest.approx(expected)


async def test_limit_is_honoured(client, seeded):
    body = (await client.get("/insights/feature-areas?limit=2")).json()

    assert len(body["areas"]) == 2
    # Still the whole picture, so a truncated list cannot be mistaken for one.
    assert body["total_items"] == 8


async def test_limit_is_bounded(client):
    assert (await client.get("/insights/feature-areas?limit=0")).status_code == 422
    assert (await client.get("/insights/feature-areas?limit=500")).status_code == 422


async def test_empty_workspace_returns_zeros_not_an_error(client):
    body = (await client.get("/insights/feature-areas")).json()

    assert body == {"areas": [], "total_items": 0, "unclassified": 0}


async def test_areas_are_scoped_to_the_workspace(
    client, session_factory, other_workspace, seeded
):
    """Another tenant's feedback must not appear in this rollup."""
    await _seed(
        session_factory,
        other_workspace.id,
        "run-other",
        [_item("x1", "notifications"), _item("x2", "notifications")],
    )

    body = (await client.get("/insights/feature-areas")).json()

    assert "notifications" not in [area["name"] for area in body["areas"]]
    assert body["total_items"] == 8


async def test_requires_a_key(client):
    response = await client.get(
        "/insights/feature-areas", headers={"X-API-Key": "nope"}
    )
    assert response.status_code == 401
