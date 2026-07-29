"""End-to-end graph behaviour, including the three structural hazards."""

from __future__ import annotations

from app.graph.build import build_graph, initial_state
from app.schemas import CritiqueVerdict
from app.store import repo

GRAPH = build_graph()


async def test_full_pipeline_produces_ranked_themes(config, feedback_batch):
    final = await GRAPH.ainvoke(initial_state("run-1", feedback_batch), config)

    assert len(final["analyzed"]) == 5
    assert final["themes"], "expected at least one theme"
    assert final["summary"]

    # The three differently-worded signup reports must be one theme, not three.
    signup = [t for t in final["themes"] if "Signup" in t["name"]]
    assert len(signup) == 1
    assert signup[0]["count"] == 3

    # Ranked by impact, descending.
    scores = [t["impact_score"] for t in final["themes"]]
    assert scores == sorted(scores, reverse=True)

    # Every theme was named and persisted.
    assert all(t["id"] and t["name"] for t in final["themes"])


async def test_triage_short_circuit_reaches_the_end(config):
    """A batch of pure noise must skip analysis, clustering and recommendation
    entirely rather than sending garbage to the model."""
    noise = [
        {"id": "1", "text": "ok", "user_type": "free", "source": "support"},
        {"id": "2", "text": "?!?!?!", "user_type": "free", "source": "support"},
        {"id": "3", "text": "https://spam.example.com", "user_type": "free", "source": "support"},
    ]

    final = await GRAPH.ainvoke(initial_state("run-noise", noise), config)

    assert final["analyzed"] == []
    assert final["themes"] == []
    assert final["recommendations"] == []
    assert len(final["rejected"]) == 3
    assert "Nothing actionable" in final["summary"]


async def test_critique_cycle_terminates_when_never_approved(
    runtime, config, feedback_batch
):
    """A critic that rejects everything must not spin forever."""
    runtime.chat.overrides[CritiqueVerdict] = lambda _prompt: CritiqueVerdict(
        approved=False,
        issues=["Not grounded in the evidence."],
        guidance="Cite the actual mention counts.",
    )

    final = await GRAPH.ainvoke(initial_state("run-loop", feedback_batch), config)

    assert final["revision_count"] == runtime.settings.max_critique_revisions
    assert final["summary"], "graph must still reach the summary node"


async def test_critique_approval_stops_after_one_pass(config, feedback_batch):
    final = await GRAPH.ainvoke(initial_state("run-ok", feedback_batch), config)
    assert final["revision_count"] == 1


async def test_one_failing_item_does_not_kill_the_run(runtime, config):
    """A 200-item batch must survive a single row the model chokes on."""
    runtime.chat.fail_on = {"POISON"}

    batch = [
        {"id": "1", "text": "Signup is broken for everyone", "user_type": "paid", "source": "support"},
        {"id": "2", "text": "POISON payload that breaks the model", "user_type": "free", "source": "support"},
        {"id": "3", "text": "Billing charged me twice this month", "user_type": "paid", "source": "support"},
    ]

    final = await GRAPH.ainvoke(initial_state("run-partial", batch), config)

    statuses = {item["id"]: item["status"] for item in final["analyzed"]}
    assert statuses["2"] == "failed"
    assert statuses["1"] == "ok"
    assert statuses["3"] == "ok"
    assert final["summary"]


async def test_second_run_reuses_the_theme_from_the_first(
    runtime, config, feedback_batch
):
    """Taxonomy memory across runs: the same problem keeps the same theme id,
    which is what makes trajectory possible at all."""
    first = await GRAPH.ainvoke(initial_state("run-a", feedback_batch), config)
    first_signup = next(t for t in first["themes"] if "Signup" in t["name"])

    second_batch = [
        {"id": "10", "text": "Signup broken again after the update", "user_type": "paid", "source": "support"},
        {"id": "11", "text": "Still cannot signup at all", "user_type": "free", "source": "support"},
    ]
    second = await GRAPH.ainvoke(initial_state("run-b", second_batch), config)
    second_signup = next(t for t in second["themes"] if "Signup" in t["name"])

    assert second_signup["id"] == first_signup["id"]
    assert second_signup["is_new"] is False

    async with runtime.session_factory() as session:
        themes = await repo.load_themes(session)

    names = [t.name for t in themes]
    assert names.count("Signup issues") == 1, f"taxonomy churned: {names}"
