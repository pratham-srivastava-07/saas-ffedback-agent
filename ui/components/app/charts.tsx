"use client";

/**
 * Charts, hand-built in SVG.
 *
 * No charting library: these three forms are simple enough that Recharts
 * would cost ~100kB gzipped to draw rectangles, and the explore route already
 * showed what an unnecessary dependency does to a bundle.
 *
 * Mark specs follow the dataviz reference — thin marks, rounded data-ends
 * anchored to the baseline, a 2px surface gap between adjacent fills,
 * recessive axes, and a hover tooltip on every mark.
 */

import { useState } from "react";

import { cn } from "@/lib/utils";

type Point = { label: string; value: number; hint?: string };

// ---------------------------------------------------------------------------
// Volume over time
// ---------------------------------------------------------------------------

export function VolumeBars({
  data,
  className,
}: {
  data: Point[];
  className?: string;
}) {
  const [hover, setHover] = useState<number | null>(null);
  const max = Math.max(...data.map((d) => d.value), 1);

  if (data.length === 0) {
    return <ChartEmpty className={className} />;
  }

  return (
    <div className={cn("relative", className)}>
      <div className="flex h-32 items-end gap-[2px]" role="img"
        aria-label={`Items analysed per run. Latest: ${data[data.length - 1]?.value ?? 0}.`}>
        {data.map((point, index) => {
          const height = Math.max((point.value / max) * 100, 2);
          const active = hover === index;
          return (
            <button
              key={`${point.label}-${index}`}
              type="button"
              onMouseEnter={() => setHover(index)}
              onMouseLeave={() => setHover(null)}
              onFocus={() => setHover(index)}
              onBlur={() => setHover(null)}
              // The hit target is the full column height, not the bar — a
              // 4px-tall bar is otherwise impossible to hover.
              className="group relative flex h-full flex-1 items-end focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
              aria-label={`${point.label}: ${point.value}`}
            >
              <span
                className={cn(
                  "w-full rounded-t-[4px] transition-colors",
                  active ? "bg-primary" : "bg-primary/45",
                )}
                style={{ height: `${height}%` }}
              />
            </button>
          );
        })}
      </div>

      <div className="mt-2 h-8">
        {hover !== null && data[hover] && (
          <p className="font-mono text-[11px] text-muted-foreground tabular">
            <span className="text-foreground">{data[hover].value}</span> items
            {" · "}
            {data[hover].label}
            {data[hover].hint ? ` · ${data[hover].hint}` : ""}
          </p>
        )}
        {hover === null && (
          <p className="font-mono text-[11px] text-muted-foreground tabular">
            {data.length} run{data.length === 1 ? "" : "s"} · hover for detail
          </p>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Ranked magnitude
// ---------------------------------------------------------------------------

/**
 * Horizontal bars for "which themes are biggest".
 *
 * Magnitude comparison, so length carries the value and colour only carries
 * identity. Every row is directly labelled with its name and number, which is
 * the secondary encoding the palette's tritan separation requires.
 */
export function RankedBars({
  data,
  colors,
  className,
  valueSuffix = "",
}: {
  data: Point[];
  colors: string[];
  className?: string;
  valueSuffix?: string;
}) {
  const max = Math.max(...data.map((d) => d.value), 1);

  if (data.length === 0) {
    return <ChartEmpty className={className} />;
  }

  return (
    <ul className={cn("space-y-3.5", className)}>
      {data.map((point, index) => (
        <li key={`${point.label}-${index}`}>
          <div className="flex items-baseline justify-between gap-4">
            <span className="flex min-w-0 items-center gap-2">
              <span
                className="size-2 shrink-0 rounded-full"
                style={{ backgroundColor: colors[index] }}
                aria-hidden
              />
              <span className="truncate text-sm">{point.label}</span>
            </span>
            <span className="shrink-0 font-mono text-xs tabular">
              {point.value}
              {valueSuffix}
            </span>
          </div>
          <div
            className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-muted"
            role="img"
            aria-label={`${point.label}: ${point.value}${valueSuffix}`}
          >
            <div
              className="h-full rounded-full"
              style={{
                width: `${Math.max((point.value / max) * 100, 2)}%`,
                backgroundColor: colors[index],
              }}
            />
          </div>
          {point.hint && (
            <p className="mt-1 font-mono text-[11px] text-muted-foreground tabular">
              {point.hint}
            </p>
          )}
        </li>
      ))}
    </ul>
  );
}

// ---------------------------------------------------------------------------
// Sentiment split
// ---------------------------------------------------------------------------

/**
 * A single stacked bar for one three-part composition.
 *
 * Not a donut: comparing three angles is harder than comparing three lengths,
 * and the parts are named right underneath. Colours come from the semantic
 * sentiment tokens rather than the categorical palette — these are states, not
 * arbitrary series, and reusing a categorical hue for "negative" would let the
 * same colour mean two things in one dashboard.
 */
export function SentimentSplit({
  positive,
  neutral,
  negative,
  className,
}: {
  positive: number;
  neutral: number;
  negative: number;
  className?: string;
}) {
  const total = positive + neutral + negative;

  if (total === 0) {
    return <ChartEmpty className={className} />;
  }

  const parts = [
    { key: "positive", value: positive, className: "bg-positive", label: "Positive" },
    { key: "neutral", value: neutral, className: "bg-neutral", label: "Neutral" },
    { key: "negative", value: negative, className: "bg-negative", label: "Negative" },
  ].filter((part) => part.value > 0);

  return (
    <div className={className}>
      {/* gap-[2px] is the surface spacer between adjacent fills. */}
      <div
        className="flex h-2.5 gap-[2px] overflow-hidden rounded-full"
        role="img"
        aria-label={`${positive} positive, ${neutral} neutral, ${negative} negative`}
      >
        {parts.map((part) => (
          <span
            key={part.key}
            className={cn("h-full first:rounded-l-full last:rounded-r-full", part.className)}
            style={{ width: `${(part.value / total) * 100}%` }}
          />
        ))}
      </div>

      <ul className="mt-3 flex flex-wrap gap-x-5 gap-y-1.5">
        {[
          { label: "Positive", value: positive, dot: "bg-positive" },
          { label: "Neutral", value: neutral, dot: "bg-neutral" },
          { label: "Negative", value: negative, dot: "bg-negative" },
        ].map((entry) => (
          <li key={entry.label} className="flex items-center gap-1.5">
            <span className={cn("size-2 rounded-full", entry.dot)} aria-hidden />
            <span className="text-xs text-muted-foreground">{entry.label}</span>
            <span className="font-mono text-xs tabular">{entry.value}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function ChartEmpty({ className }: { className?: string }) {
  return (
    <p
      className={cn(
        "flex items-center justify-center rounded-md border border-dashed border-border py-8 text-xs text-muted-foreground",
        className,
      )}
    >
      Nothing to plot yet
    </p>
  );
}
