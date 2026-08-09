"""Schema upgrades for databases created before workspace scoping existed.

No Alembic: the schema is small and SQLite-only, and a migration framework
would be more machinery than the problem deserves. But a `sentilytics.db` from
before tenancy must not silently corrupt, so missing columns are added and
every orphaned row is adopted into the default workspace.

``ALTER TABLE ... ADD COLUMN`` is the one schema change SQLite supports
cheaply, which is why every added column is nullable or carries a default.
"""

from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.store.models import (
    DEFAULT_WORKSPACE_ID,
    DEFAULT_WORKSPACE_NAME,
    Base,
)

logger = logging.getLogger(__name__)

_WORKSPACE_COLUMN = f"VARCHAR(36) NOT NULL DEFAULT '{DEFAULT_WORKSPACE_ID}'"

# Columns added after the initial release, per table.
_ADDITIONS: dict[str, list[tuple[str, str]]] = {
    "runs": [
        ("workspace_id", _WORKSPACE_COLUMN),
        ("trends", "JSON"),
        ("recommendations", "JSON"),
    ],
    "themes": [("workspace_id", _WORKSPACE_COLUMN)],
    "feedback_items": [
        ("workspace_id", _WORKSPACE_COLUMN),
        # 3D projection for the cluster explorer; null for rows analysed
        # before it existed.
        ("x", "FLOAT"),
        ("y", "FLOAT"),
        ("z", "FLOAT"),
    ],
    "theme_snapshots": [
        ("impact_score", "FLOAT NOT NULL DEFAULT 0.0"),
        ("is_new", "BOOLEAN NOT NULL DEFAULT 0"),
    ],
}


async def _table_columns(conn, table: str) -> set[str]:
    result = await conn.execute(text(f"PRAGMA table_info({table})"))
    return {row[1] for row in result.fetchall()}


async def upgrade(engine: AsyncEngine) -> None:
    """Create anything missing, then add columns to pre-existing tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    if engine.dialect.name != "sqlite":
        # The ALTER statements below are SQLite-shaped. Any other backend is
        # assumed to be managed properly rather than patched in place.
        logger.info("Skipping in-place column upgrade on %s", engine.dialect.name)
        await ensure_default_workspace(engine)
        return

    async with engine.begin() as conn:
        for table, columns in _ADDITIONS.items():
            existing = await _table_columns(conn, table)
            if not existing:
                # create_all just built it with the current shape.
                continue
            for name, ddl in columns:
                if name in existing:
                    continue
                logger.info("Upgrading %s: adding column %s", table, name)
                await conn.execute(
                    text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")
                )

    await ensure_default_workspace(engine)
    await _adopt_orphans(engine)


async def ensure_default_workspace(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        existing = await conn.execute(
            text("SELECT id FROM workspaces WHERE id = :id"),
            {"id": DEFAULT_WORKSPACE_ID},
        )
        if existing.first() is not None:
            return
        await conn.execute(
            text(
                "INSERT INTO workspaces (id, name, api_key_hash, created_at) "
                "VALUES (:id, :name, NULL, CURRENT_TIMESTAMP)"
            ),
            {"id": DEFAULT_WORKSPACE_ID, "name": DEFAULT_WORKSPACE_NAME},
        )
        logger.info("Created the default workspace")


async def _adopt_orphans(engine: AsyncEngine) -> None:
    """Point rows with a null or unknown workspace at the default one."""
    async with engine.begin() as conn:
        for table in ("runs", "themes", "feedback_items"):
            await conn.execute(
                text(
                    f"UPDATE {table} SET workspace_id = :default_id "
                    "WHERE workspace_id IS NULL OR workspace_id NOT IN "
                    "(SELECT id FROM workspaces)"
                ),
                {"default_id": DEFAULT_WORKSPACE_ID},
            )
