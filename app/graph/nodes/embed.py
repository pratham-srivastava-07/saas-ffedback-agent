"""Embed every surviving item in one batched call.

Placed after fan-in rather than inside the per-item node on purpose:
embedding APIs accept arrays, so fifty items cost one request instead of fifty.
"""

from __future__ import annotations

import logging

from langchain_core.runnables import RunnableConfig

from app.graph.state import AnalysisState
from app.llm import get_runtime

logger = logging.getLogger(__name__)


async def embed(state: AnalysisState, config: RunnableConfig) -> dict:
    runtime = get_runtime(config)
    items = [item for item in state.get("analyzed", []) if item.get("text")]

    if not items:
        return {"embeddings": {}}

    texts = [item["text"] for item in items]
    vectors = await runtime.embeddings.aembed_documents(texts)

    return {
        "embeddings": {
            item["id"]: vector for item, vector in zip(items, vectors)
        }
    }
