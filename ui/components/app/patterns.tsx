"use client";

/**
 * Interface primitives borrowed from the agent-UI patterns at
 * beautiful-ui-five.vercel.app, adapted to this product's data.
 *
 * The ideas taken: a loading state that reports elapsed time rather than
 * spinning anonymously, chip filters that re-cut a table in place, a
 * selection bar that appears only when a selection exists, an expandable
 * trace so a pipeline stage can be inspected instead of merely watched, and
 * an insight delta that says which way a number moved.
 */

import { useEffect, useRef, useState } from "react";
import { ChevronRight, Loader2, Minus, TrendingDown, TrendingUp, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

/* -------------------------------------------------------------------------
 * Loading state — elapsed time, not an anonymous spinner
 * ---------------------------------------------------------------------- */

/**
 * A run takes tens of seconds. A spinner alone gives no way to tell "working"
 * from "hung", so this counts up: the number moving is the proof of life.
 */
export function ElapsedTimer({
  running,
  className,
}: {
  running: boolean;
  className?: string;
}) {
  const [elapsed, setElapsed] = useState(0);
  const startedAt = useRef<number | null>(null);

  useEffect(() => {
    if (!running) {
      startedAt.current = null;
      return;
    }
    startedAt.current = Date.now();
    setElapsed(0);
    const timer = window.setInterval(() => {
      if (startedAt.current) {
        setElapsed((Date.now() - startedAt.current) / 1000);
      }
    }, 100);
    return () => window.clearInterval(timer);
  }, [running]);

  if (!running) return null;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 font-mono text-xs text-muted-foreground tabular",
        className,
      )}
      // Announced once, not on every tick — a live region updating ten times
      // a second would make a screen reader unusable.
      aria-label="Analysis in progress"
    >
      <Loader2 className="size-3 animate-spin" aria-hidden />
      <span aria-hidden>{elapsed.toFixed(1)}s</span>
    </span>
  );
}

/** Shimmer bar for a value that has not arrived yet. */
export function Shimmer({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "inline-block animate-pulse rounded bg-muted align-middle",
        className,
      )}
      aria-hidden
    />
  );
}

/* -------------------------------------------------------------------------
 * Insight delta
 * ---------------------------------------------------------------------- */

/**
 * Which way a number moved, versus what.
 *
 * `goodWhen` exists because direction is not meaning: more feedback analysed
 * is good, more churn-risk mentions is not. Colour follows the meaning, and
 * an arrow plus text carries it too, so the signal is never colour alone.
 */
export function DeltaBadge({
  current,
  previous,
  goodWhen = "up",
  suffix = "",
  className,
}: {
  current: number;
  previous: number | null | undefined;
  goodWhen?: "up" | "down" | "neutral";
  suffix?: string;
  className?: string;
}) {
  if (previous === null || previous === undefined || previous === 0) {
    return (
      <span className={cn("font-mono text-[11px] text-muted-foreground", className)}>
        no prior run
      </span>
    );
  }

  const change = ((current - previous) / previous) * 100;
  const flat = Math.abs(change) < 1;
  const up = change > 0;

  const good =
    goodWhen === "neutral" ? null : goodWhen === "up" ? up : !up;

  const Icon = flat ? Minus : up ? TrendingUp : TrendingDown;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 font-mono text-[11px] tabular",
        flat || good === null
          ? "text-muted-foreground"
          : good
            ? "text-positive"
            : "text-negative",
        className,
      )}
    >
      <Icon className="size-3" aria-hidden />
      {flat ? "flat" : `${up ? "+" : ""}${change.toFixed(0)}%${suffix}`}
      <span className="sr-only">versus the previous run</span>
    </span>
  );
}

/* -------------------------------------------------------------------------
 * Chip filters
 * ---------------------------------------------------------------------- */

export interface FilterOption<T extends string> {
  value: T;
  label: string;
  count: number;
}

/**
 * Chip filters that re-cut a table in place.
 *
 * Counts sit on the chips so an empty result is predictable before you click
 * it — nobody should have to select a filter to discover it matches nothing.
 */
export function FilterChips<T extends string>({
  options,
  value,
  onChange,
  className,
}: {
  options: FilterOption<T>[];
  value: T;
  onChange: (value: T) => void;
  className?: string;
}) {
  return (
    <div
      role="tablist"
      aria-label="Filter"
      className={cn("flex flex-wrap items-center gap-1.5", className)}
    >
      {options.map((option) => {
        const active = option.value === value;
        return (
          <button
            key={option.value}
            role="tab"
            type="button"
            aria-selected={active}
            disabled={option.count === 0 && !active}
            onClick={() => onChange(option.value)}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs transition-colors",
              "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring",
              "disabled:cursor-not-allowed disabled:opacity-40",
              active
                ? "border-primary/40 bg-primary/10 font-medium text-foreground"
                : "border-border text-muted-foreground hover:border-border hover:text-foreground",
            )}
          >
            {option.label}
            <span className="font-mono text-[10px] tabular opacity-70">
              {option.count}
            </span>
          </button>
        );
      })}
    </div>
  );
}

/* -------------------------------------------------------------------------
 * Selection actions
 * ---------------------------------------------------------------------- */

/**
 * Appears only once something is selected, so it costs no space at rest.
 * Sticky rather than fixed: it stays with the table it acts on.
 */
export function SelectionBar({
  count,
  onClear,
  children,
  className,
}: {
  count: number;
  onClear: () => void;
  children?: React.ReactNode;
  className?: string;
}) {
  if (count === 0) return null;

  return (
    <div
      role="status"
      className={cn(
        "sticky bottom-4 z-20 mx-auto flex w-fit items-center gap-3 rounded-full border border-border bg-surface/95 px-4 py-2 shadow-lg backdrop-blur",
        className,
      )}
    >
      <span className="font-mono text-xs tabular">
        {count} selected
      </span>
      {children}
      <Button
        variant="ghost"
        size="sm"
        onClick={onClear}
        className="h-7 px-2 text-muted-foreground"
      >
        <X className="size-3.5" aria-hidden />
        Clear
      </Button>
    </div>
  );
}

/* -------------------------------------------------------------------------
 * Expandable trace
 * ---------------------------------------------------------------------- */

/**
 * A stage you can open rather than only watch.
 *
 * Uses native details/summary so it is keyboard-operable and expandable
 * before hydration, without a disclosure state to manage.
 */
export function TraceDisclosure({
  summary,
  meta,
  children,
  className,
}: {
  summary: React.ReactNode;
  meta?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <details className={cn("group", className)}>
      <summary className="flex cursor-pointer list-none items-center gap-2 rounded-md px-2 py-1.5 text-sm hover:bg-muted/40 focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-ring [&::-webkit-details-marker]:hidden">
        <ChevronRight
          className="size-3.5 shrink-0 text-muted-foreground transition-transform group-open:rotate-90"
          aria-hidden
        />
        <span className="min-w-0 flex-1">{summary}</span>
        {meta && <span className="shrink-0">{meta}</span>}
      </summary>
      <div className="border-l border-border pb-2 pl-4 pt-1 ml-4 text-sm text-muted-foreground">
        {children}
      </div>
    </details>
  );
}
