"use client";

import Link from "next/link";
import { ChevronRight, Quote } from "lucide-react";

import type { Recommendation, Theme, Trend } from "@/lib/api";
import { ChurnFlag, SentimentBar, SeverityMarks, TrendBadge } from "@/components/app/signals";
import { cn } from "@/lib/utils";

/**
 * Ranked themes. Dense rows with hairline separation rather than cards: at this
 * density card chrome costs more than it communicates, and rows let the impact
 * figures line up into a readable column.
 */
export function ThemeTable({
  themes,
  trends,
  className,
}: {
  themes: Theme[];
  trends: Trend[];
  className?: string;
}) {
  const trendFor = new Map(trends.map((trend) => [trend.theme_id, trend]));

  return (
    <div className={cn("overflow-hidden rounded-lg border", className)}>
      {themes.map((theme, index) => {
        const trend = trendFor.get(theme.id);
        return (
          <div
            key={theme.id || index}
            className={cn(
              "group relative bg-surface px-4 py-4 sm:px-5",
              index > 0 && "border-t border-border",
            )}
          >
            <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-2">
              <div className="flex min-w-0 flex-1 items-start gap-3">
                <span className="mt-0.5 font-mono text-xs text-muted-foreground tabular">
                  {String(index + 1).padStart(2, "0")}
                </span>

                <div className="min-w-0">
                  {theme.id ? (
                    <Link
                      href={`/app/themes/${encodeURIComponent(theme.id)}`}
                      className="inline-flex items-center gap-1 rounded-sm font-display text-[15px] font-semibold tracking-tight hover:text-primary focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
                    >
                      {theme.name || "Unnamed theme"}
                      <ChevronRight className="size-3.5 opacity-0 transition-opacity group-hover:opacity-100" aria-hidden />
                    </Link>
                  ) : (
                    <span className="font-display text-[15px] font-semibold tracking-tight">
                      {theme.name || "Unnamed theme"}
                    </span>
                  )}

                  {theme.description && (
                    <p className="mt-1 max-w-[70ch] text-sm text-muted-foreground">
                      {theme.description}
                    </p>
                  )}
                </div>
              </div>

              <div className="flex shrink-0 items-center gap-2">
                {theme.churn_risk_count > 0 && (
                  <ChurnFlag count={theme.churn_risk_count} />
                )}
                {trend && (
                  <TrendBadge direction={trend.direction} ratio={trend.change_ratio} />
                )}
              </div>
            </div>

            <div className="mt-4 grid gap-4 pl-7 sm:grid-cols-4">
              <Metric label="Mentions" value={theme.count} />
              <Metric label="Impact" value={theme.impact_score} decimals={1} />
              <div>
                <p className="text-xs text-muted-foreground">Severity</p>
                <p className="mt-1 flex items-center gap-2 font-mono text-sm tabular">
                  {theme.avg_severity.toFixed(1)}
                  <SeverityMarks severity={Math.round(theme.avg_severity)} />
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Sentiment</p>
                <SentimentBar className="mt-1.5" breakdown={theme.sentiment_breakdown} />
              </div>
            </div>

            {trend && (
              <p className="mt-3 pl-7 text-xs text-muted-foreground">{trend.detail}</p>
            )}
          </div>
        );
      })}
    </div>
  );
}

function Metric({
  label,
  value,
  decimals = 0,
}: {
  label: string;
  value: number;
  decimals?: number;
}) {
  return (
    <div>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 font-mono text-sm tabular">{value.toFixed(decimals)}</p>
    </div>
  );
}

const EFFORT_STYLE: Record<string, string> = {
  low: "border-positive/35 text-positive",
  medium: "border-signal-new/40 text-signal-new",
  high: "border-border text-muted-foreground",
};

export function Recommendations({
  recommendations,
  themes,
  className,
}: {
  recommendations: Recommendation[];
  themes: Theme[];
  className?: string;
}) {
  if (recommendations.length === 0) return null;
  const nameFor = new Map(themes.map((theme) => [theme.id, theme.name]));

  return (
    <div className={cn("overflow-hidden rounded-lg border", className)}>
      {recommendations.map((rec, index) => (
        <div
          key={`${rec.title}-${index}`}
          className={cn("bg-surface px-4 py-4 sm:px-5", index > 0 && "border-t border-border")}
        >
          <div className="flex flex-wrap items-start justify-between gap-3">
            <h3 className="font-display text-[15px] font-semibold tracking-tight">
              {rec.title}
            </h3>
            <span
              className={cn(
                "rounded-md border px-2 py-0.5 font-mono text-[11px] uppercase tracking-wide",
                EFFORT_STYLE[rec.effort] ?? EFFORT_STYLE.high,
              )}
            >
              {rec.effort} effort
            </span>
          </div>

          <p className="mt-2 max-w-[75ch] text-sm leading-relaxed text-muted-foreground">
            {rec.rationale}
          </p>

          {rec.theme_ids.length > 0 && (
            <ul className="mt-3 flex flex-wrap gap-1.5">
              {rec.theme_ids.map((id) => (
                <li key={id}>
                  <Link
                    href={`/app/themes/${encodeURIComponent(id)}`}
                    className="rounded border border-border px-1.5 py-0.5 text-[11px] text-muted-foreground transition-colors hover:border-primary/50 hover:text-foreground"
                  >
                    {nameFor.get(id) ?? "linked theme"}
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      ))}
    </div>
  );
}

export function SummaryPanel({
  summary,
  className,
}: {
  summary: string;
  className?: string;
}) {
  if (!summary) return null;
  return (
    <div className={cn("rounded-lg border bg-surface-2/60 p-5 sm:p-6", className)}>
      <div className="flex items-start gap-3">
        <Quote className="mt-1 size-4 shrink-0 text-primary" aria-hidden />
        <p className="max-w-[72ch] text-base leading-relaxed">{summary}</p>
      </div>
    </div>
  );
}

/** Counts that only make sense together, so they are shown together. */
export function RunStats({
  analyzed,
  rejected,
  themes,
  revisions,
  className,
}: {
  analyzed: number;
  rejected: number;
  themes: number;
  revisions?: number;
  className?: string;
}) {
  const stats = [
    { label: "Analysed", value: analyzed },
    { label: "Rejected as noise", value: rejected },
    { label: "Themes", value: themes },
    ...(revisions !== undefined
      ? [{ label: "Audit passes", value: revisions }]
      : []),
  ];

  return (
    <dl className={cn("grid grid-cols-2 gap-px overflow-hidden rounded-lg border bg-border sm:grid-cols-4", className)}>
      {stats.map((stat) => (
        <div key={stat.label} className="bg-surface px-4 py-3.5">
          <dt className="text-xs text-muted-foreground">{stat.label}</dt>
          <dd className="mt-1 font-mono text-xl tabular">{stat.value}</dd>
        </div>
      ))}
    </dl>
  );
}
