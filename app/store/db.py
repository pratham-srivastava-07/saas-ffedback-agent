"""Async SQLAlchemy engine and session factory.

SQLite keeps the project runnable from a fresh clone with no Docker and no
cloud account, which matters for something meant to be handed to someone else
and run in under a minute.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings
from app.store.models import Base

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker | None = None


def get_engine(database_url: str | None = None) -> AsyncEngine:
    global _engine
    if _engine is None:
        url = database_url or get_settings().database_url
        _engine = create_async_engine(url, future=True)
    return _engine


def get_session_factory(database_url: str | None = None) -> async_sessionmaker:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(database_url), expire_on_commit=False
        )
    return _session_factory


async def init_db(engine: AsyncEngine | None = None) -> None:
    engine = engine or get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def reset_state() -> None:
    """Drop cached engine/session factory. Used by tests."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None
