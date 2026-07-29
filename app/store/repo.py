"""Query helpers. Nodes and API handlers talk to the database only through here."""

from __future__ import annotations

import uuid
from typing import Any, Sequence

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.store.models import FeedbackItem, Run, Theme, ThemeSnapshot


# --------------------------------------------------------------------------
# Runs
# --------------------------------------------------------------------------


async def create_run(session: AsyncSession, run_id: str | None = None) -> Run:
    run = Run(id=run_id or str(uuid.uuid4()), status="running")
    session.add(run)
    await session.commit()
    return run


async def finish_run(
    session: AsyncSession,
    run_id: str,
    *,
    status: str,
    summary: str | None = None,
    item_count: int = 0,
    rejected_count: int = 0,
    theme_count: int = 0,
    error: str | None = None,
) -> None:
    run = await session.get(Run, run_id)
    if run is None:
        return
    run.status = status
    run.summary = summary
    run.item_count = item_count
    run.rejected_count = rejected_count
    run.theme_count = theme_count
    run.error = error
    await session.commit()


async def get_run(session: AsyncSession, run_id: str) -> Run | None:
    return await session.get(Run, run_id)


async def list_runs(session: AsyncSession, limit: int = 50) -> Sequence[Run]:
    result = await session.execute(
        select(Run).order_by(desc(Run.created_at)).limit(limit)
    )
    return result.scalars().all()


# --------------------------------------------------------------------------
# Themes
# --------------------------------------------------------------------------


async def load_themes(session: AsyncSession) -> Sequence[Theme]:
    """All stored themes with their centroids, for similarity matching."""
    result = await session.execute(select(Theme))
    return result.scalars().all()


async def create_theme(
    session: AsyncSession,
    *,
    name: str,
    description: str,
    centroid: list[float],
    run_id: str,
    mentions: int,
) -> Theme:
    theme = Theme(
        id=str(uuid.uuid4()),
        name=name,
        description=description,
        centroid=centroid,
        first_seen_run=run_id,
        run_count=1,
        total_mentions=mentions,
    )
    session.add(theme)
    await session.commit()
    return theme


async def merge_into_theme(
    session: AsyncSession,
    theme: Theme,
    *,
    centroid: list[float],
    mentions: int,
) -> Theme:
    """Fold a matched cluster into an existing theme.

    The stored centroid becomes a running mean weighted by how many runs have
    contributed, so a single unusual batch cannot yank a theme's identity.
    """
    n = max(theme.run_count, 1)
    theme.centroid = [
        (old * n + new) / (n + 1) for old, new in zip(theme.centroid, centroid)
    ]
    theme.run_count = n + 1
    theme.total_mentions = (theme.total_mentions or 0) + mentions
    session.add(theme)
    await session.commit()
    return theme


async def list_themes_ranked(
    session: AsyncSession, limit: int = 100
) -> Sequence[Theme]:
    result = await session.execute(
        select(Theme).order_by(desc(Theme.total_mentions)).limit(limit)
    )
    return result.scalars().all()


# --------------------------------------------------------------------------
# Snapshots
# --------------------------------------------------------------------------


async def save_snapshot(
    session: AsyncSession,
    *,
    theme_id: str,
    run_id: str,
    count: int,
    share: float,
    avg_severity: float,
    positive: int,
    neutral: int,
    negative: int,
    churn_risk_count: int,
) -> None:
    session.add(
        ThemeSnapshot(
            theme_id=theme_id,
            run_id=run_id,
            count=count,
            share=share,
            avg_severity=avg_severity,
            positive=positive,
            neutral=neutral,
            negative=negative,
            churn_risk_count=churn_risk_count,
        )
    )
    await session.commit()


async def theme_history(
    session: AsyncSession,
    theme_id: str,
    *,
    exclude_run_id: str | None = None,
    limit: int = 10,
) -> Sequence[ThemeSnapshot]:
    """Trailing snapshots for a theme, newest first, excluding the current run."""
    stmt = select(ThemeSnapshot).where(ThemeSnapshot.theme_id == theme_id)
    if exclude_run_id:
        stmt = stmt.where(ThemeSnapshot.run_id != exclude_run_id)
    stmt = stmt.order_by(desc(ThemeSnapshot.created_at)).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


# --------------------------------------------------------------------------
# Items
# --------------------------------------------------------------------------


async def save_items(
    session: AsyncSession, run_id: str, items: list[dict[str, Any]]
) -> None:
    session.add_all(
        [
            FeedbackItem(
                run_id=run_id,
                external_id=str(item.get("id", "")),
                text=item.get("text", ""),
                user_type=item.get("user_type", "free"),
                source=item.get("source", "other"),
                sentiment=item.get("sentiment"),
                emotion=item.get("emotion"),
                intent=item.get("intent"),
                severity=item.get("severity"),
                feature_area=item.get("feature_area"),
                churn_risk=bool(item.get("churn_risk", False)),
                theme_id=item.get("theme_id"),
                status=item.get("status", "ok"),
                error=item.get("error"),
            )
            for item in items
        ]
    )
    await session.commit()


async def count_items_for_theme(session: AsyncSession, theme_id: str) -> int:
    result = await session.execute(
        select(func.count(FeedbackItem.id)).where(FeedbackItem.theme_id == theme_id)
    )
    return int(result.scalar_one())
