"""Query helpers. Nodes and API handlers talk to the database only through here.

Every read that could span tenants takes a ``workspace_id``. That is not
defensive politeness: taxonomy matching compares centroids against *stored*
themes, so an unscoped read would let one tenant's clusters merge into
another's themes and quietly corrupt both taxonomies.
"""

from __future__ import annotations

import uuid
from datetime import timedelta
from typing import Any, Sequence

from sqlalchemy import case, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.store.models import (
    DEFAULT_WORKSPACE_ID,
    FeedbackItem,
    Run,
    Theme,
    ThemeSnapshot,
    User,
    Workspace,
    _utcnow,
)


# --------------------------------------------------------------------------
# Workspaces
# --------------------------------------------------------------------------


async def create_workspace(
    session: AsyncSession,
    *,
    name: str,
    api_key_hash: str | None = None,
    workspace_id: str | None = None,
) -> Workspace:
    workspace = Workspace(
        id=workspace_id or str(uuid.uuid4()),
        name=name,
        api_key_hash=api_key_hash,
    )
    session.add(workspace)
    await session.commit()
    return workspace


async def get_workspace(
    session: AsyncSession, workspace_id: str
) -> Workspace | None:
    return await session.get(Workspace, workspace_id)


async def workspace_by_key_hash(
    session: AsyncSession, api_key_hash: str
) -> Workspace | None:
    result = await session.execute(
        select(Workspace).where(Workspace.api_key_hash == api_key_hash)
    )
    return result.scalars().first()


async def list_workspaces(session: AsyncSession) -> Sequence[Workspace]:
    result = await session.execute(select(Workspace).order_by(Workspace.created_at))
    return result.scalars().all()


# --------------------------------------------------------------------------
# Users
# --------------------------------------------------------------------------


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(
        select(User).where(User.email == email.strip().lower())
    )
    return result.scalars().first()


async def get_user_for_workspace(
    session: AsyncSession, workspace_id: str
) -> User | None:
    result = await session.execute(
        select(User).where(User.workspace_id == workspace_id)
    )
    return result.scalars().first()


async def create_user_with_workspace(
    session: AsyncSession,
    *,
    email: str,
    password_hash: str,
    salt: str,
    workspace_name: str,
    api_key_hash: str,
) -> tuple[User, Workspace]:
    """Signup, in one transaction.

    A user without a workspace, or a workspace without its key, would both be
    unusable accounts, so all three rows commit together or not at all.
    """
    workspace = Workspace(
        id=str(uuid.uuid4()), name=workspace_name, api_key_hash=api_key_hash
    )
    user = User(
        id=str(uuid.uuid4()),
        email=email.strip().lower(),
        password_hash=password_hash,
        salt=salt,
        workspace_id=workspace.id,
    )
    session.add_all([workspace, user])
    await session.commit()
    return user, workspace


# --------------------------------------------------------------------------
# Runs
# --------------------------------------------------------------------------


async def create_run(
    session: AsyncSession,
    run_id: str | None = None,
    workspace_id: str = DEFAULT_WORKSPACE_ID,
) -> Run:
    run = Run(
        id=run_id or str(uuid.uuid4()),
        workspace_id=workspace_id,
        status="running",
    )
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
    trends: list | None = None,
    recommendations: list | None = None,
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
    if trends is not None:
        run.trends = trends
    if recommendations is not None:
        run.recommendations = recommendations
    await session.commit()


async def get_run(
    session: AsyncSession, run_id: str, workspace_id: str = DEFAULT_WORKSPACE_ID
) -> Run | None:
    run = await session.get(Run, run_id)
    if run is None or run.workspace_id != workspace_id:
        return None
    return run


async def list_runs(
    session: AsyncSession,
    workspace_id: str = DEFAULT_WORKSPACE_ID,
    limit: int = 50,
) -> Sequence[Run]:
    result = await session.execute(
        select(Run)
        .where(Run.workspace_id == workspace_id)
        .order_by(desc(Run.created_at))
        .limit(limit)
    )
    return result.scalars().all()


async def reap_stale_runs(session: AsyncSession, older_than_minutes: int) -> int:
    """Fail runs left ``running`` by a crash.

    Nothing else ever clears them, so without this they accumulate forever and
    every run list is polluted by ghosts.
    """
    cutoff = _utcnow() - timedelta(minutes=older_than_minutes)
    result = await session.execute(
        update(Run)
        .where(Run.status == "running", Run.created_at < cutoff)
        .values(status="failed", error="Abandoned: process exited mid-run.")
        # Rows already loaded in this session are re-read rather than
        # re-evaluated in Python, which avoids comparing datetimes in memory.
        .execution_options(synchronize_session="fetch")
    )
    await session.commit()
    return int(result.rowcount or 0)


