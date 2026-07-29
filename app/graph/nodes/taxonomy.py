"""Reconcile this run's clusters against the stored theme taxonomy.

This is what makes trajectory possible. Without it every run invents fresh
theme names and "is this getting worse?" cannot be answered, because there is
nothing stable to compare against.

Each cluster centroid is compared to the centroids of themes we have already
seen. Above the merge threshold it *is* that theme and keeps its established
name; below, it is genuinely new and gets named downstream.
"""

from __future__ import annotations

import logging

from app.graph.state import AnalysisState
from app.graph.vectors import cosine_similarity
from app.llm import get_runtime
from app.store import repo

logger = logging.getLogger(__name__)


async def resolve_taxonomy(state: AnalysisState, config=None) -> dict:
    runtime = get_runtime(config)
    clusters = state.get("clusters", [])

    if not clusters:
        return {"themes": []}

    if runtime.session_factory is None:
        logger.warning("No session factory; treating every cluster as new.")
        return {"themes": [_as_new(cluster) for cluster in clusters]}

    threshold = runtime.settings.theme_merge_threshold

    async with runtime.session_factory() as session:
        stored = list(await repo.load_themes(session))

        themes: list[dict] = []
        # A stored theme may only absorb one cluster per run; otherwise two
        # distinct clusters could collapse into a single theme and we would
        # lose the distinction the clustering step just found.
        claimed: set[str] = set()

        for cluster in clusters:
            best_theme = None
            best_score = 0.0

            for theme in stored:
                if theme.id in claimed:
                    continue
                score = cosine_similarity(cluster["centroid"], theme.centroid or [])
                if score > best_score:
                    best_theme, best_score = theme, score

            if best_theme is not None and best_score >= threshold:
                claimed.add(best_theme.id)
                await repo.merge_into_theme(
                    session,
                    best_theme,
                    centroid=cluster["centroid"],
                    mentions=len(cluster["item_ids"]),
                )
                themes.append(
                    {
                        "id": best_theme.id,
                        "name": best_theme.name,
                        "description": best_theme.description,
                        "is_new": False,
                        "count": len(cluster["item_ids"]),
                        "item_ids": cluster["item_ids"],
                        "centroid": cluster["centroid"],
                    }
                )
            else:
                themes.append(_as_new(cluster))

    return {"themes": themes}


def _as_new(cluster: dict) -> dict:
    return {
        "id": None,
        "name": "",
        "description": "",
        "is_new": True,
        "count": len(cluster["item_ids"]),
        "item_ids": cluster["item_ids"],
        "centroid": cluster["centroid"],
    }
