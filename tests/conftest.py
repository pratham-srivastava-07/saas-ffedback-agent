from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Settings
from app.llm import Runtime
from app.store.models import Base
from tests.fakes import FakeChat, FakeEmbeddings


@pytest.fixture
def settings() -> Settings:
    return Settings(
        groq_api_key="test",
        google_api_key="test",
        min_snapshots_for_trend=3,
        theme_merge_threshold=0.82,
        cluster_distance_threshold=0.35,
    )


@pytest_asyncio.fixture
async def session_factory(tmp_path):
    """File-backed SQLite. An in-memory URL would hand each new connection a
    fresh empty database, which silently breaks anything spanning sessions."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/test.db")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


@pytest.fixture
def chat() -> FakeChat:
    return FakeChat(overrides={}, fail_on=set(), calls=[])


@pytest_asyncio.fixture
async def runtime(settings, session_factory, chat) -> Runtime:
    return Runtime(
        chat=chat,
        embeddings=FakeEmbeddings(),
        settings=settings,
        session_factory=session_factory,
    )


@pytest.fixture
def config(runtime) -> dict:
    return {"configurable": {"runtime": runtime}, "recursion_limit": 50}


@pytest.fixture
def feedback_batch() -> list[dict]:
    return [
        {"id": "1", "text": "Signup is broken, OAuth fails every time", "user_type": "enterprise", "source": "support"},
        {"id": "2", "text": "Cannot complete signup, the flow crashes", "user_type": "paid", "source": "support"},
        {"id": "3", "text": "Signup fails after email confirmation", "user_type": "free", "source": "review"},
        {"id": "4", "text": "Billing page shows the wrong amount", "user_type": "paid", "source": "support"},
        {"id": "5", "text": "I love the new export feature, thanks", "user_type": "free", "source": "nps"},
    ]
