"""Theme taxonomy endpoints — the accumulated view across every run."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import session_factory_dep
from app.store import repo

router = APIRouter(prefix="/themes", tags=["themes"])


@router.get("")
async def list_themes(limit: int = 100, session_factory=Depends(session_factory_dep)):
    async with session_factory() as session:
        themes = await repo.list_themes_ranked(session, limit=limit)
        return [
            {
                "id": theme.id,
                "name": theme.name,
                "description": theme.description,
                "total_mentions": theme.total_mentions,
                "run_count": theme.run_count,
                "first_seen_run": theme.first_seen_run,
                "created_at": theme.created_at.isoformat(),
                "updated_at": theme.updated_at.isoformat(),
            }
            for theme in themes
        ]


@router.get("/trends")
async def theme_trends(
    limit: int = 20, history: int = 10, session_factory=Depends(session_factory_dep)
):
    """Per-theme history, for sparklines and trajectory display."""
    async with session_factory() as session:
        themes = await repo.list_themes_ranked(session, limit=limit)
        out = []
        for theme in themes:
            snapshots = await repo.theme_history(session, theme.id, limit=history)
            ordered = list(reversed(snapshots))
            out.append(
                {
                    "id": theme.id,
                    "name": theme.name,
                    "total_mentions": theme.total_mentions,
                    "run_count": theme.run_count,
                    "history": [
                        {
                            "run_id": snapshot.run_id,
                            "at": snapshot.created_at.isoformat(),
                            "count": snapshot.count,
                            "share": round(snapshot.share, 4),
                            "avg_severity": round(snapshot.avg_severity, 2),
                        }
                        for snapshot in ordered
                    ],
                }
            )
        return out
