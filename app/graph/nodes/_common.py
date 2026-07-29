"""Shared helpers for graph nodes."""

from __future__ import annotations

from typing import TypeVar

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from app.llm import Runtime

T = TypeVar("T", bound=BaseModel)


async def call_structured(
    runtime: Runtime, schema: type[T], system: str, user: str
) -> T:
    """Invoke the chat model with a guaranteed shape.

    Everything goes through ``with_structured_output`` rather than parsing raw
    text, which is what made the previous implementation fail whenever the
    model wrapped its JSON in a markdown fence.
    """
    model = runtime.chat.with_structured_output(schema)
    async with runtime.limiter():
        result = await model.ainvoke(
            [SystemMessage(content=system), HumanMessage(content=user)]
        )
    return result  # type: ignore[return-value]


def theme_evidence_block(themes: list[dict], limit: int = 8) -> str:
    """Render top themes as evidence text for the recommend/critique prompts."""
    lines = []
    for theme in themes[:limit]:
        breakdown = theme.get("sentiment_breakdown", {})
        lines.append(
            f"- id={theme.get('id')} | {theme.get('name')} | "
            f"{theme.get('count', 0)} mentions | "
            f"avg severity {theme.get('avg_severity', 0):.1f}/5 | "
            f"negative {breakdown.get('negative', 0)} | "
            f"churn-risk {theme.get('churn_risk_count', 0)} | "
            f"impact {theme.get('impact_score', 0):.1f}\n"
            f"  {theme.get('description', '')}"
        )
    return "\n".join(lines) if lines else "(no themes)"


def trend_block(trends: list[dict], limit: int = 8) -> str:
    lines = [
        f"- {t.get('theme_name')}: {t.get('direction')} ({t.get('detail', '')})"
        for t in trends[:limit]
    ]
    return "\n".join(lines) if lines else "(no trend data)"
