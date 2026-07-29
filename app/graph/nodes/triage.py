"""Reject noise before it reaches the LLM.

Heuristic rather than model-based, on purpose. Spam detection here is not a
hard problem, and a deterministic node is testable, free, instant, and cannot
misbehave during a live demo. It still drives a genuine conditional edge: a
batch of pure noise short-circuits the whole pipeline.

Noise that survives to clustering is worse than wasted tokens — it inflates
theme counts, and theme counts are the product's output.
"""

from __future__ import annotations

import re

from app.graph.state import AnalysisState

_MIN_LENGTH = 5
_URL_ONLY = re.compile(r"^\s*(https?://\S+\s*)+$", re.IGNORECASE)
_HAS_LETTERS = re.compile(r"[^\W\d_]")
_REPEATED_CHAR = re.compile(r"^(.)\1{4,}$")
_VOWELS = re.compile(r"[aeiou]")

# Mash is usually a walk along a keyboard row. Checking membership catches
# "asdfghjkl" and "qwertyuiop", which a vowel-frequency test alone does not:
# both contain vowels, and "qwertyuiop" is 40% vowels.
_KEYBOARD_ROWS = ("qwertyuiop", "asdfghjkl", "zxcvbnm")
_MIN_MASH_LENGTH = 5


def _is_keyboard_walk(token: str) -> bool:
    lowered = token.lower()
    if len(lowered) < _MIN_MASH_LENGTH:
        return False
    return any(lowered in row or row in lowered for row in _KEYBOARD_ROWS)


def _rejection_reason(text: str) -> str | None:
    stripped = text.strip()

    if len(stripped) < _MIN_LENGTH:
        return "too_short"
    if not _HAS_LETTERS.search(stripped):
        return "no_language_content"
    if _URL_ONLY.match(stripped):
        return "url_only"
    if _REPEATED_CHAR.match(stripped.replace(" ", "")):
        return "keyboard_mash"

    if " " not in stripped:
        if _is_keyboard_walk(stripped):
            return "keyboard_mash"
        # A long single token with almost no vowels is not a word. English
        # runs near 38% vowels; real words clear this bar comfortably.
        letters = [c for c in stripped.lower() if c.isalpha()]
        if len(letters) > 8:
            vowel_ratio = len(_VOWELS.findall("".join(letters))) / len(letters)
            if vowel_ratio < 0.2:
                return "keyboard_mash"

    return None


async def triage(state: AnalysisState) -> dict:
    kept: list[dict] = []
    rejected: list[dict] = []

    for item in state.get("clean", []):
        reason = _rejection_reason(item["text"])
        if reason:
            rejected.append(
                {"id": item["id"], "text": item["text"], "reason": reason}
            )
        else:
            kept.append(item)

    return {"clean": kept, "rejected": rejected}
