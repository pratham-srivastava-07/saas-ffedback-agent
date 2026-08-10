"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, Boxes } from "lucide-react";

import { PageHeader } from "@/components/app/shell";
import { ErrorState, SkeletonRows } from "@/components/app/states";
import { Recommendations, ThemeTable } from "@/components/app/results";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { useApi } from "@/lib/use-api";
import { formatDate } from "@/lib/format";

/**
 * A past run, replayed.
 *
 * Themes, trends and recommendations are read back from storage rather than
 * recomputed, so this shows what was actually reported at the time — including
 * a trend verdict that later runs may have superseded.
 */
export default function RunDetailPage() {
  const params = useParams<{ id: string }>();
  const runId = params?.id ?? "";

  const { data, error, loading, reload } = useApi(
    () => api.runResult(runId),
    [runId],
  );

  return (
    <>
      <PageHeader
        title={data ? formatDate(data.created_at) : "Run"}
        description={data?.summary ?? undefined}
        actions={
          <div className="flex gap-2">
            {data && data.item_count > 0 && (
              <Button asChild variant="outline" size="sm">
                <Link href={`/app/explore?run=${encodeURIComponent(runId)}`}>
                  <Boxes className="size-3.5" aria-hidden />
                  Explore in 3D
                </Link>
              </Button>
            )}
            <Button asChild variant="outline" size="sm">
              <Link href="/app/runs">
                <ArrowLeft className="size-3.5" aria-hidden />
                All runs
              </Link>
            </Button>
          </div>
        }
      />

      <div className="space-y-8 px-5 py-6 sm:px-8">
        {loading && <SkeletonRows rows={5} />}

        {error && <ErrorState message={error} onRetry={reload} />}

        {data && (
          <>
            <div className="flex flex-wrap gap-x-8 gap-y-2 font-mono text-xs text-muted-foreground tabular">
              <span>{data.item_count} analysed</span>
              <span>{data.rejected_count} rejected as noise</span>
              <span>{data.theme_count} themes</span>
              <span>status: {data.status}</span>
            </div>

            {data.error && <ErrorState message={data.error} />}

            {data.themes.length > 0 && (
              <ThemeTable themes={data.themes} trends={data.trends} />
            )}

            {data.recommendations.length > 0 && (
              <Recommendations
                recommendations={data.recommendations}
                themes={data.themes}
              />
            )}

            {data.themes.length === 0 && !data.error && (
              <p className="rounded-lg border border-dashed border-border px-6 py-12 text-center text-sm text-muted-foreground">
                This run produced no themes. Everything submitted was either a
                duplicate or rejected as noise.
              </p>
            )}
          </>
        )}
      </div>
    </>
  );
}
