"""Graph construction.

Three things here are the reason this is a LangGraph application rather than a
linear chain:

* ``triage`` drives a **conditional edge** — a batch of pure noise skips the
  entire pipeline and goes straight to the summary.
* ``analyze_one`` is reached by **Send fan-out** — one concurrent branch per
  item, joined back through the ``operator.add`` reducer on ``analyzed``.
* ``recommend`` and ``critique`` form a **bounded cycle** — recommendations
  that the critic finds unsupported are sent back for another pass, at most
  ``max_critique_revisions`` times.
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from app.graph.nodes import (
    analyze_one,
    cluster,
    critique,
    detect_trends,
    embed,
    name_themes,
    normalize,
    prioritize,
    recommend,
    resolve_taxonomy,
    summarize,
    triage,
)
from app.graph.state import AnalysisState
from app.llm import Runtime


def fan_out_to_analysis(state: AnalysisState) -> list[Send] | str:
    """Map step: one concurrent branch per surviving item.

    Returning a node name instead short-circuits the pipeline when triage
    rejected everything — there is nothing to analyse, cluster or recommend.
    """
    items = state.get("clean", [])
    if not items:
        return "summarize"
    return [Send("analyze_one", {"item": item}) for item in items]


def after_critique(state: AnalysisState, config=None) -> str:
    """Close the cycle, or bound it."""
    max_revisions = 2
    try:
        from app.llm import get_runtime

        max_revisions = get_runtime(config).settings.max_critique_revisions
    except Exception:  # noqa: BLE001 - fall back to the documented default
        pass

    verdict = state.get("critique") or {}
    if verdict.get("approved"):
        return "summarize"
    if state.get("revision_count", 0) >= max_revisions:
        return "summarize"
    return "recommend"


def build_graph():
    workflow = StateGraph(AnalysisState)

    workflow.add_node("normalize", normalize)
    workflow.add_node("triage", triage)
    workflow.add_node("analyze_one", analyze_one)
    workflow.add_node("embed", embed)
    workflow.add_node("cluster", cluster)
    workflow.add_node("resolve_taxonomy", resolve_taxonomy)
    workflow.add_node("name_themes", name_themes)
    workflow.add_node("prioritize", prioritize)
    workflow.add_node("detect_trends", detect_trends)
    workflow.add_node("recommend", recommend)
    workflow.add_node("critique", critique)
    workflow.add_node("summarize", summarize)

    workflow.add_edge(START, "normalize")
    workflow.add_edge("normalize", "triage")

    workflow.add_conditional_edges(
        "triage", fan_out_to_analysis, ["analyze_one", "summarize"]
    )

    # Joins after every fan-out branch finishes.
    workflow.add_edge("analyze_one", "embed")
    workflow.add_edge("embed", "cluster")
    workflow.add_edge("cluster", "resolve_taxonomy")

    # Naming runs after reconciliation so we spend LLM calls only on clusters
    # we have genuinely never seen; recurring themes keep their stored name.
    workflow.add_edge("resolve_taxonomy", "name_themes")
    workflow.add_edge("name_themes", "prioritize")
    workflow.add_edge("prioritize", "detect_trends")
    workflow.add_edge("detect_trends", "recommend")
    workflow.add_edge("recommend", "critique")

    workflow.add_conditional_edges(
        "critique", after_critique, ["recommend", "summarize"]
    )
    workflow.add_edge("summarize", END)

    return workflow.compile()


def initial_state(run_id: str, raw_feedback: list[dict]) -> AnalysisState:
    return {
        "run_id": run_id,
        "raw": raw_feedback,
        "clean": [],
        "rejected": [],
        "analyzed": [],
        "embeddings": {},
        "clusters": [],
        "themes": [],
        "trends": [],
        "recommendations": [],
        "critique": None,
        "revision_count": 0,
        "summary": "",
    }


def run_config(runtime: Runtime) -> dict:
    return {
        "configurable": {"runtime": runtime},
        # Headroom for the bounded critique cycle without letting a runaway
        # loop spin forever.
        "recursion_limit": 50,
    }
