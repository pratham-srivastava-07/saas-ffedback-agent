"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { Layers, Scale } from "lucide-react";

import { PageHeader } from "@/components/app/shell";
import { EmptyState, ErrorState, SkeletonRows } from "@/components/app/states";
import { Sparkline } from "@/components/app/sparkline";
import { TrendBadge } from "@/components/app/signals";
import { FilterChips, SelectionBar, type FilterOption } from "@/components/app/patterns";
import { Button } from "@/components/ui/button";
import { api, type TrendDirection } from "@/lib/api";
import { useApi } from "@/lib/use-api";
import { percent, relativeTime } from "@/lib/format";
import { deriveDirection } from "@/lib/trend";
import { cn } from "@/lib/utils";

type Filter = "all" | TrendDirection;

const FILTER_ORDER: Filter[] = [
  "all",
  "spiking",
  "emerging",
  "steady",
  "declining",
  "insufficient_history",
];

const FILTER_LABELS: Record<Filter, string> = {
  all: "All",
  spiking: "Spiking",
  emerging: "Emerging",
  steady: "Steady",
  declining: "Declining",
  insufficient_history: "Too new to call",
};

export default function ThemesPage() {
  const { data, error, loading, reload } = useApi(() => api.themeTrends(50, 12), []);
  const [filter, setFilter] = useState<Filter>("all");
  const [selected, setSelected] = useState<Set<string>>(new Set());

  // Direction is derived once, here, so filtering and the badge can never
  // disagree about the same theme.
  const themes = useMemo(
    () =>
      (data ?? []).map((theme) => ({
        ...theme,
        direction: deriveDirection(theme.history),
      })),
    [data],
  );

  const options: FilterOption<Filter>[] = useMemo(
    () =>
      FILTER_ORDER.map((value) => ({
        value,
        label: FILTER_LABELS[value],
        count:
          value === "all"
            ? themes.length
            : themes.filter((theme) => theme.direction === value).length,
      })).filter((option) => option.value === "all" || option.count > 0),
    [themes],
  );

  const visible = useMemo(
    () =>
      filter === "all"
        ? themes
        : themes.filter((theme) => theme.direction === filter),
    [themes, filter],
  );

  function toggle(id: string) {
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  return (
    <>
      <PageHeader
        title="Themes"
        description="Everything this workspace has seen. A theme keeps its identity across runs, so the line shows real trajectory."
      />

      <div className="px-5 py-6 sm:px-8">
        {loading && <SkeletonRows rows={6} />}

        {error && <ErrorState message={error} onRetry={reload} />}

        {data && data.length === 0 && (
          <EmptyState
            icon={Layers}
            title="No themes yet"
            body="Themes appear once you analyse your first batch of feedback."
            actionLabel="Run an analysis"
            actionHref="/app"
          />
        )}

        {themes.length > 0 && (
          <>
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <FilterChips options={options} value={filter} onChange={setFilter} />
              <p className="font-mono text-[11px] text-muted-foreground tabular">
                {visible.length} of {themes.length}
              </p>
            </div>

            <div className="overflow-hidden rounded-lg border">
              {/* Column headers, so the numbers are named rather than guessed. */}
              <div className="hidden items-center gap-4 border-b border-border bg-muted/30 px-4 py-2 text-[11px] font-medium uppercase tracking-wide text-muted-foreground sm:flex sm:px-5">
                <span className="w-4" aria-hidden />
                <span className="flex-1">Theme</span>
                <span className="w-32 text-right">Trajectory</span>
                <span className="w-20 text-right">Last share</span>
                <span className="w-24 text-right">Mentions</span>
              </div>

              {visible.map((theme, index) => {
                const shares = theme.history.map((point) => point.share);
                const latest = theme.history[theme.history.length - 1];
                const isSelected = selected.has(theme.id);

                return (
                  <div
                    key={theme.id}
                    className={cn(
                      "flex flex-wrap items-center gap-x-4 gap-y-3 px-4 py-3.5 transition-colors sm:flex-nowrap sm:px-5",
                      index > 0 && "border-t border-border",
                      isSelected ? "bg-primary/5" : "bg-surface hover:bg-muted/30",
                    )}
                  >
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => toggle(theme.id)}
                      aria-label={`Select ${theme.name}`}
                      className="size-4 shrink-0 accent-primary"
                    />

                    <div className="min-w-0 flex-1">
                      <Link
                        href={`/app/themes/${encodeURIComponent(theme.id)}`}
                        className="font-display text-[15px] font-semibold tracking-tight hover:text-primary focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
                      >
                        {theme.name}
                      </Link>
                      <p className="mt-0.5 font-mono text-[11px] text-muted-foreground tabular">
                        {theme.run_count} {theme.run_count === 1 ? "run" : "runs"}
                        {latest && ` / last seen ${relativeTime(latest.at)}`}
                      </p>
                    </div>

                    <div className="flex w-32 justify-end">
                      <TrendBadge direction={theme.direction} />
                    </div>

                    <span className="w-20 text-right font-mono text-sm tabular">
                      {latest ? percent(latest.share) : "-"}
                    </span>

                    <div className="flex w-24 items-center justify-end gap-3">
                      <Sparkline values={shares} />
                      <span className="font-mono text-sm tabular">
                        {theme.total_mentions}
                      </span>
                    </div>
                  </div>
                );
              })}

              {visible.length === 0 && (
                <p className="bg-surface px-5 py-10 text-center text-sm text-muted-foreground">
                  No themes are {FILTER_LABELS[filter].toLowerCase()} right now.
                </p>
              )}
            </div>

            <SelectionBar count={selected.size} onClear={() => setSelected(new Set())}>
              <Button
                variant="outline"
                size="sm"
                className="h-7"
                disabled={selected.size < 2}
                title={
                  selected.size < 2
                    ? "Select at least two themes to compare"
                    : undefined
                }
              >
                <Scale className="size-3.5" aria-hidden />
                Compare
              </Button>
            </SelectionBar>
          </>
        )}
      </div>
    </>
  );
}
