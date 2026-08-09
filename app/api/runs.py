"""Run history endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.auth import workspace_dep
from app.api.deps import session_factory_dep
from app.api.themes import _serialize_item
from app.store import repo

router = APIRouter(prefix="/runs", tags=["runs"])


def _serialize(run) -> dict:
    return {
        "id": run.id,
        "created_at": run.created_at.isoformat(),
        "status": run.status,
        "item_count": run.item_count,
        "rejected_count": run.rejected_count,
        "theme_count": run.theme_count,
        "summary": run.summary,
        "error": run.error,
    }


@router.get("")
async def list_runs(
    limit: int = 50,
    session_factory=Depends(session_factory_dep),
    workspace_id: str = Depends(workspace_dep),
):
    async with session_factory() as session:
        runs = await repo.list_runs(session, workspace_id=workspace_id, limit=limit)
        return [_serialize(run) for run in runs]


@router.get("/{run_id}")
async def get_run(
    run_id: str,
    session_factory=Depends(session_factory_dep),
    workspace_id: str = Depends(workspace_dep),
):
    async with session_factory() as session:
        run = await repo.get_run(session, run_id, workspace_id=workspace_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")
        return _serialize(run)


@router.get("/{run_id}/result")
async def get_run_result(
    run_id: str,
    session_factory=Depends(session_factory_dep),
    workspace_id: str = Depends(workspace_dep),
):
    """Rebuild a past run's full result.

    Kept separate from ``GET /runs/{id}`` so listing history stays cheap —
    this joins every item and snapshot for the run.

    Themes come from that run's snapshots rather than the live theme rows, so
    the counts and impact scores are the ones the run actually produced, not
    what the theme has accumulated since.
    """
    async with session_factory() as session:
        run = await repo.get_run(session, run_id, workspace_id=workspace_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")

        items = await repo.items_for_run(session, run_id, workspace_id=workspace_id)
        snapshots = await repo.snapshots_for_run(session, run_id)

        themes = [
            {
                "id": theme.id,
                "name": theme.name,
                "description": theme.description,
                "count": snapshot.count,
                "share": round(snapshot.share, 4),
                "is_new": snapshot.is_new,
                "impact_score": snapshot.impact_score,
                "avg_severity": round(snapshot.avg_severity, 2),
                "sentiment_breakdown": {
                    "positive": snapshot.positive,
                    "neutral": snapshot.neutral,
                    "negative": snapshot.negative,
                },
                "churn_risk_count": snapshot.churn_risk_count,
            }
            for snapshot, theme in snapshots
        ]

        return {
            **_serialize(run),
            "themes": themes,
            # Persisted at write time: "emerging" depends on whether a theme
            # was new during that run, which snapshots alone cannot recover.
            "trends": run.trends or [],
            "recommendations": run.recommendations or [],
            "analyzed": [_serialize_item(item) for item in items],
        }
