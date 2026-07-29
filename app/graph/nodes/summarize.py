"""The Monday-morning brief.

Also the landing point for the triage short-circuit, so it must produce
something sensible when there is nothing to summarise. That path is handled
without an LLM call: there is nothing to reason about, and a deterministic
message cannot hallucinate insights about an empty batch.
"""

from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.graph.nodes._common import theme_evidence_block, trend_block
from app.graph.state import AnalysisState
from app.llm import get_runtime

logger = logging.getLogger(__name__)

SYSTEM = """You write a short brief for a product team, read on Monday morning.

Two or three sentences. Lead with the single most important thing. Use real \
numbers from the evidence. No preamble, no "in conclusion", no bullet points."""


async def summarize(state: AnalysisState, config=None) -> dict:
    runtime = get_runtime(config)
    themes = state.get("themes", [])
    rejected = state.get("rejected", [])

    if not themes:
        if rejected:
            return {
                "summary": (
                    f"Nothing actionable in this batch: all {len(rejected)} "
                    "items were duplicates or noise."
                )
            }
        return {"summary": "No feedback was submitted."}

    analyzed = state.get("analyzed", [])
    prompt = (
        f"{len(analyzed)} items analysed, {len(themes)} themes found.\n\n"
        f"THEMES:\n{theme_evidence_block(themes)}\n\n"
        f"TRENDS:\n{trend_block(state.get('trends', []))}"
    )

    try:
        async with runtime.limiter():
            response = await runtime.chat.ainvoke(
                [SystemMessage(content=SYSTEM), HumanMessage(content=prompt)]
            )
        summary = str(getattr(response, "content", "")).strip()
    except Exception as exc:  # noqa: BLE001
        logger.warning("summarize failed: %s", exc)
        summary = ""

    if not summary:
        top = themes[0]
        summary = (
            f"{len(analyzed)} items analysed across {len(themes)} themes. "
            f"Top issue: {top.get('name')} "
            f"({top.get('count')} mentions, severity {top.get('avg_severity')}/5)."
        )

    return {"summary": summary}
