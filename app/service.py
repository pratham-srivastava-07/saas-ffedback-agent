"""Run orchestration: graph lifecycle, persistence, and SSE streaming."""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any, AsyncIterator

from app.graph.build import build_graph, initial_state, run_config
from app.llm import Runtime
from app.store import repo
from app.store.models import DEFAULT_WORKSPACE_ID

logger = logging.getLogger(__name__)

NODE_NAMES = {
    "normalize",
    "triage",
    "analyze_one",
    "embed",
    "cluster",
    "resolve_taxonomy",
    "name_themes",
    "prioritize",
    "detect_trends",
    "recommend",
    "critique",
    "summarize",
}

_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


# --------------------------------------------------------------------------
# Response shaping
# --------------------------------------------------------------------------


def build_response(state: dict[str, Any]) -> dict[str, Any]:
    themes = state.get("themes", [])

    theme_of_item: dict[str, str] = {}
    for theme in themes:
        for item_id in theme.get("item_ids", []):
            if theme.get("id"):
                theme_of_item[item_id] = theme["id"]

    analyzed = [
        {**item, "theme_id": theme_of_item.get(item["id"])}
        for item in state.get("analyzed", [])
    ]

    return {
        "run_id": state.get("run_id", ""),
        "summary": state.get("summary", ""),
        "analyzed": analyzed,
        "rejected": state.get("rejected", []),
        "themes": [
            {
                "id": theme.get("id") or "",
                "name": theme.get("name", ""),
                "description": theme.get("description", ""),
                "count": theme.get("count", 0),
                "is_new": bool(theme.get("is_new")),
                "impact_score": theme.get("impact_score", 0.0),
                "avg_severity": theme.get("avg_severity", 0.0),
                "sentiment_breakdown": theme.get("sentiment_breakdown", {}),
                "churn_risk_count": theme.get("churn_risk_count", 0),
                "sample_item_ids": theme.get("item_ids", [])[:5],
            }
            for theme in themes
        ],
        "trends": state.get("trends", []),
        "recommendations": state.get("recommendations", []),
        "revision_count": state.get("revision_count", 0),
    }


async def _persist(
    runtime: Runtime,
    run_id: str,
    state: dict[str, Any],
    workspace_id: str = DEFAULT_WORKSPACE_ID,
) -> None:
    if runtime.session_factory is None:
        return

    response = build_response(state)
    async with runtime.session_factory() as session:
        await repo.save_items(
            session, run_id, response["analyzed"], workspace_id=workspace_id
        )
        await repo.finish_run(
            session,
            run_id,
            status="completed",
            summary=state.get("summary", ""),
            item_count=len(response["analyzed"]),
            rejected_count=len(response["rejected"]),
            theme_count=len(response["themes"]),
            # Stored rather than recomputed later: "emerging" depends on
            # whether the theme was new at the time, which snapshots do not
            # record, so reconstruction would relabel first appearances.
            trends=response["trends"],
            recommendations=response["recommendations"],
        )


async def _mark_failed(runtime: Runtime, run_id: str, error: str) -> None:
    if runtime.session_factory is None:
        return
    async with runtime.session_factory() as session:
        await repo.finish_run(session, run_id, status="failed", error=error[:500])


async def _start_run(
    runtime: Runtime, workspace_id: str = DEFAULT_WORKSPACE_ID
) -> str:
    run_id = str(uuid.uuid4())
    if runtime.session_factory is not None:
        async with runtime.session_factory() as session:
            await repo.create_run(session, run_id, workspace_id=workspace_id)
    return run_id


# --------------------------------------------------------------------------
# Entry points
# --------------------------------------------------------------------------


async def analyze(
    runtime: Runtime,
    raw_feedback: list[dict],
    workspace_id: str = DEFAULT_WORKSPACE_ID,
) -> dict[str, Any]:
    run_id = await _start_run(runtime, workspace_id)
    try:
        final = await get_graph().ainvoke(
            initial_state(run_id, raw_feedback, workspace_id), run_config(runtime)
        )
    except Exception as exc:
        await _mark_failed(runtime, run_id, str(exc))
        raise

    await _persist(runtime, run_id, final, workspace_id)
    return build_response(final)


def _sse(event: str, payload: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(payload, default=str)}\n\n"


def _node_stats(node: str, output: Any) -> dict[str, Any]:
    """Small per-node result summary, so the UI can show more than a checkmark."""
    if not isinstance(output, dict):
        return {}
    keys = {
        "normalize": ("clean", "rejected"),
        "triage": ("clean", "rejected"),
        "embed": ("embeddings",),
        "cluster": ("clusters",),
        "resolve_taxonomy": ("themes",),
        "name_themes": ("themes",),
        "prioritize": ("themes",),
        "detect_trends": ("trends",),
        "recommend": ("recommendations",),
    }.get(node, ())

    stats = {key: len(output[key]) for key in keys if isinstance(output.get(key), (list, dict))}

    if node == "critique" and isinstance(output.get("critique"), dict):
        stats["approved"] = bool(output["critique"].get("approved"))
    return stats


async def analyze_stream(
    runtime: Runtime,
    raw_feedback: list[dict],
    workspace_id: str = DEFAULT_WORKSPACE_ID,
) -> AsyncIterator[str]:
    """Yield SSE frames as the graph executes.

    This is what turns the dashboard from a spinner into something that shows
    the pipeline actually working.
    """
    run_id = await _start_run(runtime, workspace_id)
    yield _sse("run_start", {"run_id": run_id, "nodes": sorted(NODE_NAMES)})

    root_id: str | None = None
    final_state: dict[str, Any] | None = None
    analyzed_done = 0

    try:
        async for event in get_graph().astream_events(
            initial_state(run_id, raw_feedback, workspace_id),
            run_config(runtime),
            version="v2",
        ):
            if root_id is None:
                root_id = event.get("run_id")

            kind = event.get("event")
            name = event.get("name")

            if kind == "on_chain_start" and name in NODE_NAMES:
                yield _sse("node_start", {"node": name})

            elif kind == "on_chain_end" and name in NODE_NAMES:
                payload: dict[str, Any] = {"node": name}
                if name == "analyze_one":
                    analyzed_done += 1
                    payload["completed"] = analyzed_done
                else:
                    payload["stats"] = _node_stats(
                        name, (event.get("data") or {}).get("output")
                    )
                yield _sse("node_end", payload)

            elif kind == "on_chain_end" and event.get("run_id") == root_id:
                final_state = (event.get("data") or {}).get("output")

    except Exception as exc:  # noqa: BLE001 - surface it to the client
        logger.exception("Streaming run %s failed", run_id)
        await _mark_failed(runtime, run_id, str(exc))
        yield _sse("error", {"run_id": run_id, "message": str(exc)[:500]})
        return

    if final_state is None:
        await _mark_failed(runtime, run_id, "graph produced no final state")
        yield _sse("error", {"run_id": run_id, "message": "No final state produced."})
        return

    await _persist(runtime, run_id, final_state, workspace_id)
    yield _sse("complete", build_response(final_state))
