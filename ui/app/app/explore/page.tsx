"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Boxes } from "lucide-react";

import { PageHeader } from "@/components/app/shell";
import { EmptyState, ErrorState, SkeletonRows } from "@/components/app/states";
import { SentimentDot } from "@/components/app/signals";
import { ScatterField } from "@/components/three/webgl-slot";
import { colorForTheme } from "@/lib/cluster-colors";
import { api, type ScatterPoint } from "@/lib/api";
import { useApi } from "@/lib/use-api";
import { formatDate, severityLabel } from "@/lib/format";

/**
 * The embedding space, made navigable.
 *
 * Coordinates are real PCA projections stored at analysis time. PCA is fit per
 * run, so each run has its own basis — the run selector re-fetches rather than
 * transitioning, because animating between two bases would be pure artefact.
 */
export default function ExplorePage() {
  const searchParams = useSearchParams();
  const requestedRun = searchParams.get("run");

  const runs = useApi(() => api.runs(50), []);
  const [runId, setRunId] = useState<string | null>(requestedRun);

  // Default to the most recent run that actually produced points.
  useEffect(() => {
    if (runId || !runs.data) return;
    const usable = runs.data.find(
      (run) => run.status === "completed" && run.item_count > 0,
    );
    if (usable) setRunId(usable.id);
  }, [runs.data, runId]);

  const scatter = useApi(
    () => (runId ? api.runScatter(runId) : Promise.resolve(null)),
    [runId],
  );

  const [selected, setSelected] = useState<ScatterPoint | null>(null);
  const [focusThemeId, setFocusThemeId] = useState<string | null>(null);

  useEffect(() => {
    setSelected(null);
    setFocusThemeId(null);
  }, [runId]);

  const themeOrder = useMemo(
    () => scatter.data?.themes.map((theme) => theme.id) ?? [],
    [scatter.data],
  );

  const points = scatter.data?.points ?? [];
  const loading = runs.loading || (Boolean(runId) && scatter.loading);
  const error = runs.error ?? scatter.error;

  return (
    <>
      <PageHeader
        title="Explore"
        description="Each dot is one piece of feedback, positioned by meaning. Clusters are themes."
        actions={
          runs.data && runs.data.length > 0 ? (
            <select
              value={runId ?? ""}
              onChange={(event) => setRunId(event.target.value || null)}
              aria-label="Choose a run"
              className="h-8 rounded-md border border-input bg-transparent px-2 font-mono text-xs shadow-xs focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
            >
              {runs.data
                .filter((run) => run.item_count > 0)
                .map((run) => (
                  <option key={run.id} value={run.id}>
                    {formatDate(run.created_at)} — {run.item_count} items
                  </option>
                ))}
            </select>
          ) : undefined
        }
      />

      <div className="px-5 py-6 sm:px-8">
        {loading && <SkeletonRows rows={4} />}

        {error && !loading && (
          <ErrorState
            message={error}
            onRetry={() => (runId ? scatter.reload() : runs.reload())}
          />
        )}

        {!loading && !error && points.length === 0 && (
          <EmptyState
            icon={Boxes}
            title="Nothing to plot yet"
            body="The explorer needs a completed run with stored feedback. Analyse a batch and it will appear here."
            actionLabel="Run an analysis"
            actionHref="/app"
          />
        )}

        {!loading && points.length > 0 && (
          <div className="grid gap-6 lg:grid-cols-[1fr_20rem]">
            <div className="min-w-0">
              <ScatterField
                className="h-[26rem] overflow-hidden rounded-lg border bg-surface sm:h-[34rem]"
                points={points}
                themeOrder={themeOrder}
                selectedId={selected?.item_id ?? null}
                onSelect={setSelected}
                focusThemeId={focusThemeId}
                fallback={
                  <div className="flex h-full items-center justify-center px-6 text-center">
                    <p className="max-w-xs text-sm text-muted-foreground">
                      This device has no WebGL, so the 3D view is unavailable.
                      The themes and their feedback are all listed alongside.
                    </p>
                  </div>
                }
              />

              {/*
                The axes are principal components and carry no nameable
                meaning, so they are left unlabelled. Saying so is more honest
                than drawing axes that invite a reading they cannot support.
              */}
              <p className="mt-3 font-mono text-[11px] leading-relaxed text-muted-foreground">
                Positions are a PCA projection of the embedding space. The axes
                have no individual meaning — only the distances between points
                do. Coordinates are fit per run and are not comparable between
                runs.
              </p>
            </div>

            <aside className="space-y-5">
              {selected ? (
                <div className="rounded-lg border bg-surface p-4">
                  <div className="flex items-center justify-between gap-3">
                    <h2 className="font-display text-sm font-semibold">
                      Selected feedback
                    </h2>
                    <button
                      type="button"
                      onClick={() => setSelected(null)}
                      className="font-mono text-[11px] text-muted-foreground hover:text-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
                    >
                      clear
                    </button>
                  </div>
                  <p className="mt-3 text-sm leading-relaxed">{selected.text}</p>
                  <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1.5 font-mono text-[11px] text-muted-foreground tabular">
                    <span className="flex items-center gap-1.5">
                      <SentimentDot sentiment={selected.sentiment} />
                      {selected.sentiment ?? "unrated"}
                    </span>
                    <span>{severityLabel(selected.severity)}</span>
                  </div>
                  {selected.theme_id && (
                    <Link
                      href={`/app/themes/${encodeURIComponent(selected.theme_id)}`}
                      className="mt-3 inline-block font-mono text-[11px] text-primary hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
                    >
                      {selected.theme_name} →
                    </Link>
                  )}
                </div>
              ) : (
                <div className="rounded-lg border border-dashed border-border p-4">
                  <p className="text-sm text-muted-foreground">
                    Click any dot to read the feedback behind it.
                  </p>
                </div>
              )}

              <div className="rounded-lg border bg-surface p-4">
                <h2 className="font-display text-sm font-semibold">Themes</h2>
                <p className="mt-1 font-mono text-[11px] text-muted-foreground tabular">
                  {points.length} of this run&apos;s items are plotted
                </p>
                <ul className="mt-3 space-y-1">
                  {scatter.data?.themes.map((theme) => {
                    const active = focusThemeId === theme.id;
                    return (
                      <li key={theme.id}>
                        <button
                          type="button"
                          onClick={() =>
                            setFocusThemeId(active ? null : theme.id)
                          }
                          aria-pressed={active}
                          className={`flex w-full items-center gap-2.5 rounded-md px-2 py-1.5 text-left transition-colors hover:bg-muted/50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring ${
                            active ? "bg-muted" : ""
                          }`}
                        >
                          <span
                            className="size-2.5 shrink-0 rounded-full"
                            style={{
                              backgroundColor: colorForTheme(
                                theme.id,
                                themeOrder,
                              ),
                            }}
                            aria-hidden
                          />
                          <span className="min-w-0 flex-1 truncate text-sm">
                            {theme.name}
                          </span>
                          <span className="font-mono text-[11px] text-muted-foreground tabular">
                            {theme.count}
                          </span>
                        </button>
                      </li>
                    );
                  })}
                </ul>
              </div>
            </aside>
          </div>
        )}
      </div>
    </>
  );
}
