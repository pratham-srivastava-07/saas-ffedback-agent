"""normalize and triage: the deterministic front of the pipeline."""

from __future__ import annotations

from app.graph.nodes.normalize import normalize
from app.graph.nodes.triage import triage


async def test_normalize_collapses_whitespace_and_assigns_ids():
    result = await normalize({"raw": [{"text": "  too   many\n\nspaces  "}]})

    assert result["clean"][0]["text"] == "too many spaces"
    assert result["clean"][0]["id"] == "item-1"


async def test_normalize_drops_only_genuine_duplicates():
    result = await normalize(
        {
            "raw": [
                {"id": "a", "text": "Signup is broken"},
                {"id": "b", "text": "signup is BROKEN!"},  # same after folding
                {"id": "c", "text": "Signup fails on mobile"},  # different report
            ]
        }
    )

    assert [item["id"] for item in result["clean"]] == ["a", "c"]
    assert result["rejected"][0]["reason"] == "duplicate"


async def test_normalize_keeps_semantically_similar_items_separate():
    """Volume is the product's output. Two people reporting the same bug in
    different words is two mentions, not one."""
    result = await normalize(
        {
            "raw": [
                {"id": "a", "text": "The signup flow is broken"},
                {"id": "b", "text": "I cannot sign up, it keeps failing"},
            ]
        }
    )

    assert len(result["clean"]) == 2


async def test_triage_rejects_noise_and_keeps_real_feedback():
    result = await triage(
        {
            "clean": [
                {"id": "1", "text": "The export button does nothing", "user_type": "free", "source": "support"},
                {"id": "2", "text": "ok", "user_type": "free", "source": "support"},
                {"id": "3", "text": "!!!!! ???", "user_type": "free", "source": "support"},
                {"id": "4", "text": "https://example.com", "user_type": "free", "source": "support"},
                {"id": "5", "text": "asdfghjkl", "user_type": "free", "source": "support"},
            ]
        }
    )

    assert [item["id"] for item in result["clean"]] == ["1"]

    reasons = {item["id"]: item["reason"] for item in result["rejected"]}
    assert reasons["2"] == "too_short"
    assert reasons["3"] == "no_language_content"
    assert reasons["4"] == "url_only"
    assert reasons["5"] == "keyboard_mash"
