"""Check the recommendations against the evidence before anyone sees them.

Recommendations are the softest output in the pipeline — an LLM asked for
product advice will happily invent a plausible-sounding feature nobody asked
for. This node reads them back against the themes and sends them round again
if they are not supported.

The loop it forms is bounded in ``build.py``. An unbounded cycle is how a
LangGraph demo hangs in front of an audience.
"""

from __future__ import annotations

import logging

from app.graph.nodes._common import call_structured, theme_evidence_block
from app.graph.state import AnalysisState
from app.llm import get_runtime
from app.schemas import CritiqueVerdict

logger = logging.getLogger(__name__)

SYSTEM = """You audit product recommendations against the evidence they claim \
to rest on.

Reject a recommendation if it:
- addresses a problem absent from the themes,
- cites counts or severities that do not match the evidence,
- references a theme id that was not supplied, or
- is too vague to act on ("improve the UX").

Approve when every recommendation is grounded. Be strict but do not invent \
objections — if the set is sound, approve it."""


async def critique(state: AnalysisState, config=None) -> dict:
    runtime = get_runtime(config)
    recommendations = state.get("recommendations", [])

    # Nothing to audit: approve so the graph moves on rather than looping.
    if not recommendations:
        return {"critique": {"approved": True, "issues": [], "guidance": ""}}

    rendered = "\n".join(
        f"- [{rec.get('effort')}] {rec.get('title')} "
        f"(themes: {', '.join(rec.get('theme_ids', []))})\n  {rec.get('rationale')}"
        for rec in recommendations
    )

    prompt = (
        f"EVIDENCE:\n{theme_evidence_block(state.get('themes', []))}\n\n"
        f"RECOMMENDATIONS UNDER REVIEW:\n{rendered}"
    )

    try:
        verdict = await call_structured(runtime, CritiqueVerdict, SYSTEM, prompt)
        return {"critique": verdict.model_dump()}
    except Exception as exc:  # noqa: BLE001
        # A failed audit must not trap the run in the cycle.
        logger.warning("critique failed, passing through: %s", exc)
        return {
            "critique": {
                "approved": True,
                "issues": [],
                "guidance": f"Critique unavailable: {exc}"[:300],
            }
        }
