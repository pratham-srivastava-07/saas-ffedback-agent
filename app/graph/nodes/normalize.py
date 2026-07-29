"""Clean raw input and drop exact duplicates.

Deliberately *not* semantic deduplication. If forty people report the signup
bug in forty different phrasings, that is forty mentions, and collapsing them
would destroy the volume signal this product exists to produce. Only genuine
duplicates — the same text submitted twice, e.g. a webhook retry — are removed.
"""

from __future__ import annotations

import re
import unicodedata

from app.graph.state import AnalysisState

_WHITESPACE = re.compile(r"\s+")
_PUNCTUATION = re.compile(r"[^\w\s]")


def _collapse(text: str) -> str:
    return _WHITESPACE.sub(" ", text).strip()


def _dedupe_key(text: str) -> str:
    """Key for duplicate detection: case, punctuation and accent insensitive."""
    folded = unicodedata.normalize("NFKD", text).casefold()
    return _WHITESPACE.sub(" ", _PUNCTUATION.sub("", folded)).strip()


async def normalize(state: AnalysisState) -> dict:
    seen: set[str] = set()
    clean: list[dict] = []
    rejected: list[dict] = []

    for position, item in enumerate(state.get("raw", [])):
        text = _collapse(str(item.get("text", "")))
        item_id = str(item.get("id") or "") or f"item-{position + 1}"

        if not text:
            rejected.append({"id": item_id, "text": "", "reason": "empty"})
            continue

        key = _dedupe_key(text)
        if key in seen:
            rejected.append({"id": item_id, "text": text, "reason": "duplicate"})
            continue

        seen.add(key)
        clean.append(
            {
                "id": item_id,
                "text": text,
                "user_type": item.get("user_type") or "free",
                "source": item.get("source") or "other",
            }
        )

    return {"clean": clean, "rejected": rejected}
