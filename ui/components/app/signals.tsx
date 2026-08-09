import {
  ArrowDownRight,
  ArrowUpRight,
  CircleDashed,
  Minus,
  Sparkle,
  TriangleAlert,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { SENTIMENT_META, TREND_META, severityLabel } from "@/lib/format";
import type { Sentiment, TrendDirection } from "@/lib/api";

const TREND_ICON = {
  spiking: ArrowUpRight,
  emerging: Sparkle,
  declining: ArrowDownRight,
  steady: Minus,
  insufficient_history: CircleDashed,
} as const;

/**
 * Direction is carried by icon shape AND label AND colour, never colour alone.
 * `insufficient_history` gets a dashed outline rather than being hidden: the
 * backend deliberately declines to invent a percentage from thin data and the
 * interface says so out loud.
 */
export function TrendBadge({
  direction,
  ratio,
  className,
  showLabel = true,
}: {
  direction: TrendDirection;
  ratio?: number | null;
  className?: string;
  showLabel?: boolean;
}) {
  const meta = TREND_META[direction];
  const Icon = TREND_ICON[direction];
  const multiple =
    direction === "spiking" || direction === "declining"
      ? ratio ?? null
      : null;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-xs font-medium",
        meta.className,
        className,
      )}
      title={meta.description}
    >
      <Icon className="size-3.5" aria-hidden />
      {showLabel && <span>{meta.label}</span>}
      {multiple !== null && (
        <span className="tabular font-mono text-[11px]">
          {multiple.toFixed(1)}x
        </span>
      )}
    </span>
  );
}

export function SentimentDot({
  sentiment,
  className,
}: {
  sentiment: Sentiment | null;
  className?: string;
}) {
  if (!sentiment) {
    return (
      <span
        className={cn("inline-block size-2 rounded-full bg-muted-foreground/40", className)}
        aria-label="Sentiment unknown"
      />
    );
  }
  const meta = SENTIMENT_META[sentiment];
  return (
    <span
      className={cn("inline-block size-2 rounded-full", meta.swatch, className)}
      aria-label={meta.label}
      title={meta.label}
    />
  );
}

/**
 * Proportional sentiment split. Segment widths carry the data; the legend
 * below carries the numbers, so nothing depends on reading colour alone.
 */
export function SentimentBar({
  breakdown,
  className,
}: {
  breakdown: Record<string, number>;
  className?: string;
}) {
  const positive = breakdown.positive ?? 0;
  const neutral = breakdown.neutral ?? 0;
  const negative = breakdown.negative ?? 0;
  const total = positive + neutral + negative;

  if (total === 0) {
    return (
      <p className={cn("text-xs text-muted-foreground", className)}>
        No sentiment recorded
      </p>
    );
  }

  const segments = [
    { key: "negative", value: negative, className: "bg-negative" },
    { key: "neutral", value: neutral, className: "bg-neutral/60" },
    { key: "positive", value: positive, className: "bg-positive" },
  ].filter((segment) => segment.value > 0);

  return (
    <div className={className}>
      <div
        className="flex h-1.5 w-full overflow-hidden rounded-full bg-muted"
        role="img"
        aria-label={`${negative} negative, ${neutral} neutral, ${positive} positive`}
      >
        {segments.map((segment) => (
          <div
            key={segment.key}
            className={segment.className}
            style={{ width: `${(segment.value / total) * 100}%` }}
          />
        ))}
      </div>
      <div className="mt-1.5 flex gap-3 font-mono text-[11px] text-muted-foreground tabular">
        <span className="text-negative">{negative} neg</span>
        <span>{neutral} neu</span>
        <span className="text-positive">{positive} pos</span>
      </div>
    </div>
  );
}

/** Severity 1-5 as discrete filled marks. Reads as a gauge, not a progress bar. */
export function SeverityMarks({
  severity,
  className,
}: {
  severity: number | null;
  className?: string;
}) {
  const value = severity ?? 0;
  return (
    <span
      className={cn("inline-flex items-center gap-0.5", className)}
      title={severityLabel(severity)}
      aria-label={`Severity ${value} of 5: ${severityLabel(severity)}`}
    >
      {[1, 2, 3, 4, 5].map((mark) => (
        <span
          key={mark}
          className={cn(
            "h-3 w-1 rounded-[1px]",
            mark <= value
              ? value >= 4
                ? "bg-negative"
                : value === 3
                  ? "bg-signal-new"
                  : "bg-muted-foreground/60"
              : "bg-muted",
          )}
        />
      ))}
    </span>
  );
}

export function ChurnFlag({ count }: { count: number }) {
  if (count <= 0) return null;
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-md border border-negative/30 bg-negative/10 px-2 py-0.5 text-xs font-medium text-negative"
      title="Customers who signalled they may leave"
    >
      <TriangleAlert className="size-3.5" aria-hidden />
      <span className="tabular font-mono">{count}</span> at risk
    </span>
  );
}
