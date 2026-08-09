"""The threshold calibration sweep."""

from __future__ import annotations

from scripts.calibrate_threshold import (
    TOPICS,
    _evaluate,
    _pairs,
    _split_centroids,
    labelled_groups,
    run,
)
from tests.fakes import FakeEmbeddings


def test_labelled_groups_cover_the_demo_topics():
    groups = labelled_groups()

    assert set(groups) <= set(TOPICS)
    assert len(groups) >= 6, "too few labelled topics to calibrate against"
    assert all(len(texts) >= 2 for texts in groups.values())


def test_evaluate_counts_merges_and_splits():
    # (similarity, genuinely the same theme)
    scored = [(0.95, True), (0.90, True), (0.40, False), (0.85, False)]

    strict = _evaluate(scored, 0.92)
    assert strict["merged_correctly"] == 1
    assert strict["split_wrongly"] == 1
    assert strict["merged_wrongly"] == 0
    assert strict["precision"] == 1.0

    loose = _evaluate(scored, 0.80)
    assert loose["merged_correctly"] == 2
    assert loose["merged_wrongly"] == 1, "0.85 negative should merge wrongly"
    assert loose["recall"] == 1.0


def test_evaluate_handles_a_threshold_nothing_reaches():
    scored = [(0.5, True), (0.2, False)]
    stats = _evaluate(scored, 0.99)

    assert stats["precision"] == 0.0
    assert stats["recall"] == 0.0
    assert stats["f1"] == 0.0


def test_pairs_labels_same_topic_positive_and_cross_topic_negative():
    embedder = FakeEmbeddings()
    groups = {
        "signup": ["signup is broken", "signup fails again"],
        "billing": ["billing is wrong", "billing charged twice"],
    }
    vectors = {
        text: embedder.embed_query(text)
        for texts in groups.values()
        for text in texts
    }

    scored = _pairs(_split_centroids(groups, vectors))
    positives = [sim for sim, same in scored if same]
    negatives = [sim for sim, same in scored if not same]

    assert len(positives) == 2, "one positive pair per topic"
    assert len(negatives) == 1, "one cross-topic pair"
    assert min(positives) > max(negatives)


async def test_sweep_runs_offline_end_to_end(capsys):
    """Smoke test: must work with no API key and no network."""
    assert await run(offline=True) == 0

    output = capsys.readouterr().out
    assert "Centroid similarity distribution" in output
    assert "Sweep" in output
    # The fake embedder is orthogonal by construction, so the script must say
    # so rather than presenting a tie-break artifact as a recommendation.
    assert "No single best threshold" in output
    assert "Consider setting" not in output
