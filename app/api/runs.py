"""Run history endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import session_factory_dep
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
async def list_runs(limit: int = 50, session_factory=Depends(session_factory_dep)):
    async with session_factory() as session:
        return [_serialize(run) for run in await repo.list_runs(session, limit=limit)]


@router.get("/{run_id}")
async def get_run(run_id: str, session_factory=Depends(session_factory_dep)):
    async with session_factory() as session:
        run = await repo.get_run(session, run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")
        return _serialize(run)
