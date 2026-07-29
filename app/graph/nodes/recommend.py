"""Turn ranked themes into product actions.

Re-entered when ``critique`` rejects the previous attempt, in which case the
critique's guidance is fed back in. ``revision_count`` is incremented here and
is what bounds the cycle.
"""

from __future__ import annotations

import logging

from app.graph.nodes._common import call_structured, theme_evidence_block, trend_block
from app.graph.state import AnalysisState
from app.llm import get_runtime
from app.schemas import RecommendationSet

logger = logging.getLogger(__name__)

SYSTEM = """You are a product analyst advising a SaaS team on what to fix next.

Rules:
- Every recommendation must trace to the supplied themes. Cite mention counts \
and severities in the rationale.
- Reference themes by the exact id given.
- Do not invent problems that are not in the evidence.
- Order by impact. Three to five recommendations."""


async def recommend(state: AnalysisState, config=None) -> dict:
    runtime = get_runtime(config)
    themes = state.get("themes", [])
    revision = state.get("revision_count", 0)

    if not themes:
        return {"recommendations": [], "revision_count": revision}

    prompt = (
        f"THEMES (ranked by impact):\n{theme_evidence_block(themes)}\n\n"
        f"TRENDS:\n{trend_block(state.get('trends', []))}"
    )

    critique = state.get("critique")
    if critique and not critique.get("approved"):
        issues = "\n".join(f"- {issue}" for issue in critique.get("issues", []))
        prompt += (
            "\n\nYour previous attempt was rejected for these reasons:\n"
            f"{issues}\n\nGuidance: {critique.get('guidance', '')}\n"
            "Produce a corrected set grounded strictly in the evidence above."
        )

    try:
        result = await call_structured(runtime, RecommendationSet, SYSTEM, prompt)
        recommendations = [rec.model_dump() for rec in result.recommendations]
    except Exception as exc:  # noqa: BLE001
        logger.warning("recommend failed: %s", exc)
        recommendations = []

    return {"recommendations": recommendations, "revision_count": revision + 1}
