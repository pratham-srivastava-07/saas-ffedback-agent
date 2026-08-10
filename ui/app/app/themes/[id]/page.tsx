"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, MessageSquare } from "lucide-react";

import { PageHeader } from "@/components/app/shell";
import { EmptyState, ErrorState, SkeletonRows } from "@/components/app/states";
import { SentimentDot } from "@/components/app/signals";
import { Button } from "@/components/ui/button";
import { api, type StoredItem, type ThemeItemsResponse } from "@/lib/api";
import { severityLabel } from "@/lib/format";

const PAGE_SIZE = 25;

/**
 * The evidence behind a theme.
 *
 * This page is the product's promise. A ranked list saying "34 mentions" is
 * only trustworthy if you can read the 34, so this is where a count stops
 * being an assertion and becomes something a person can check.
 */
export default function ThemeDetailPage() {
  const params = useParams<{ id: string }>();
  const themeId = params?.id ?? "";

  const [pages, setPages] = useState<ThemeItemsResponse[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);

  const loadPage = useCallback(
    async (offset: number) => {
      const response = await api.themeItems(themeId, PAGE_SIZE, offset);
      setPages((previous) =>
        offset === 0 ? [response] : [...previous, response],
      );
      return response;
    },
    [themeId],
  );

  useEffect(() => {
    if (!themeId) return;
    let cancelled = false;

    setLoading(true);
    setError(null);
    setPages([]);

    loadPage(0)
      .catch((caught: Error) => {
        if (!cancelled) setError(caught.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [themeId, loadPage]);

  const theme = pages[0]?.theme;
  const total = pages[0]?.total ?? 0;
  const items: StoredItem[] = pages.flatMap((page) => page.items);
  const hasMore = items.length < total;

  async function loadMore() {
    setLoadingMore(true);
    try {
      await loadPage(items.length);
    } catch (caught) {
      setError((caught as Error).message);
    } finally {
      setLoadingMore(false);
    }
  }

  return (
    <>
      <PageHeader
        title={theme?.name ?? "Theme"}
        description={theme?.description || undefined}
        actions={
          <Button asChild variant="outline" size="sm">
            <Link href="/app/themes">
              <ArrowLeft className="size-3.5" aria-hidden />
              All themes
            </Link>
          </Button>
        }
      />

      <div className="px-5 py-6 sm:px-8">
        {theme && (
          <p className="mb-5 font-mono text-xs text-muted-foreground tabular">
            {theme.total_mentions} mentions across {theme.run_count}{" "}
            {theme.run_count === 1 ? "run" : "runs"}
            {total > 0 && ` / showing ${items.length} of ${total}`}
          </p>
        )}

        {loading && <SkeletonRows rows={6} />}

        {error && !loading && (
          <ErrorState message={error} onRetry={() => loadPage(0)} />
        )}

        {!loading && !error && items.length === 0 && (
          <EmptyState
            icon={MessageSquare}
            title="No feedback stored for this theme"
            body="The theme exists in the taxonomy, but none of its items are in this workspace's history."
            actionLabel="Back to themes"
            actionHref="/app/themes"
          />
        )}

        {items.length > 0 && (
          <>
            <ul className="overflow-hidden rounded-lg border">
              {items.map((item, index) => (
                <li
                  key={`${item.run_id}-${item.id}-${index}`}
                  className={`bg-surface px-4 py-4 sm:px-5 ${
                    index > 0 ? "border-t border-border" : ""
                  }`}
                >
                  <p className="text-sm leading-relaxed text-foreground">
                    {item.text}
                  </p>

                  <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1.5 font-mono text-[11px] text-muted-foreground tabular">
                    <span className="flex items-center gap-1.5">
                      <SentimentDot sentiment={item.sentiment} />
                      {item.sentiment ?? "unrated"}
                    </span>
                    <span>{severityLabel(item.severity)}</span>
                    <span>{item.user_type}</span>
                    <span>{item.source}</span>
                    {item.churn_risk && (
                      <span className="text-negative">churn risk</span>
                    )}
                    <Link
                      href={`/app/runs/${encodeURIComponent(item.run_id)}`}
                      className="ml-auto hover:text-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
                    >
                      view run
                    </Link>
                  </div>
                </li>
              ))}
            </ul>

            {hasMore && (
              <div className="mt-5 flex justify-center">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={loadMore}
                  disabled={loadingMore}
                >
                  {loadingMore
                    ? "Loading..."
                    : `Load ${Math.min(PAGE_SIZE, total - items.length)} more`}
                </Button>
              </div>
            )}
          </>
        )}
      </div>
    </>
  );
}
