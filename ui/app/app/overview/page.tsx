"use client";

import { useMemo } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  ArrowRight,
  Layers,
  MessageSquare,
  Play,
  ShieldAlert,
} from "lucide-react";

import { PageHeader } from "@/components/app/shell";
import { EmptyState, ErrorState, SkeletonCard, SkeletonRows } from "@/components/app/states";
import { RankedBars, SentimentSplit, VolumeBars } from "@/components/app/charts";
import { TrendBadge } from "@/components/app/signals";
import { DeltaBadge } from "@/components/app/patterns";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { useApi } from "@/lib/use-api";
import { colorAt } from "@/lib/chart-colors";
import { formatDate, relativeTime } from "@/lib/format";
import { cn } from "@/lib/utils";

/**
 * The overview.
 *
 * Every number here is derived from stored runs and themes — there is no
 * separate metrics table and nothing is precomputed, so the page cannot drift
 * from what the pipeline actually produced.
 */
export default function OverviewPage() {
  const runs = useApi(() => api.runs(50), []);
  const themes = useApi(() => api.themes(100), []);

  const latestId = runs.data?.find((run) => run.status === "completed")?.id ?? null;
  const latest = useApi(
    () => (latestId ? api.runResult(latestId) : Promise.resolve(null)),
    [latestId],
  );

  const stats = useMemo(() => {
    const list = runs.data ?? [];
    return {
      analysed: list.reduce((total, run) => total + run.item_count, 0),
      rejected: list.reduce((total, run) => total + run.rejected_count, 0),
      runs: list.length,
      themes: themes.data?.length ?? 0,
    };
  }, [runs.data, themes.data]);

  // The API returns runs newest first, so these are the last two.
  const latestVolume = runs.data?.[0]?.item_count ?? null;
  const previousVolume = runs.data?.[1]?.item_count ?? null;

  // Oldest first: a timeline that reads right-to-left is a lie about time.
  const volume = useMemo(
    () =>
      [...(runs.data ?? [])]
        .reverse()
        .map((run) => ({
          label: formatDate(run.created_at),
          value: run.item_count,
          hint: `${run.theme_count} themes`,
        })),
    [runs.data],
  );

  const topThemes = useMemo(() => {
    const ranked = [...(themes.data ?? [])].sort(
      (a, b) => b.total_mentions - a.total_mentions,
    );
    return ranked.slice(0, 6).map((theme, index) => ({
      id: theme.id,
      label: theme.name,
      value: theme.total_mentions,
      hint: `seen in ${theme.run_count} run${theme.run_count === 1 ? "" : "s"}`,
      color: colorAt(index),
    }));
  }, [themes.data]);

  const sentiment = useMemo(() => {
    const totals = { positive: 0, neutral: 0, negative: 0 };
    for (const theme of latest.data?.themes ?? []) {
      totals.positive += theme.sentiment_breakdown?.positive ?? 0;
      totals.neutral += theme.sentiment_breakdown?.neutral ?? 0;
      totals.negative += theme.sentiment_breakdown?.negative ?? 0;
    }
    return totals;
  }, [latest.data]);

  const churnRisk = useMemo(
    () =>
      (latest.data?.themes ?? []).reduce(
        (total, theme) => total + (theme.churn_risk_count ?? 0),
        0,
      ),
    [latest.data],
  );

  const loading = runs.loading || themes.loading;
  const error = runs.error ?? themes.error;

  if (!loading && !error && (runs.data?.length ?? 0) === 0) {
    return (
      <>
        <PageHeader title="Overview" description="Your workspace at a glance." />
        <div className="px-5 py-6 sm:px-8">
          <EmptyState
            icon={Play}
            title="No analyses yet"
            body="Run your first batch of feedback and this page fills in: volume over time, your biggest themes, and what changed."
            actionLabel="Run an analysis"
            actionHref="/app"
          />
        </div>
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Overview"
        description="Your workspace at a glance."
        actions={
          <Button asChild size="sm">
            <Link href="/app">
              <Play className="size-3.5" aria-hidden />
              New analysis
            </Link>
          </Button>
        }
      />

      <div className="space-y-6 px-5 py-6 sm:px-8">
        {error && <ErrorState message={error} onRetry={runs.reload} />}

        {/* Metric strip. Four is the ceiling before a row of numbers stops
            being scannable and becomes a wall. */}
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {loading ? (
            Array.from({ length: 4 }).map((_, index) => <SkeletonCard key={index} />)
          ) : (
            <>
              <StatTile
                icon={MessageSquare}
                label="Feedback analysed"
                value={stats.analysed}
                context={
                  latestVolume === null
                    ? `across ${stats.runs} run${stats.runs === 1 ? "" : "s"}`
                    : `latest run: ${latestVolume} items / ${stats.runs} runs total`
                }
                delta={
                  latestVolume === null ? undefined : (
                    // Compares the last two runs, not the cumulative total —
                    // the total only ever grows, so a delta on it means nothing.
                    // Volume itself is neither good nor bad, hence neutral.
                    <DeltaBadge
                      current={latestVolume}
                      previous={previousVolume}
                      goodWhen="neutral"
                    />
                  )
                }
              />
              <StatTile
                icon={Layers}
                label="Themes tracked"
                value={stats.themes}
                context="stable across runs"
              />
              <StatTile
                icon={ShieldAlert}
                label="Churn-risk mentions"
                value={churnRisk}
                context="in the latest run"
                emphasis={churnRisk > 0 ? "negative" : undefined}
              />
              <StatTile
                icon={AlertTriangle}
                label="Rejected as noise"
                value={stats.rejected}
                context="never reached the model"
              />
            </>
          )}
        </div>

        <div className="grid gap-6 xl:grid-cols-3">
          <section className="rounded-lg border bg-surface p-5 xl:col-span-2">
            <h2 className="font-display text-sm font-semibold tracking-tight">
              Volume over time
            </h2>
            <p className="mt-1 text-xs text-muted-foreground">
              Items analysed per run, oldest first.
            </p>
            <div className="mt-5">
              {loading ? <SkeletonRows rows={2} /> : <VolumeBars data={volume} />}
            </div>
          </section>

          <section className="rounded-lg border bg-surface p-5">
            <h2 className="font-display text-sm font-semibold tracking-tight">
              Sentiment, latest run
            </h2>
            <p className="mt-1 text-xs text-muted-foreground">
              {latest.data ? formatDate(latest.data.created_at) : "-"}
            </p>
            <div className="mt-5">
              {latest.loading ? (
                <SkeletonRows rows={2} />
              ) : (
                <SentimentSplit {...sentiment} />
              )}
            </div>
          </section>
        </div>

        <div className="grid gap-6 xl:grid-cols-3">
          <section className="rounded-lg border bg-surface p-5 xl:col-span-2">
            <div className="flex items-baseline justify-between gap-4">
              <h2 className="font-display text-sm font-semibold tracking-tight">
                Biggest themes
              </h2>
              <Link
                href="/app/themes"
                className="font-mono text-[11px] text-primary hover:underline"
              >
                all themes
              </Link>
            </div>
            <p className="mt-1 text-xs text-muted-foreground">
              By total mentions across every run in this workspace.
            </p>

            <div className="mt-5">
              {themes.loading ? (
                <SkeletonRows rows={5} />
              ) : (
                <RankedBars
                  data={topThemes}
                  colors={topThemes.map((theme) => theme.color)}
                />
              )}
            </div>
          </section>

          <section className="rounded-lg border bg-surface p-5">
            <div className="flex items-baseline justify-between gap-4">
              <h2 className="font-display text-sm font-semibold tracking-tight">
                Recent runs
              </h2>
              <Link
                href="/app/runs"
                className="font-mono text-[11px] text-primary hover:underline"
              >
                all runs
              </Link>
            </div>

            <ul className="mt-4 space-y-px">
              {(runs.data ?? []).slice(0, 6).map((run) => (
                <li key={run.id}>
                  <Link
                    href={`/app/runs/${encodeURIComponent(run.id)}`}
                    className="flex items-center gap-3 rounded-md px-2 py-2.5 transition-colors hover:bg-muted/50 focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-ring"
                  >
                    <span
                      className={cn(
                        "size-2 shrink-0 rounded-full",
                        run.status === "completed"
                          ? "bg-positive"
                          : run.status === "failed"
                            ? "bg-negative"
                            : "bg-signal-new",
                      )}
                      aria-hidden
                    />
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-sm">
                        {run.item_count} items · {run.theme_count} themes
                      </span>
                      <span className="font-mono text-[11px] text-muted-foreground tabular">
                        {relativeTime(run.created_at)}
                      </span>
                    </span>
                    <ArrowRight
                      className="size-3.5 shrink-0 text-muted-foreground"
                      aria-hidden
                    />
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        </div>

        {latest.data && latest.data.trends.length > 0 && (
          <section className="rounded-lg border bg-surface p-5">
            <h2 className="font-display text-sm font-semibold tracking-tight">
              What changed in the latest run
            </h2>
            <ul className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {latest.data.trends.slice(0, 6).map((trend) => (
                <li
                  key={trend.theme_id}
                  className="flex items-start justify-between gap-3 rounded-md border border-border px-3 py-2.5"
                >
                  <span className="min-w-0">
                    <Link
                      href={`/app/themes/${encodeURIComponent(trend.theme_id)}`}
                      className="block truncate text-sm hover:underline"
                    >
                      {trend.theme_name}
                    </Link>
                    <span className="mt-0.5 block font-mono text-[11px] text-muted-foreground">
                      {trend.detail}
                    </span>
                  </span>
                  <TrendBadge
                    direction={trend.direction}
                    ratio={trend.change_ratio}
                  />
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </>
  );
}

function StatTile({
  icon: Icon,
  label,
  value,
  context,
  emphasis,
  delta,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: number;
  context: string;
  emphasis?: "negative";
  delta?: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border bg-surface p-5">
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs text-muted-foreground">{label}</p>
        <Icon className="size-4 shrink-0 text-muted-foreground" aria-hidden />
      </div>
      <div className="mt-3 flex items-baseline gap-2.5">
        <p
          className={cn(
            "font-mono text-3xl leading-none tabular",
            emphasis === "negative" && "text-negative",
          )}
        >
          {value.toLocaleString()}
        </p>
        {/*
          Only tiles whose comparison is real carry a delta. A cumulative
          total always rises, so a percentage on one would be decoration
          dressed as insight.
        */}
        {delta}
      </div>
      <p className="mt-2 font-mono text-[11px] text-muted-foreground tabular">
        {context}
      </p>
    </div>
  );
}
