"""FastAPI application entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analyze, runs, themes
from app.config import get_settings
from app.llm import build_runtime
from app.service import get_graph
from app.store.db import get_session_factory, init_db

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    await init_db()

    session_factory = get_session_factory()
    app.state.settings = settings
    app.state.session_factory = session_factory
    app.state.runtime = build_runtime(settings, session_factory)

    yield


app = FastAPI(
    title="Sentilytics Insight Engine",
    version="2.0.0",
    description=(
        "Turns a feedback firehose into a ranked list of what to fix this week, "
        "with the evidence attached."
    ),
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router)
app.include_router(themes.router)
app.include_router(runs.router)


@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok"}


@app.get("/graph", tags=["meta"])
async def graph_topology():
    """The pipeline as mermaid, so the UI can render the real topology."""
    return {"mermaid": get_graph().get_graph().draw_mermaid()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
