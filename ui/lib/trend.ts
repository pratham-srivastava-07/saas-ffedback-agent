import type { TrendDirection } from "@/lib/api";

/**
 * Trajectory derived from a theme's own snapshot history.
 *
 * `GET /themes/trends` returns history but no verdict — the direction is
 * computed server-side per run and stored there. Rather than invent a second
 * definition, this mirrors `app/graph/nodes/trends.py` exactly, including its
 * constants and its refusal to call a trend on thin history. Two rules that
 * disagreed would be worse than no filter at all: the Themes list would
 * contradict the run pages.
 *
 * Keep these three numbers in step with `app/config.py`.
 */
const MIN_SNAPSHOTS = 3;
const SPIKE_RATIO = 2.0;
const DECLINE_RATIO = 0.5;

export interface HistoryPoint {
  share: number;
}

export function deriveDirection(history: HistoryPoint[]): TrendDirection {
  if (history.length === 0) return "insufficient_history";

  const current = history[history.length - 1].share;
  const priors = history.slice(0, -1);

  // First appearance, nothing to compare against.
  if (priors.length === 0) return "emerging";

  if (priors.length < MIN_SNAPSHOTS) return "insufficient_history";

  const baseline =
    priors.reduce((total, point) => total + point.share, 0) / priors.length;

  if (baseline <= 0) return "steady";

  const ratio = current / baseline;
  if (ratio >= SPIKE_RATIO) return "spiking";
  if (ratio <= DECLINE_RATIO) return "declining";
  return "steady";
}
