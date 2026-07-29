"""Deterministic stand-ins for the chat model and the embedder.

The whole suite runs against these: no API key, no network, no cost, and
stable clustering assertions. The embedder maps text to topic-orthogonal
vectors, so "signup" feedback genuinely clusters apart from "billing"
feedback and the clustering tests assert real behaviour rather than mocks.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Sequence

import numpy as np
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.runnables import Runnable, RunnableLambda

from app.schemas import (
    CritiqueVerdict,
    ItemAnalysis,
    LLMRecommendation,
    RecommendationSet,
    ThemeNaming,
)

TOPICS = ["signup", "billing", "performance", "export", "mobile", "search"]
_EXTRA_DIMS = 4


class FakeEmbeddings(Embeddings):
    """Topic-orthogonal unit vectors derived from keywords.

    Same topic -> identical direction -> cosine distance 0 -> same cluster.
    Different topic -> orthogonal -> distance 1 -> different clusters.
    """

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        vector = np.zeros(len(TOPICS) + _EXTRA_DIMS, dtype=np.float32)
        lowered = text.lower()

        for index, topic in enumerate(TOPICS):
            if topic in lowered:
                vector[index] = 1.0

        if not vector.any():
            # Stable across processes: hashlib, not the randomised builtin.
            digest = hashlib.sha256(lowered.encode()).digest()
            vector[len(TOPICS) + (digest[0] % _EXTRA_DIMS)] = 1.0

        norm = np.linalg.norm(vector)
        return (vector / norm).tolist() if norm else vector.tolist()

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.embed_documents(texts)

    async def aembed_query(self, text: str) -> list[float]:
        return self.embed_query(text)


_POSITIVE = ("love", "great", "excellent", "amazing", "thanks", "perfect")
_SEVERE = ("crash", "broken", "data loss", "cannot", "down", "fails", "lost")
_CHURN = ("cancel", "refund", "switch", "leaving", "competitor", "churn")


def _default_item_analysis(text: str) -> ItemAnalysis:
    lowered = text.lower()
    positive = any(word in lowered for word in _POSITIVE)
    severe = any(word in lowered for word in _SEVERE)

    area = next((topic for topic in TOPICS if topic in lowered), "general")

    return ItemAnalysis(
        sentiment="positive" if positive else "negative" if severe else "neutral",
        emotion="satisfied" if positive else "frustrated" if severe else "neutral",
        intent="praise" if positive else "bug-report" if severe else "other",
        severity=5 if severe else 1 if positive else 3,
        feature_area=area,
        churn_risk=any(word in lowered for word in _CHURN),
    )


def _default_theme_naming(prompt: str) -> ThemeNaming:
    topic = next((t for t in TOPICS if t in prompt.lower()), "general")
    return ThemeNaming(
        name=f"{topic.title()} issues", description=f"Users reporting {topic} problems."
    )


def _theme_ids_in(prompt: str) -> list[str]:
    return re.findall(r"id=([0-9a-fA-F-]{8,})", prompt)


def _default_recommendations(prompt: str) -> RecommendationSet:
    ids = _theme_ids_in(prompt)
    return RecommendationSet(
        recommendations=[
            LLMRecommendation(
                title="Fix the top reported issue",
                rationale="Highest impact score in the evidence.",
                theme_ids=ids[:1],
                effort="medium",
            )
        ]
    )


class FakeChat(BaseChatModel):
    """Chat model whose structured outputs are computed, not canned.

    ``overrides`` maps a schema class to a callable taking the rendered prompt
    and returning an instance, which is how individual tests force specific
    behaviour (e.g. a critic that never approves).
    """

    overrides: dict[type, Any] = {}
    fail_on: set[str] = set()
    calls: list[tuple[str, str]] = []

    @property
    def _llm_type(self) -> str:
        return "fake-chat"

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        text = _render(messages)
        self.calls.append(("plain", text))
        if any(token in text for token in self.fail_on):
            raise RuntimeError("fake chat failure")
        return ChatResult(
            generations=[
                ChatGeneration(message=AIMessage(content="Fake narrative summary."))
            ]
        )

    def with_structured_output(
        self, schema: type, **kwargs: Any
    ) -> Runnable:  # type: ignore[override]
        def respond(messages: Sequence[BaseMessage]) -> Any:
            message_list = list(messages)
            full = _render(message_list)
            # Match only on the human turn. Reading the system prompt too made
            # every cluster inherit keywords from the prompt's own examples.
            prompt = _human_text(message_list)
            self.calls.append((getattr(schema, "__name__", str(schema)), full))

            if any(token in full for token in self.fail_on):
                raise RuntimeError("fake chat failure")

            if schema in self.overrides:
                return self.overrides[schema](prompt)

            if schema is ItemAnalysis:
                return _default_item_analysis(prompt)
            if schema is ThemeNaming:
                return _default_theme_naming(prompt)
            if schema is RecommendationSet:
                return _default_recommendations(prompt)
            if schema is CritiqueVerdict:
                return CritiqueVerdict(approved=True, issues=[], guidance="")

            raise NotImplementedError(f"No fake for {schema}")

        return RunnableLambda(respond)


def _render(messages: list[BaseMessage]) -> str:
    return "\n".join(str(getattr(m, "content", m)) for m in messages)


def _human_text(messages: list[BaseMessage]) -> str:
    human = [m for m in messages if isinstance(m, HumanMessage)]
    return str(human[-1].content) if human else _render(messages)
