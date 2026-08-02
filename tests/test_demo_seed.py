"""The demo corpus, and the trend story it is supposed to tell.

This is the only test that exercises the pipeline across multiple runs, so it
is what actually proves the memory half works: themes have to survive five
separate invocations and accumulate enough history for trend detection to
fire.
"""

from __future__ import annotations

from app.graph.build import build_graph, initial_state
from app.graph.nodes.triage import _rejection_reason
from app.store import repo
from scripts.demo_data import WEEKS, weeks_with_ids
from tests.fakes import TOPICS

GRAPH = build_graph()


async def _replay_all_weeks(config) -> dict:
    """Run the whole corpus through the real graph; return the final result."""
    final: dict = {}
    for index, (_label, items) in enumerate(weeks_with_ids(), start=1):
        final = await GRAPH.ainvoke(initial_state(f"demo-run-{index}", items), config)
    return final


def test_every_substantive_demo_item_carries_exactly_one_topic():
    """The offline embedder keys off topic words, so an item with none spawns a
    spurious singleton theme and an item with two straddles clusters. Noise
    items are exempt: triage drops them before they reach the embedder."""
    offenders = []

    for label, items in WEEKS:
        for item in items:
            if _rejection_reason(item["text"]):
                continue
            hits = [topic for topic in TOPICS if topic in item["text"].lower()]
            if len(hits) != 1:
                offenders.append((label, item["text"], hits))

    assert not offenders, f"demo items with wrong topic count: {offenders}"


def test_demo_ids_are_unique():
    ids = [item["id"] for _, items in weeks_with_ids() for item in items]
    assert len(ids) == len(set(ids))


async def test_seeded_history_produces_the_intended_trend_story(config):
    """All four trend directions, produced by the real trend engine from real
    accumulated history rather than hand-written rows."""
    final = await _replay_all_weeks(config)

    directions = {
        trend["theme_name"]: trend["direction"] for trend in final["trends"]
    }

    def direction_for(keyword: str) -> str:
        matches = [d for name, d in directions.items() if keyword.lower() in name.lower()]
        assert matches, f"no theme matching {keyword!r} in {list(directions)}"
        return matches[0]

    # A week-5 regression against four quiet weeks.
    assert direction_for("Signup") == "spiking"
    # Fixed in week 4, so its share collapses.
    assert direction_for("Billing") == "declining"
    # First appearance is in week 5.
    assert direction_for("Mobile") == "emerging"
    # Grumbles along at a constant rate throughout.
    assert direction_for("Dashboard") == "steady"


async def test_taxonomy_does_not_churn_across_five_runs(runtime, config):
    """A recurring problem must keep one theme row, not gain a new one weekly."""
    await _replay_all_weeks(config)

    async with runtime.session_factory() as session:
        themes = await repo.load_themes(session)

    names = [theme.name for theme in themes]
    assert len(names) == len(set(names)), f"duplicate themes: {names}"

    signup = [theme for theme in themes if "Signup" in theme.name]
    assert len(signup) == 1
    # Present in all five weekly batches.
    assert signup[0].run_count == 5
