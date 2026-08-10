"use client";

import Link from "next/link";
import { History } from "lucide-react";

import { PageHeader } from "@/components/app/shell";
import { EmptyState, ErrorState, SkeletonRows } from "@/components/app/states";
import { api } from "@/lib/api";
import { useApi } from "@/lib/use-api";
import { formatDate, relativeTime } from "@/lib/format";

const STATUS_STYLES: Record<string, string> = {
  completed: "text-positive",
  failed: "text-negative",
  running: "text-signal-new",
};

export default function RunsPage() {
  const { data, error, loading, reload } = useApi(() => api.runs(50), []);

  return (
    <>
      <PageHeader
        title="Runs"
        description="Every analysis this workspace has performed. Open one to see it exactly as it was ranked at the time."
      />

      <div className="px-5 py-6 sm:px-8">
        {loading && <SkeletonRows rows={5} />}

        {error && <ErrorState message={error} onRetry={reload} />}

        {data && data.length === 0 && (
          <EmptyState
            icon={History}
            title="No runs yet"
            body="Analyse a batch of feedback and it will appear here."
            actionLabel="Run an analysis"
            actionHref="/app"
          />
        )}

        {data && data.length > 0 && (
          <div className="overflow-hidden rounded-lg border">
            {data.map((run, index) => (
              <Link
                key={run.id}
                href={`/app/runs/${encodeURIComponent(run.id)}`}
                className={`block bg-surface px-4 py-4 transition-colors hover:bg-muted/40 focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-ring sm:px-5 ${
                  index > 0 ? "border-t border-border" : ""
                }`}
              >
                <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-2">
                  <div className="min-w-0 flex-1">
                    <p className="font-display text-[15px] font-semibold tracking-tight">
                      {formatDate(run.created_at)}
                      <span className="ml-2 font-mono text-[11px] font-normal text-muted-foreground">
                        {relativeTime(run.created_at)}
                      </span>
                    </p>
                    {run.summary && (
                      <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">
                        {run.summary}
                      </p>
                    )}
                    {run.error && (
                      <p className="mt-1 text-sm text-negative">{run.error}</p>
                    )}
                  </div>

                  <div className="flex shrink-0 items-center gap-5 font-mono text-[11px] tabular">
                    <span className={STATUS_STYLES[run.status] ?? "text-muted-foreground"}>
                      {run.status}
                    </span>
                    <span className="text-muted-foreground">
                      {run.item_count} analysed
                    </span>
                    {run.rejected_count > 0 && (
                      <span className="text-muted-foreground">
                        {run.rejected_count} rejected
                      </span>
                    )}
                    <span className="text-muted-foreground">
                      {run.theme_count} themes
                    </span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