# --------------------------------------------------------------------------
# Themes
# --------------------------------------------------------------------------


async def load_themes(
    session: AsyncSession, workspace_id: str = DEFAULT_WORKSPACE_ID
) -> Sequence[Theme]:
    """This workspace's themes with their centroids, for similarity matching."""
    result = await session.execute(
        select(Theme).where(Theme.workspace_id == workspace_id)
    )
    return result.scalars().all()


async def get_theme(
    session: AsyncSession, theme_id: str, workspace_id: str = DEFAULT_WORKSPACE_ID
) -> Theme | None:
    theme = await session.get(Theme, theme_id)
    if theme is None or theme.workspace_id != workspace_id:
        return None
    return theme


async def create_theme(
    session: AsyncSession,
    *,
    name: str,
    description: str,
    centroid: list[float],
    run_id: str,
    mentions: int,
    workspace_id: str = DEFAULT_WORKSPACE_ID,
) -> Theme:
    theme = Theme(
        id=str(uuid.uuid4()),
        workspace_id=workspace_id,
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
    session: AsyncSession,
    workspace_id: str = DEFAULT_WORKSPACE_ID,
    limit: int = 100,
) -> Sequence[Theme]:
    result = await session.execute(
        select(Theme)
        .where(Theme.workspace_id == workspace_id)
        .order_by(desc(Theme.total_mentions))
        .limit(limit)
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
    impact_score: float = 0.0,
    is_new: bool = False,
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
            impact_score=impact_score,
            is_new=is_new,
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
    """Trailing snapshots for a theme, newest first, excluding the current run.

    Scoping is inherited: the caller resolves the theme within a workspace
    before asking for its history.
    """
    stmt = select(ThemeSnapshot).where(ThemeSnapshot.theme_id == theme_id)
    if exclude_run_id:
        stmt = stmt.where(ThemeSnapshot.run_id != exclude_run_id)
    stmt = stmt.order_by(desc(ThemeSnapshot.created_at)).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


async def snapshots_for_run(
    session: AsyncSession, run_id: str
) -> Sequence[tuple[ThemeSnapshot, Theme]]:
    """Every theme's standing in one run, for rebuilding a past result."""
    result = await session.execute(
        select(ThemeSnapshot, Theme)
        .join(Theme, Theme.id == ThemeSnapshot.theme_id)
        .where(ThemeSnapshot.run_id == run_id)
        .order_by(desc(ThemeSnapshot.impact_score))
    )
    return [(row[0], row[1]) for row in result.all()]


# --------------------------------------------------------------------------
# Items
# --------------------------------------------------------------------------


async def save_items(
    session: AsyncSession,
    run_id: str,
    items: list[dict[str, Any]],
    workspace_id: str = DEFAULT_WORKSPACE_ID,
) -> None:
    session.add_all(
        [
            FeedbackItem(
                workspace_id=workspace_id,
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
                x=item.get("x"),
                y=item.get("y"),
                z=item.get("z"),
            )
            for item in items
        ]
    )
    await session.commit()


async def items_for_theme(
    session: AsyncSession,
    theme_id: str,
    *,
    workspace_id: str = DEFAULT_WORKSPACE_ID,
    limit: int = 50,
    offset: int = 0,
) -> Sequence[FeedbackItem]:
    """The evidence behind a theme — the whole point of "with the evidence"."""
    result = await session.execute(
        select(FeedbackItem)
        .where(
            FeedbackItem.theme_id == theme_id,
            FeedbackItem.workspace_id == workspace_id,
        )
        .order_by(desc(FeedbackItem.severity), FeedbackItem.id)
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()


async def items_for_run(
    session: AsyncSession, run_id: str, workspace_id: str = DEFAULT_WORKSPACE_ID
) -> Sequence[FeedbackItem]:
    result = await session.execute(
        select(FeedbackItem)
        .where(
            FeedbackItem.run_id == run_id,
            FeedbackItem.workspace_id == workspace_id,
        )
        .order_by(FeedbackItem.id)
    )
    return result.scalars().all()


async def count_items_for_theme(
    session: AsyncSession, theme_id: str, workspace_id: str = DEFAULT_WORKSPACE_ID
) -> int:
    result = await session.execute(
        select(func.count(FeedbackItem.id)).where(
            FeedbackItem.theme_id == theme_id,
            FeedbackItem.workspace_id == workspace_id,
        )
    )
    return int(result.scalar_one())


# --------------------------------------------------------------------------
# Feature areas
# --------------------------------------------------------------------------

# The analyser writes "unknown" when it cannot place an item in a product area.
# That bucket is reported separately rather than ranked alongside real areas:
# it is usually the largest single group, and letting it sit at the top of a
# list of product areas would misrepresent both its size and its meaning.
UNCLASSIFIED_AREA = "unknown"


async def feature_area_rollup(
    session: AsyncSession,
    workspace_id: str = DEFAULT_WORKSPACE_ID,
    limit: int = 20,
) -> tuple[list[dict[str, Any]], int, int]:
    """Aggregate every analysed item by the product area it touches.

    A second cut of the same data as themes. A theme is one problem; an area
    is the part of the product that owns it, so one theme can span areas and
    one area collects many themes. Product managers route work by area.

    Returns the ranked areas, the total analysed count, and how many items
    could not be placed.
    """
    stmt = (
        select(
            FeedbackItem.feature_area.label("name"),
            func.count(FeedbackItem.id).label("mentions"),
            func.avg(FeedbackItem.severity).label("avg_severity"),
            func.sum(
                case((FeedbackItem.churn_risk.is_(True), 1), else_=0)
            ).label("churn_risk_count"),
            func.sum(
                case((FeedbackItem.sentiment == "positive", 1), else_=0)
            ).label("positive"),
            func.sum(
                case((FeedbackItem.sentiment == "neutral", 1), else_=0)
            ).label("neutral"),
            func.sum(
                case((FeedbackItem.sentiment == "negative", 1), else_=0)
            ).label("negative"),
            func.max(FeedbackItem.id).label("latest_row"),
        )
        # Failed items carry placeholder analysis, so counting them would
        # inflate "unknown" with rows the model never actually read.
        .where(
            FeedbackItem.workspace_id == workspace_id,
            FeedbackItem.status == "ok",
            FeedbackItem.feature_area.is_not(None),
        )
        .group_by(FeedbackItem.feature_area)
        .order_by(desc("mentions"))
    )

    rows = (await session.execute(stmt)).all()

    total = sum(int(row.mentions) for row in rows)
    unclassified = sum(
        int(row.mentions) for row in rows if row.name == UNCLASSIFIED_AREA
    )

    areas = [
        {
            "name": row.name,
            "mentions": int(row.mentions),
            "share": (int(row.mentions) / total) if total else 0.0,
            "avg_severity": round(float(row.avg_severity or 0), 2),
            "churn_risk_count": int(row.churn_risk_count or 0),
            "sentiment": {
                "positive": int(row.positive or 0),
                "neutral": int(row.neutral or 0),
                "negative": int(row.negative or 0),
            },
        }
        for row in rows
        if row.name != UNCLASSIFIED_AREA
    ][:limit]

    return areas, total, unclassified


async def themes_for_feature_areas(
    session: AsyncSession,
    area_names: Sequence[str],
    workspace_id: str = DEFAULT_WORKSPACE_ID,
    per_area: int = 3,
) -> dict[str, list[dict[str, Any]]]:
    """The themes appearing in each area, most mentioned first.

    One grouped query for every area rather than one query per area, so the
    endpoint cost does not grow with the number of areas on the page.
    """
    if not area_names:
        return {}

    stmt = (
        select(
            FeedbackItem.feature_area.label("area"),
            Theme.id.label("theme_id"),
            Theme.name.label("theme_name"),
            func.count(FeedbackItem.id).label("mentions"),
        )
        .join(Theme, Theme.id == FeedbackItem.theme_id)
        .where(
            FeedbackItem.workspace_id == workspace_id,
            FeedbackItem.status == "ok",
            FeedbackItem.feature_area.in_(list(area_names)),
        )
        .group_by(FeedbackItem.feature_area, Theme.id, Theme.name)
        .order_by(desc("mentions"))
    )

    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in (await session.execute(stmt)).all():
        bucket = grouped.setdefault(row.area, [])
        if len(bucket) < per_area:
            bucket.append(
                {
                    "id": row.theme_id,
                    "name": row.theme_name,
                    "mentions": int(row.mentions),
                }
            )
    return grouped
