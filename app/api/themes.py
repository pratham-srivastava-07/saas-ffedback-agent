"""Theme taxonomy endpoints — the accumulated view across every run."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.auth import workspace_dep
from app.api.deps import session_factory_dep
from app.store import repo

router = APIRouter(prefix="/themes", tags=["themes"])


@router.get("")
async def list_themes(
    limit: int = 100,
    session_factory=Depends(session_factory_dep),
    workspace_id: str = Depends(workspace_dep),
):
    async with session_factory() as session:
        themes = await repo.list_themes_ranked(
            session, workspace_id=workspace_id, limit=limit
        )
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
    limit: int = 20,
    history: int = 10,
    session_factory=Depends(session_factory_dep),
    workspace_id: str = Depends(workspace_dep),
):
    """Per-theme history, for sparklines and trajectory display."""
    async with session_factory() as session:
        themes = await repo.list_themes_ranked(
            session, workspace_id=workspace_id, limit=limit
        )
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


@router.get("/{theme_id}/items")
async def theme_items(
    theme_id: str,
    limit: int = 50,
    offset: int = 0,
    session_factory=Depends(session_factory_dep),
    workspace_id: str = Depends(workspace_dep),
):
    """The evidence behind a theme.

    The product promises a ranked list "with the evidence attached"; without
    this endpoint you could see that 34 people complained and never read what
    any of them said.
    """
    limit = max(1, min(limit, 200))

    async with session_factory() as session:
        theme = await repo.get_theme(session, theme_id, workspace_id=workspace_id)
        if theme is None:
            raise HTTPException(status_code=404, detail="Theme not found")

        total = await repo.count_items_for_theme(
            session, theme_id, workspace_id=workspace_id
        )
        items = await repo.items_for_theme(
            session,
            theme_id,
            workspace_id=workspace_id,
            limit=limit,
            offset=offset,
        )

        return {
            "theme": {
                "id": theme.id,
                "name": theme.name,
                "description": theme.description,
                "total_mentions": theme.total_mentions,
                "run_count": theme.run_count,
            },
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": [_serialize_item(item) for item in items],
        }


def _serialize_item(item) -> dict:
    return {
        "id": item.external_id,
        "run_id": item.run_id,
        "text": item.text,
        "user_type": item.user_type,
        "source": item.source,
        "sentiment": item.sentiment,
        "emotion": item.emotion,
        "intent": item.intent,
        "severity": item.severity,
        "feature_area": item.feature_area,
        "churn_risk": item.churn_risk,
        "theme_id": item.theme_id,
        "status": item.status,
    }
