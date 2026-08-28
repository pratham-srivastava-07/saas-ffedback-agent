"use client";

/**
 * Feedback grouped by the part of the product it touches.
 *
 * The second cut of the same data as themes, and the one work is routed
 * along. A theme is one problem; an area is who owns it. One theme can span
 * several areas, and one area collects many themes, so the two lists answer
 * different questions and neither replaces the other.
 */

import Link from "next/link";
import { AlertTriangle, Layers } from "lucide-react";

import { SentimentSplit } from "@/components/app/charts";
import { EmptyState } from "@/components/app/states";
import { colorAt } from "@/lib/chart-colors";
import { percent, severityLabel } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { FeatureArea, FeatureAreasResponse } from "@/lib/api";

export function FeatureAreas({
  data,
  className,
}: {
  data: FeatureAreasResponse;
  className?: string;
}) {
  if (data.areas.length === 0) {
    return (
      <EmptyState
        icon={Layers}
        title="No product areas yet"
        body="Areas appear once feedback has been analysed. Each item is placed in the part of the product it refers to."
        actionLabel="Run an analysis"
        actionHref="/app"
        className={className}
      />
    );
  }

  const classified = data.total_items - data.unclassified;

  return (
    <div className={cn("space-y-6", className)}>
      <Coverage
        classified={classified}
        unclassified={data.unclassified}
        total={data.total_items}
      />

      <ul className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
        {data.areas.map((area, index) => (
          <AreaCard key={area.name} area={area} color={colorAt(index)} />
        ))}
      </ul>
    </div>
  );
}

/**
 * How much of the corpus actually got placed.
 *
 * Shown first, and shown even when it is unflattering. The unclassified
 * bucket is frequently the largest single group, and a reader who cannot see
 * it has no way to judge how complete the rest of the page is.
 */
function Coverage({
  classified,
  unclassified,
  total,
}: {
  classified: number;
  unclassified: number;
  total: number;
}) {
  const covered = total ? classified / total : 0;

  return (
    <div className="rounded-lg border bg-surface p-5">
      <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-2">
        <div>
          <h2 className="font-display text-sm font-semibold tracking-tight">
            Coverage
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {classified.toLocaleString()} of {total.toLocaleString()} analysed
            items were placed in a product area.
          </p>
        </div>
        <span className="font-mono text-2xl leading-none tabular">
          {percent(covered)}
        </span>
      </div>

      <div
        className="mt-4 flex h-1.5 gap-[2px] overflow-hidden rounded-full"
        role="img"
        aria-label={`${classified} placed, ${unclassified} unplaced`}
      >
        <span
          className="h-full rounded-l-full bg-primary"
          style={{ width: `${covered * 100}%` }}
        />
        <span className="h-full flex-1 rounded-r-full bg-muted" />
      </div>

      {unclassified > 0 && (
        <p className="mt-3 font-mono text-[11px] leading-relaxed text-muted-foreground">
          {unclassified.toLocaleString()} could not be placed. Those are counted
          here but never ranked as an area, because &quot;unknown&quot; is not a
          part of the product.
        </p>
      )}
    </div>
  );
}

function AreaCard({ area, color }: { area: FeatureArea; color: string }) {
  return (
    <li className="flex flex-col rounded-lg border bg-surface p-5">
      <div className="flex items-start justify-between gap-3">
        <span className="flex min-w-0 items-center gap-2.5">
          <span
            className="size-2.5 shrink-0 rounded-full"
            style={{ backgroundColor: color }}
            aria-hidden
          />
          <span className="truncate font-display text-[15px] font-semibold capitalize tracking-tight">
            {area.name}
          </span>
        </span>

        {area.churn_risk_count > 0 && (
          <span className="inline-flex shrink-0 items-center gap-1 rounded-md border border-negative/35 px-1.5 py-0.5 font-mono text-[11px] text-negative tabular">
            <AlertTriangle className="size-3" aria-hidden />
            {area.churn_risk_count} at risk
          </span>
        )}
      </div>

      <dl className="mt-4 grid grid-cols-3 gap-3">
        <Stat label="Mentions" value={area.mentions.toLocaleString()} />
        <Stat label="Share" value={percent(area.share)} />
        <Stat label="Severity" value={severityLabel(area.avg_severity)} />
      </dl>

      <div className="mt-4">
        <SentimentSplit
          positive={area.sentiment.positive ?? 0}
          neutral={area.sentiment.neutral ?? 0}
          negative={area.sentiment.negative ?? 0}
        />
      </div>

      {area.themes.length > 0 && (
        <div className="mt-4 border-t border-border pt-3">
          <p className="font-mono text-[11px] text-muted-foreground">
            Top themes here
          </p>
          <ul className="mt-2 space-y-1">
            {area.themes.map((theme) => (
              <li key={theme.id}>
                <Link
                  href={`/app/themes/${encodeURIComponent(theme.id)}`}
                  className="flex items-baseline justify-between gap-3 rounded px-1 py-0.5 text-sm hover:bg-muted/50 focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-ring"
                >
                  <span className="min-w-0 truncate">{theme.name}</span>
                  <span className="shrink-0 font-mono text-[11px] text-muted-foreground tabular">
                    {theme.mentions}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </li>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="font-mono text-[11px] text-muted-foreground">{label}</dt>
      <dd className="mt-0.5 font-mono text-sm tabular">{value}</dd>
    </div>
  );
}
