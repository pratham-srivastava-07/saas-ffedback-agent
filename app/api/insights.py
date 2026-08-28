"""Cross-cutting views over stored feedback.

Themes answer "what is wrong". These answer "which part of the product", which
is the axis work is actually routed along: one theme can span several areas,
and one area collects many themes.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import session_factory_dep, workspace_dep
from app.schemas import FeatureAreasResponse
from app.store import repo

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/feature-areas", response_model=FeatureAreasResponse)
async def feature_areas(
    limit: int = Query(20, ge=1, le=100),
    workspace_id: str = Depends(workspace_dep),
    session_factory=Depends(session_factory_dep),
):
    """Every analysed item, grouped by the product area the model placed it in.

    The area is already recorded per item at analysis time. Until now it was
    only ever echoed back on individual rows, so the dimension was collected
    and then thrown away.
    """
    async with session_factory() as session:
        areas, total, unclassified = await repo.feature_area_rollup(
            session, workspace_id, limit=limit
        )
        themes = await repo.themes_for_feature_areas(
            session, [area["name"] for area in areas], workspace_id
        )

    for area in areas:
        area["themes"] = themes.get(area["name"], [])

    return {"areas": areas, "total_items": total, "unclassified": unclassified}
