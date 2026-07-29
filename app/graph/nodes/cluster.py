"""Group semantically related feedback.

This is the node the whole product rests on. The previous implementation asked
the LLM to label each item with a free-text theme in isolation, so "Signup bug"
and "Bug in Signup Flow" never joined up and counting was impossible.

Agglomerative clustering, not HDBSCAN. HDBSCAN is the more fashionable choice
and is better on large corpora, but it labels most points as noise on a
ten-item batch, which reads as a broken demo. Agglomerative with a cosine
distance threshold needs no ``k`` and degrades gracefully at small scale.
"""

from __future__ import annotations

from app.graph.state import AnalysisState
from app.graph.vectors import centroid
from app.llm import get_runtime


async def cluster(state: AnalysisState, config=None) -> dict:
    runtime = get_runtime(config)
    threshold = runtime.settings.cluster_distance_threshold

    embeddings = state.get("embeddings", {})
    item_ids = [item_id for item_id in embeddings if embeddings[item_id]]

    if not item_ids:
        return {"clusters": []}

    # sklearn needs at least two samples to build a linkage tree.
    if len(item_ids) == 1:
        only = item_ids[0]
        return {
            "clusters": [
                {
                    "index": 0,
                    "item_ids": [only],
                    "centroid": centroid([embeddings[only]]),
                }
            ]
        }

    from sklearn.cluster import AgglomerativeClustering

    vectors = [embeddings[item_id] for item_id in item_ids]

    labels = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=threshold,
        metric="cosine",
        linkage="average",
    ).fit_predict(vectors)

    grouped: dict[int, list[str]] = {}
    for item_id, label in zip(item_ids, labels):
        grouped.setdefault(int(label), []).append(item_id)

    clusters = [
        {
            "index": index,
            "item_ids": members,
            "centroid": centroid([embeddings[member] for member in members]),
        }
        # Largest first, so the most-reported issues get named and ranked first.
        for index, (_, members) in enumerate(
            sorted(grouped.items(), key=lambda kv: -len(kv[1]))
        )
    ]

    return {"clusters": clusters}
