"""Rank themes by impact. This produces the actual answer the product exists for.

A raw mention count is the wrong ranking: ten free users mildly annoyed by a
tooltip should not outrank three enterprise customers hitting data loss. The
score combines how many people are affected (weighted by what they are worth),
how badly, and whether any of them are signalling they will leave.
"""

from __future__ import annotations

from app.graph.state import AnalysisState
from app.llm import get_runtime


async def prioritize(state: AnalysisState, config=None) -> dict:
    runtime = get_runtime(config)
    weights = runtime.settings.user_tier_weights

    themes = state.get("themes", [])
    by_id = {item["id"]: item for item in state.get("analyzed", [])}
    total_items = max(len(by_id), 1)

    scored: list[dict] = []
    for theme in themes:
        members = [by_id[i] for i in theme.get("item_ids", []) if i in by_id]
        if not members:
            continue

        severities = [int(m.get("severity") or 1) for m in members]
        avg_severity = sum(severities) / len(severities)

        breakdown = {"positive": 0, "neutral": 0, "negative": 0}
        for member in members:
            sentiment = member.get("sentiment", "neutral")
            if sentiment in breakdown:
                breakdown[sentiment] += 1

        churn_count = sum(1 for m in members if m.get("churn_risk"))
        weighted_reach = sum(
            weights.get(m.get("user_type", "free"), 1.0) for m in members
        )
        churn_multiplier = 1.0 + (churn_count / len(members))

        scored.append(
            {
                **theme,
                "count": len(members),
                "share": len(members) / total_items,
                "avg_severity": round(avg_severity, 2),
                "sentiment_breakdown": breakdown,
                "churn_risk_count": churn_count,
                "impact_score": round(
                    weighted_reach * avg_severity * churn_multiplier, 2
                ),
            }
        )

    scored.sort(key=lambda theme: -theme["impact_score"])
    return {"themes": scored}
