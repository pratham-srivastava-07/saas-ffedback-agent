from __future__ import annotations

from dataclasses import dataclass

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.auth import generate_api_key, hash_api_key
from app.config import Settings
from app.llm import Runtime
from app.store import repo
from app.store.migrate import upgrade
from app.store.models import DEFAULT_WORKSPACE_ID
from tests.fakes import FakeChat, FakeEmbeddings


@pytest.fixture
def settings() -> Settings:
    return Settings(
        groq_api_key="test",
        google_api_key="test",
        min_snapshots_for_trend=3,
        theme_merge_threshold=0.82,
        cluster_distance_threshold=0.35,
        # High enough that ordinary tests never trip it; the rate-limit tests
        # build their own limiter with a tiny capacity.
        rate_limit_requests=10_000,
    )


@pytest_asyncio.fixture
async def session_factory(tmp_path):
    """File-backed SQLite. An in-memory URL would hand each new connection a
    fresh empty database, which silently breaks anything spanning sessions.

    Built through the real startup path rather than ``create_all`` so the
    default workspace exists — otherwise the tests only pass because SQLite
    leaves foreign-key enforcement off by default.
    """
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/test.db")
    await upgrade(engine)
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


@dataclass
class WorkspaceHandle:
    id: str
    api_key: str


@pytest_asyncio.fixture
async def workspace(session_factory) -> WorkspaceHandle:
    """A real workspace with a real key, so tests exercise the auth path."""
    api_key = generate_api_key()
    async with session_factory() as session:
        created = await repo.create_workspace(
            session, name="Test workspace", api_key_hash=hash_api_key(api_key)
        )
    return WorkspaceHandle(id=created.id, api_key=api_key)


@pytest_asyncio.fixture
async def other_workspace(session_factory) -> WorkspaceHandle:
    api_key = generate_api_key()
    async with session_factory() as session:
        created = await repo.create_workspace(
            session, name="Other workspace", api_key_hash=hash_api_key(api_key)
        )
    return WorkspaceHandle(id=created.id, api_key=api_key)


@pytest_asyncio.fixture
async def client(runtime, session_factory, settings, workspace):
    """Authenticated API client.

    Bypasses the lifespan, which would build a real runtime and demand
    provider keys. Lives here rather than in one test module because several
    now drive the API.
    """
    from httpx import ASGITransport, AsyncClient

    from app.api.ratelimit import RateLimiter
    from app.main import app as fastapi_app

    fastapi_app.state.runtime = runtime
    fastapi_app.state.session_factory = session_factory
    fastapi_app.state.settings = settings
    fastapi_app.state.rate_limiter = RateLimiter(
        capacity=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://test",
        headers={"X-API-Key": workspace.api_key},
    ) as async_client:
        yield async_client


@pytest.fixture
def feedback_batch() -> list[dict]:
    return [
        {"id": "1", "text": "Signup is broken, OAuth fails every time", "user_type": "enterprise", "source": "support"},
        {"id": "2", "text": "Cannot complete signup, the flow crashes", "user_type": "paid", "source": "support"},
        {"id": "3", "text": "Signup fails after email confirmation", "user_type": "free", "source": "review"},
        {"id": "4", "text": "Billing page shows the wrong amount", "user_type": "paid", "source": "support"},
        {"id": "5", "text": "I love the new export feature, thanks", "user_type": "free", "source": "nps"},
    ]
