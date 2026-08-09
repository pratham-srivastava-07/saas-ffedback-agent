"""Tune THEME_MERGE_THRESHOLD against real embeddings.

The default of 0.82 has only ever been exercised against the test suite's
fake embedder, which maps topics to orthogonal dimensions — every similarity
is exactly 1.0 or 0.0, so any threshold in between scores perfectly. Real
embeddings live in the 0.6-0.9 band, which is precisely where this constant
decides whether a taxonomy stays stable or churns.

The sweep mirrors what ``resolve_taxonomy`` actually does: it compares a
*centroid* against a *centroid*, not two individual texts. Each labelled
topic is split in half and each half's centroid computed, so a positive pair
is "two independent samples of the same theme" — exactly the situation where
a stored theme should absorb a new cluster.

    python scripts/calibrate_threshold.py --offline    # smoke test, no key
    python scripts/calibrate_threshold.py              # real embeddings

Read the output as a trade-off, not a verdict: too low and unrelated themes
merge, too high and the taxonomy invents new themes every run.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from app.config import get_settings  # noqa: E402
from app.graph.vectors import centroid, cosine_similarity  # noqa: E402
from scripts.demo_data import WEEKS  # noqa: E402

# Ground truth: the topic each demo item is really about. These are the same
# keywords the corpus is built around, so the grouping is genuine, not guessed.
TOPICS = [
    "signup",
    "billing",
    "dashboard",
    "export",
    "search",
    "integration",
    "notification",
    "mobile",
]


def labelled_groups() -> dict[str, list[str]]:
    """Demo feedback grouped by the theme it genuinely belongs to."""
    groups: dict[str, list[str]] = {topic: [] for topic in TOPICS}
    for _label, items in WEEKS:
        for item in items:
            text = item["text"]
            hits = [topic for topic in TOPICS if topic in text.lower()]
            if len(hits) == 1:
                groups[hits[0]].append(text)
    return {topic: texts for topic, texts in groups.items() if len(texts) >= 2}


async def _embed_all(texts: list[str], offline: bool) -> dict[str, list[float]]:
    if offline:
        from tests.fakes import FakeEmbeddings

        embedder = FakeEmbeddings()
    else:
        from app.llm import build_embeddings

        embedder = build_embeddings(get_settings())

    vectors = await embedder.aembed_documents(texts)
    return dict(zip(texts, vectors))


def _split_centroids(
    groups: dict[str, list[str]], vectors: dict[str, list[float]]
) -> dict[str, tuple[list[float], list[float]]]:
    """Two independent centroids per topic, mimicking two separate runs."""
    out = {}
    for topic, texts in groups.items():
        midpoint = max(1, len(texts) // 2)
        first = centroid([vectors[text] for text in texts[:midpoint]])
        second = centroid([vectors[text] for text in texts[midpoint:]])
        if first and second:
            out[topic] = (first, second)
    return out


def _pairs(splits: dict[str, tuple[list[float], list[float]]]):
    """(similarity, should_merge) for every centroid pair."""
    topics = sorted(splits)
    scored = []

    for topic in topics:
        first, second = splits[topic]
        scored.append((cosine_similarity(first, second), True))

    for i, left in enumerate(topics):
        for right in topics[i + 1 :]:
            scored.append((cosine_similarity(splits[left][0], splits[right][0]), False))

    return scored


def _evaluate(scored, threshold: float) -> dict:
    tp = sum(1 for sim, same in scored if same and sim >= threshold)
    fn = sum(1 for sim, same in scored if same and sim < threshold)
    fp = sum(1 for sim, same in scored if not same and sim >= threshold)
    tn = sum(1 for sim, same in scored if not same and sim < threshold)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )
    return {
        "threshold": threshold,
        "merged_correctly": tp,
        "split_wrongly": fn,
        "merged_wrongly": fp,
        "split_correctly": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


async def run(offline: bool) -> int:
    groups = labelled_groups()
    if len(groups) < 2:
        print("Not enough labelled topics to calibrate.")
        return 1

    texts = sorted({text for texts in groups.values() for text in texts})
    print(
        f"Embedding {len(texts)} labelled samples across {len(groups)} topics"
        f"{' (offline fakes)' if offline else ''}...\n"
    )

    vectors = await _embed_all(texts, offline)
    scored = _pairs(_split_centroids(groups, vectors))

    same = [sim for sim, is_same in scored if is_same]
    different = [sim for sim, is_same in scored if not is_same]

    print("Centroid similarity distribution")
    print(f"  same theme      min {min(same):.3f}  max {max(same):.3f}")
    print(f"  different theme min {min(different):.3f}  max {max(different):.3f}")

    if min(same) > max(different):
        print(
            f"\n  Cleanly separable: any threshold between "
            f"{max(different):.3f} and {min(same):.3f} scores perfectly."
        )
        if offline:
            print(
                "  Expected offline — the fake embedder is orthogonal by "
                "construction. Re-run with real keys for a meaningful answer."
            )

    print("\nSweep")
    print(f"  {'thresh':>7} {'merge P':>9} {'merge R':>9} {'F1':>7}"
          f" {'wrong merges':>13} {'wrong splits':>13}")

    results = []
    threshold = 0.50
    while threshold <= 0.951:
        stats = _evaluate(scored, round(threshold, 2))
        results.append(stats)
        print(
            f"  {stats['threshold']:>7.2f} {stats['precision']:>9.3f}"
            f" {stats['recall']:>9.3f} {stats['f1']:>7.3f}"
            f" {stats['merged_wrongly']:>13} {stats['split_wrongly']:>13}"
        )
        threshold += 0.05

    best = max(results, key=lambda row: (row["f1"], row["threshold"]))
    current = get_settings().theme_merge_threshold
    separable = min(same) > max(different)

    print(f"\n  Best F1 at threshold {best['threshold']:.2f} (F1 {best['f1']:.3f})")
    print(f"  Currently configured: {current}")

    if separable:
        # Every threshold in the gap scores identically, so "best F1" is
        # decided by the tie-break, not by the data. Recommending it would be
        # noise dressed up as a finding.
        midpoint = (max(different) + min(same)) / 2
        print(
            f"\n  No single best threshold: the classes do not overlap, so "
            f"anything in the gap works. Midpoint is {midpoint:.2f}."
        )
    elif abs(best["threshold"] - current) > 0.05:
        print(
            f"\n  Consider setting THEME_MERGE_THRESHOLD={best['threshold']:.2f}"
        )
    print(
        "\n  Wrong merges collapse distinct problems into one theme; wrong "
        "splits make the taxonomy churn. Pick the side you would rather err on."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--offline",
        action="store_true",
        help="use the deterministic fake embedder (smoke test, no API key)",
    )
    args = parser.parse_args()
    return asyncio.run(run(args.offline))


if __name__ == "__main__":
    raise SystemExit(main())
