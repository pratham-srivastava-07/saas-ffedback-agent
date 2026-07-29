"""Detect whether each theme is growing, shrinking, or new.

"34 mentions, 3x since Tuesday" is the sentence that gets a ticket filed.
"34 mentions" on its own does not.

Two honesty rules are enforced here:

* Comparison is on *share of the run*, not raw count. Otherwise uploading a
  bigger file next week would report every theme as spiking.
* Below ``min_snapshots_for_trend`` prior runs we say so, rather than
  extrapolating a percentage from two data points.
"""

from __future__ import annotations

import logging

from app.graph.state import AnalysisState
from app.llm import get_runtime
from app.store import repo

logger = logging.getLogger(__name__)


async def detect_trends(state: AnalysisState, config=None) -> dict:
    runtime = get_runtime(config)
    settings = runtime.settings
    themes = state.get("themes", [])
    run_id = state.get("run_id", "")

    if not themes:
        return {"trends": []}

    if runtime.session_factory is None:
        return {"trends": [_no_history(theme) for theme in themes]}

    trends: list[dict] = []

    async with runtime.session_factory() as session:
        for theme in themes:
            theme_id = theme.get("id")
            current_share = float(theme.get("share", 0.0))

            if not theme_id:
                trends.append(_no_history(theme))
                continue

            history = await repo.theme_history(
                session, theme_id, exclude_run_id=run_id, limit=10
            )

            if theme.get("is_new") and not history:
                trends.append(
                    {
                        "theme_id": theme_id,
                        "theme_name": theme.get("name", ""),
                        "direction": "emerging",
                        "current_share": round(current_share, 4),
                        "baseline_share": None,
                        "change_ratio": None,
                        "detail": "First time this theme has appeared.",
                    }
                )
            elif len(history) < settings.min_snapshots_for_trend:
                trends.append(
                    {
                        "theme_id": theme_id,
                        "theme_name": theme.get("name", ""),
                        "direction": "insufficient_history",
                        "current_share": round(current_share, 4),
                        "baseline_share": None,
                        "change_ratio": None,
                        "detail": (
                            f"Only {len(history)} prior run(s); need "
                            f"{settings.min_snapshots_for_trend} before calling a trend."
                        ),
                    }
                )
            else:
                baseline = sum(s.share for s in history) / len(history)
                ratio = (current_share / baseline) if baseline > 0 else None

                if ratio is None:
                    direction, detail = "steady", "No usable baseline."
                elif ratio >= settings.spike_ratio:
                    direction = "spiking"
                    detail = f"{ratio:.1f}x its {len(history)}-run average."
                elif ratio <= settings.decline_ratio:
                    direction = "declining"
                    detail = f"{ratio:.1f}x its {len(history)}-run average."
                else:
                    direction = "steady"
                    detail = f"In line with its {len(history)}-run average."

                trends.append(
                    {
                        "theme_id": theme_id,
                        "theme_name": theme.get("name", ""),
                        "direction": direction,
                        "current_share": round(current_share, 4),
                        "baseline_share": round(baseline, 4),
                        "change_ratio": round(ratio, 2) if ratio is not None else None,
                        "detail": detail,
                    }
                )

            # Record this run regardless, so future runs have a baseline.
            breakdown = theme.get("sentiment_breakdown", {})
            await repo.save_snapshot(
                session,
                theme_id=theme_id,
                run_id=run_id,
                count=theme.get("count", 0),
                share=current_share,
                avg_severity=float(theme.get("avg_severity", 0.0)),
                positive=breakdown.get("positive", 0),
                neutral=breakdown.get("neutral", 0),
                negative=breakdown.get("negative", 0),
                churn_risk_count=theme.get("churn_risk_count", 0),
            )

    return {"trends": trends}


def _no_history(theme: dict) -> dict:
    return {
        "theme_id": theme.get("id") or "",
        "theme_name": theme.get("name", ""),
        "direction": "insufficient_history",
        "current_share": round(float(theme.get("share", 0.0)), 4),
        "baseline_share": None,
        "change_ratio": None,
        "detail": "No stored history for this theme.",
    }
