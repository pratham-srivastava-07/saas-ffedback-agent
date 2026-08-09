import type { Sentiment, TrendDirection } from "@/lib/api";

export function percent(value: number, digits = 1): string {
  return `${(value * 100).toFixed(digits)}%`;
}

export function compactNumber(value: number): string {
  return new Intl.NumberFormat(undefined, { notation: "compact" }).format(value);
}

export function formatDate(iso: string): string {
  const date = new Date(iso.endsWith("Z") ? iso : `${iso}Z`);
  if (Number.isNaN(date.getTime())) return iso;
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

export function relativeTime(iso: string): string {
  const date = new Date(iso.endsWith("Z") ? iso : `${iso}Z`);
  if (Number.isNaN(date.getTime())) return iso;

  const seconds = Math.round((date.getTime() - Date.now()) / 1000);
  const units: [Intl.RelativeTimeFormatUnit, number][] = [
    ["second", 60],
    ["minute", 60],
    ["hour", 24],
    ["day", 7],
    ["week", 4.35],
    ["month", 12],
    ["year", Number.POSITIVE_INFINITY],
  ];

  const formatter = new Intl.RelativeTimeFormat(undefined, { numeric: "auto" });
  let value = seconds;
  for (const [unit, size] of units) {
    if (Math.abs(value) < size) return formatter.format(Math.round(value), unit);
    value /= size;
  }
  return formatter.format(Math.round(value), "year");
}

/**
 * Trend presentation.
 *
 * `insufficient_history` is a first-class, honest state: the backend refuses
 * to extrapolate a percentage from fewer than three prior runs, and the UI
 * must show that rather than hide it or invent a number.
 *
 * Every direction carries a distinct label and icon shape as well as a colour,
 * so the meaning survives for colour-blind users and in greyscale.
 */
export const TREND_META: Record<
  TrendDirection,
  { label: string; className: string; dotClassName: string; description: string }
> = {
  spiking: {
    label: "Spiking",
    className: "text-signal-up border-signal-up/35 bg-signal-up/10",
    dotClassName: "bg-signal-up",
    description: "Growing much faster than its recent average",
  },
  emerging: {
    label: "New",
    className: "text-signal-new border-signal-new/35 bg-signal-new/10",
    dotClassName: "bg-signal-new",
    description: "First time this theme has appeared",
  },
  declining: {
    label: "Declining",
    className: "text-signal-down border-signal-down/35 bg-signal-down/10",
    dotClassName: "bg-signal-down",
    description: "Shrinking against its recent average",
  },
  steady: {
    label: "Steady",
    className: "text-signal-flat border-border bg-muted/60",
    dotClassName: "bg-signal-flat",
    description: "In line with its recent average",
  },
  insufficient_history: {
    label: "Not enough history",
    className:
      "text-signal-unknown border-dashed border-signal-unknown/45 bg-transparent",
    dotClassName: "bg-signal-unknown",
    description: "Too few prior runs to call a trend yet",
  },
};

export const SENTIMENT_META: Record<
  Sentiment,
  { label: string; className: string; swatch: string }
> = {
  positive: { label: "Positive", className: "text-positive", swatch: "bg-positive" },
  neutral: { label: "Neutral", className: "text-neutral", swatch: "bg-neutral" },
  negative: { label: "Negative", className: "text-negative", swatch: "bg-negative" },
};

export function severityLabel(severity: number | null): string {
  if (severity === null) return "Unrated";
  return (
    [
      "",
      "Cosmetic",
      "Minor annoyance",
      "Real friction",
      "Blocks a core task",
      "Critical",
    ][severity] ?? `Level ${severity}`
  );
}

/** Deterministic hue per theme, so a theme keeps its colour across views. */
export function themeHue(id: string): number {
  let hash = 0;
  for (let i = 0; i < id.length; i += 1) {
    hash = (hash * 31 + id.charCodeAt(i)) % 360;
  }
  return hash;
}

export function themeColor(id: string, lightness = 0.62): string {
  return `oklch(${lightness} 0.15 ${themeHue(id)})`;
}
