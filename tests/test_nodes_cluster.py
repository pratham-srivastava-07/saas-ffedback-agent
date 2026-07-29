"""Clustering and prioritisation — the aggregate half of the product."""

from __future__ import annotations

from app.graph.nodes.cluster import cluster
from app.graph.nodes.prioritize import prioritize
from tests.fakes import FakeEmbeddings


def _embed(texts: dict[str, str]) -> dict[str, list[float]]:
    embedder = FakeEmbeddings()
    return {item_id: embedder.embed_query(text) for item_id, text in texts.items()}


async def test_related_feedback_lands_in_one_cluster(config):
    """The failure the old implementation had: differently-worded reports of
    the same problem must group, or counting is impossible."""
    embeddings = _embed(
        {
            "1": "signup is broken",
            "2": "cannot complete signup",
            "3": "signup fails at the last step",
            "4": "billing charged me twice",
        }
    )

    result = await cluster({"embeddings": embeddings}, config)
    grouped = {frozenset(c["item_ids"]) for c in result["clusters"]}

    assert frozenset({"1", "2", "3"}) in grouped
    assert frozenset({"4"}) in grouped


async def test_cluster_handles_single_item(config):
    embeddings = _embed({"1": "signup is broken"})
    result = await cluster({"embeddings": embeddings}, config)

    assert len(result["clusters"]) == 1
    assert result["clusters"][0]["item_ids"] == ["1"]


async def test_cluster_handles_empty_input(config):
    assert await cluster({"embeddings": {}}, config) == {"clusters": []}


async def test_clusters_are_ordered_largest_first(config):
    embeddings = _embed(
        {
            "1": "billing problem",
            "2": "signup broken",
            "3": "signup broken again",
            "4": "signup still broken",
        }
    )

    result = await cluster({"embeddings": embeddings}, config)
    assert len(result["clusters"][0]["item_ids"]) == 3


async def test_enterprise_severity_outranks_free_user_volume(config):
    """Ranking by raw count would put the tooltip nitpick on top. It must not."""
    state = {
        "themes": [
            {"id": "t1", "name": "Data loss on save", "item_ids": ["a", "b"]},
            {"id": "t2", "name": "Tooltip wording", "item_ids": ["c", "d", "e", "f"]},
        ],
        "analyzed": [
            {"id": "a", "user_type": "enterprise", "severity": 5, "sentiment": "negative", "churn_risk": True},
            {"id": "b", "user_type": "enterprise", "severity": 5, "sentiment": "negative", "churn_risk": True},
            {"id": "c", "user_type": "free", "severity": 1, "sentiment": "neutral", "churn_risk": False},
            {"id": "d", "user_type": "free", "severity": 1, "sentiment": "neutral", "churn_risk": False},
            {"id": "e", "user_type": "free", "severity": 1, "sentiment": "neutral", "churn_risk": False},
            {"id": "f", "user_type": "free", "severity": 1, "sentiment": "neutral", "churn_risk": False},
        ],
    }

    result = await prioritize(state, config)

    assert result["themes"][0]["id"] == "t1"
    assert result["themes"][0]["churn_risk_count"] == 2
    assert result["themes"][0]["count"] == 2


async def test_prioritize_computes_sentiment_breakdown_and_share(config):
    state = {
        "themes": [{"id": "t1", "name": "Signup", "item_ids": ["a", "b"]}],
        "analyzed": [
            {"id": "a", "user_type": "paid", "severity": 4, "sentiment": "negative", "churn_risk": False},
            {"id": "b", "user_type": "paid", "severity": 2, "sentiment": "positive", "churn_risk": False},
        ],
    }

    theme = (await prioritize(state, config))["themes"][0]

    assert theme["sentiment_breakdown"] == {"positive": 1, "neutral": 0, "negative": 1}
    assert theme["avg_severity"] == 3.0
    assert theme["share"] == 1.0
