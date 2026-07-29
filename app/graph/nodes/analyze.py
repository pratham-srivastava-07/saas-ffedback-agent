"""Per-item understanding. One structured LLM call per feedback item.

This node is the target of a ``Send`` fan-out, so LangGraph runs one instance
per item concurrently and the ``operator.add`` reducer on ``analyzed``
collects the results. The previous implementation made two sequential calls
per item (classify, then theme) inside a synchronous handler.

Failures are isolated: a single item that the model chokes on is returned with
``status="failed"`` rather than raising, because one malformed row should not
destroy a 200-item run.
"""

from __future__ import annotations

import logging

from langchain_core.runnables import RunnableConfig

from app.graph.nodes._common import call_structured
from app.llm import get_runtime
from app.schemas import ItemAnalysis

logger = logging.getLogger(__name__)

SYSTEM = """You analyse SaaS customer feedback for a product team.

Judge only what the text actually says. Do not infer a severity or a churn \
risk that the user did not express — inflated severity makes the priority \
ranking useless.

Severity guide:
1 cosmetic nitpick, 2 minor annoyance, 3 real friction with a workaround,
4 blocks a core task, 5 data loss, security, or total outage."""


async def analyze_one(payload: dict, config: RunnableConfig) -> dict:
    runtime = get_runtime(config)
    item = payload["item"]

    user = (
        f"Source: {item['source']}\n"
        f"Customer tier: {item['user_type']}\n"
        f"Feedback: {item['text']}"
    )

    try:
        analysis = await call_structured(runtime, ItemAnalysis, SYSTEM, user)
        analyzed = {
            **item,
            "sentiment": analysis.sentiment,
            "emotion": analysis.emotion,
            "intent": analysis.intent,
            "severity": analysis.severity,
            "feature_area": analysis.feature_area,
            "churn_risk": analysis.churn_risk,
            "status": "ok",
            "error": None,
        }
    except Exception as exc:  # noqa: BLE001 - one bad item must not kill the run
        logger.warning("analyze_one failed for %s: %s", item.get("id"), exc)
        analyzed = {
            **item,
            "sentiment": "neutral",
            "emotion": "neutral",
            "intent": "other",
            "severity": 1,
            "feature_area": "unknown",
            "churn_risk": False,
            "status": "failed",
            "error": str(exc)[:300],
        }

    return {"analyzed": [analyzed]}
