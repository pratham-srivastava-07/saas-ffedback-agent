"""Model providers and the runtime object injected into graph nodes.

Nodes never import a concrete model. They pull a :class:`Runtime` out of the
LangGraph ``RunnableConfig``, which is what lets the whole test suite run
against fakes with no API key and no network.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig

from app.config import Settings, get_settings

if TYPE_CHECKING:  # pragma: no cover
    from sqlalchemy.ext.asyncio import async_sessionmaker


@dataclass
class Runtime:
    """Everything a node needs that is not part of the graph state."""

    chat: BaseChatModel
    embeddings: Embeddings
    settings: Settings
    session_factory: Any | None = None
    semaphore: asyncio.Semaphore | None = None

    def limiter(self) -> asyncio.Semaphore:
        """Cap concurrent LLM calls during ``Send`` fan-out.

        Created lazily because a Semaphore must be bound to the running loop.
        """
        if self.semaphore is None:
            self.semaphore = asyncio.Semaphore(
                self.settings.max_concurrent_llm_calls
            )
        return self.semaphore


def build_chat_model(settings: Settings | None = None) -> BaseChatModel:
    settings = settings or get_settings()
    if not settings.groq_api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Copy .env.example to .env and fill it in."
        )
    from langchain_groq import ChatGroq

    return ChatGroq(
        model=settings.chat_model,
        api_key=settings.groq_api_key,
        temperature=0,
    )


def build_embeddings(settings: Settings | None = None) -> Embeddings:
    settings = settings or get_settings()
    if not settings.google_api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY is not set (needed for embeddings). "
            "Copy .env.example to .env and fill it in."
        )
    from langchain_google_genai import GoogleGenerativeAIEmbeddings

    return GoogleGenerativeAIEmbeddings(
        model=settings.embedding_model,
        google_api_key=settings.google_api_key,
    )


def build_runtime(
    settings: Settings | None = None, session_factory: "async_sessionmaker | None" = None
) -> Runtime:
    settings = settings or get_settings()
    return Runtime(
        chat=build_chat_model(settings),
        embeddings=build_embeddings(settings),
        settings=settings,
        session_factory=session_factory,
    )


def get_runtime(config: RunnableConfig | None) -> Runtime:
    """Extract the runtime a node needs from the LangGraph config."""
    runtime = ((config or {}).get("configurable") or {}).get("runtime")
    if not isinstance(runtime, Runtime):
        raise RuntimeError(
            "No Runtime in config['configurable']['runtime']. "
            "Invoke the graph via app.graph.build.run_graph()."
        )
    return runtime
