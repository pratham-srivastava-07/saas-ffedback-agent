"use client";

import Link from "next/link";
import { Layers } from "lucide-react";

import { PageHeader } from "@/components/app/shell";
import { EmptyState, ErrorState, SkeletonRows } from "@/components/app/states";
import { Sparkline } from "@/components/app/sparkline";
import { api } from "@/lib/api";
import { useApi } from "@/lib/use-api";
import { percent, relativeTime } from "@/lib/format";

export default function ThemesPage() {
  const { data, error, loading, reload } = useApi(() => api.themeTrends(50, 12), []);

  return (
    <>
      <PageHeader
        title="Themes"
        description="Everything this workspace has seen, ranked by total mentions. A theme keeps its identity across runs, so the line shows real trajectory."
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

        {data && data.length > 0 && (
          <div className="overflow-hidden rounded-lg border">
            {data.map((theme, index) => {
              const shares = theme.history.map((point) => point.share);
              const latest = theme.history[theme.history.length - 1];

              return (
                <div
                  key={theme.id}
                  className={`bg-surface px-4 py-4 sm:px-5 ${index > 0 ? "border-t border-border" : ""}`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-3">
                    <div className="flex min-w-0 flex-1 items-baseline gap-3">
                      <span className="font-mono text-xs text-muted-foreground tabular">
                        {String(index + 1).padStart(2, "0")}
                      </span>
                      <div className="min-w-0">
                        <Link
                          href={`/app/themes/${encodeURIComponent(theme.id)}`}
                          className="font-display text-[15px] font-semibold tracking-tight hover:text-primary focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
                        >
                          {theme.name}
                        </Link>
                        <p className="mt-0.5 font-mono text-[11px] text-muted-foreground tabular">
                          {theme.total_mentions} mentions across {theme.run_count}{" "}
                          {theme.run_count === 1 ? "run" : "runs"}
                          {latest && ` / last seen ${relativeTime(latest.at)}`}
                        </p>
                      </div>
                    </div>

                    <div className="flex shrink-0 items-center gap-5">
                      {latest && (
                        <div className="text-right">
                          <p className="text-xs text-muted-foreground">Last share</p>
                          <p className="font-mono text-sm tabular">
                            {percent(latest.share)}
                          </p>
                        </div>
                      )}
                      <Sparkline values={shares} />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </>
  );
}
