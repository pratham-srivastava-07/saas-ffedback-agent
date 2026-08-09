"""Tenancy: isolation between workspaces, and the upgrade from before it existed."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.graph.build import build_graph, initial_state
from app.store import repo
from app.store.migrate import upgrade
from app.store.models import DEFAULT_WORKSPACE_ID

GRAPH = build_graph()


async def test_two_workspaces_analysing_identical_feedback_stay_separate(
    runtime, config, feedback_batch, workspace, other_workspace
):
    """The whole point of tenancy. Identical input in two workspaces must
    produce two independent taxonomies — if these merged, one tenant's themes
    would absorb another's and both would be corrupted."""
    first = await GRAPH.ainvoke(
        initial_state("run-a", feedback_batch, workspace.id), config
    )
    second = await GRAPH.ainvoke(
        initial_state("run-b", feedback_batch, other_workspace.id), config
    )

    first_ids = {theme["id"] for theme in first["themes"]}
    second_ids = {theme["id"] for theme in second["themes"]}

    assert first_ids and second_ids
    assert not (first_ids & second_ids), "themes leaked across workspaces"

    # Each workspace sees only its own.
    async with runtime.session_factory() as session:
        mine = await repo.load_themes(session, workspace.id)
        theirs = await repo.load_themes(session, other_workspace.id)

    assert {theme.id for theme in mine} == first_ids
    assert {theme.id for theme in theirs} == second_ids

    # Both are first-time appearances, so neither inherited the other's run
    # history and neither reports a trend built from foreign data.
    assert all(theme["is_new"] for theme in second["themes"])


async def test_trend_history_does_not_bleed_between_workspaces(
    runtime, config, feedback_batch, workspace, other_workspace
):
    """Workspace A runs the same batch four times; B runs it once. B must
    still report no usable history rather than inheriting A's baseline."""
    for index in range(4):
        await GRAPH.ainvoke(
            initial_state(f"a-{index}", feedback_batch, workspace.id), config
        )

    second = await GRAPH.ainvoke(
        initial_state("b-0", feedback_batch, other_workspace.id), config
    )

    directions = {trend["direction"] for trend in second["trends"]}
    assert directions <= {"emerging", "insufficient_history"}, (
        f"workspace B inherited history from A: {second['trends']}"
    )


async def test_runs_and_items_are_scoped(
    runtime, config, feedback_batch, workspace, other_workspace
):
    from app import service

    await service.analyze(runtime, feedback_batch, workspace.id)

    async with runtime.session_factory() as session:
        mine = await repo.list_runs(session, workspace_id=workspace.id)
        theirs = await repo.list_runs(session, workspace_id=other_workspace.id)

    assert len(mine) == 1
    assert theirs == []

    # A run id from another workspace must not resolve.
    async with runtime.session_factory() as session:
        leaked = await repo.get_run(
            session, mine[0].id, workspace_id=other_workspace.id
        )
    assert leaked is None


# --------------------------------------------------------------------------
# Migration from the pre-tenancy schema
# --------------------------------------------------------------------------

_OLD_SCHEMA = [
    """CREATE TABLE runs (
        id VARCHAR(36) NOT NULL PRIMARY KEY,
        created_at DATETIME,
        status VARCHAR(16),
        item_count INTEGER,
        rejected_count INTEGER,
        theme_count INTEGER,
        summary TEXT,
        error TEXT
    )""",
    """CREATE TABLE themes (
        id VARCHAR(36) NOT NULL PRIMARY KEY,
        name VARCHAR(200),
        description TEXT,
        centroid JSON,
        first_seen_run VARCHAR(36),
        run_count INTEGER,
        total_mentions INTEGER,
        created_at DATETIME,
        updated_at DATETIME
    )""",
    """CREATE TABLE feedback_items (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        run_id VARCHAR(36),
        external_id VARCHAR(128),
        text TEXT,
        user_type VARCHAR(16),
        source VARCHAR(32),
        sentiment VARCHAR(16),
        emotion VARCHAR(16),
        intent VARCHAR(32),
        severity INTEGER,
        feature_area VARCHAR(120),
        churn_risk BOOLEAN,
        theme_id VARCHAR(36),
        status VARCHAR(16),
        error TEXT
    )""",
    """CREATE TABLE theme_snapshots (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        theme_id VARCHAR(36),
        run_id VARCHAR(36),
        created_at DATETIME,
        count INTEGER,
        share FLOAT,
        avg_severity FLOAT,
        positive INTEGER,
        neutral INTEGER,
        negative INTEGER,
        churn_risk_count INTEGER
    )""",
]


async def test_pre_tenancy_database_is_upgraded_not_corrupted(tmp_path):
    """A `sentilytics.db` written before workspaces existed must survive the
    upgrade with its data intact and adopted into the default workspace."""
    db_path = tmp_path / "legacy.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")

    async with engine.begin() as conn:
        for statement in _OLD_SCHEMA:
            await conn.execute(text(statement))
        await conn.execute(
            text(
                "INSERT INTO runs (id, status, item_count) "
                "VALUES ('old-run', 'completed', 3)"
            )
        )
        await conn.execute(
            text(
                "INSERT INTO themes (id, name, description, centroid, "
                "first_seen_run, run_count, total_mentions) VALUES "
                "('old-theme', 'Signup issues', '', '[1.0]', 'old-run', 2, 5)"
            )
        )
        await conn.execute(
            text(
                "INSERT INTO feedback_items (run_id, external_id, text, "
                "user_type, source, theme_id, status) VALUES "
                "('old-run', 'x1', 'signup broken', 'paid', 'support', "
                "'old-theme', 'ok')"
            )
        )

    await upgrade(engine)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        # Pre-existing rows landed in the default workspace.
        themes = await repo.load_themes(session, DEFAULT_WORKSPACE_ID)
        runs = await repo.list_runs(session, workspace_id=DEFAULT_WORKSPACE_ID)
        items = await repo.items_for_theme(
            session, "old-theme", workspace_id=DEFAULT_WORKSPACE_ID
        )

    assert [theme.id for theme in themes] == ["old-theme"]
    assert themes[0].total_mentions == 5, "existing data was not preserved"
    assert [run.id for run in runs] == ["old-run"]
    assert [item.text for item in items] == ["signup broken"]

    await engine.dispose()


async def test_upgrade_is_idempotent(tmp_path):
    """Startup runs it every boot, so a second pass must be a no-op."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/twice.db")
    await upgrade(engine)
    await upgrade(engine)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        workspaces = await repo.list_workspaces(session)

    assert [w.id for w in workspaces] == [DEFAULT_WORKSPACE_ID]
    await engine.dispose()
