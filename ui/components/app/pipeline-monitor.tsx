"use client";

import { Check, CircleDashed, Loader2, SkipForward } from "lucide-react";

import { cn } from "@/lib/utils";

/**
 * Live view of a graph run.
 *
 * Nodes are listed in execution order, which is deliberately NOT the order the
 * `run_start` frame sends them in (that list is alphabetical). Showing an
 * alphabetical pipeline would misrepresent how the run actually proceeds.
 *
 * Two structures in the graph are worth showing rather than hiding: `triage`
 * can short-circuit straight to `summarize` when a batch is all noise, and
 * `critique` can send `recommend` round again. A node that runs twice is
 * reported as such instead of silently resetting.
 */

export type NodeState = "pending" | "running" | "done" | "skipped";

export interface NodeProgress {
  state: NodeState;
  stats?: Record<string, number | boolean>;
  completed?: number;
  runs: number;
}

export const PIPELINE_ORDER = [
  "normalize",
  "triage",
  "analyze_one",
  "embed",
  "cluster",
  "resolve_taxonomy",
  "name_themes",
  "prioritize",
  "detect_trends",
  "recommend",
  "critique",
  "summarize",
] as const;

const NODE_COPY: Record<string, { label: string; detail: string }> = {
  normalize: { label: "Clean", detail: "Trim and drop duplicates" },
  triage: { label: "Triage", detail: "Reject noise" },
  analyze_one: { label: "Read each item", detail: "One structured call per item" },
  embed: { label: "Embed", detail: "One batched call" },
  cluster: { label: "Cluster", detail: "Group by meaning" },
  resolve_taxonomy: { label: "Match themes", detail: "Against themes on file" },
  name_themes: { label: "Name new themes", detail: "Only genuinely new clusters" },
  prioritize: { label: "Rank", detail: "Reach, severity, churn risk" },
  detect_trends: { label: "Detect trends", detail: "Against prior runs" },
  recommend: { label: "Recommend", detail: "Actions from the evidence" },
  critique: { label: "Audit", detail: "Check claims against evidence" },
  summarize: { label: "Summarize", detail: "The brief" },
};

const STAT_LABEL: Record<string, string> = {
  clean: "kept",
  rejected: "rejected",
  embeddings: "embedded",
  clusters: "clusters",
  themes: "themes",
  trends: "trends",
  recommendations: "actions",
  approved: "approved",
};

export function formatStats(progress: NodeProgress): string | null {
  if (progress.completed !== undefined) {
    return `${progress.completed} done`;
  }
  if (!progress.stats) return null;

  const parts = Object.entries(progress.stats).map(([key, value]) => {
    const label = STAT_LABEL[key] ?? key;
    if (typeof value === "boolean") return value ? label : `not ${label}`;
    return `${value} ${label}`;
  });

  return parts.length ? parts.join(", ") : null;
}

function StateIcon({ state }: { state: NodeState }) {
  if (state === "running") {
    return <Loader2 className="size-4 animate-spin text-primary" aria-hidden />;
  }
  if (state === "done") {
    return <Check className="size-4 text-positive" aria-hidden />;
  }
  if (state === "skipped") {
    return <SkipForward className="size-4 text-muted-foreground/60" aria-hidden />;
  }
  return <CircleDashed className="size-4 text-muted-foreground/40" aria-hidden />;
}

export function PipelineMonitor({
  progress,
  className,
}: {
  progress: Record<string, NodeProgress>;
  className?: string;
}) {
  return (
    <ol className={cn("relative", className)} aria-label="Pipeline progress">
      {PIPELINE_ORDER.map((node, index) => {
        const state = progress[node]?.state ?? "pending";
        const entry = progress[node];
        const stats = entry ? formatStats(entry) : null;
        const copy = NODE_COPY[node];
        const last = index === PIPELINE_ORDER.length - 1;

        return (
          <li key={node} className="relative flex gap-3 pb-1">
            {/* Rail. Solid behind completed work, faint ahead of it. */}
            {!last && (
              <span
                aria-hidden
                className={cn(
                  "absolute left-[7px] top-6 h-[calc(100%-0.75rem)] w-px",
                  state === "done" || state === "skipped"
                    ? "bg-border"
                    : "bg-border/50",
                )}
              />
            )}

            <span className="relative z-10 mt-1 flex size-4 shrink-0 items-center justify-center bg-surface">
              <StateIcon state={state} />
            </span>

            <div
              className={cn(
                "min-w-0 flex-1 rounded-md px-2.5 py-1.5 transition-colors",
                state === "running" && "bg-primary/8",
              )}
            >
              <div className="flex flex-wrap items-baseline justify-between gap-x-3">
                <span
                  className={cn(
                    "text-sm",
                    state === "pending"
                      ? "text-muted-foreground/70"
                      : "font-medium text-foreground",
                  )}
                >
                  {copy.label}
                  {entry && entry.runs > 1 && (
                    <span className="ml-2 font-mono text-[11px] text-signal-new">
                      pass {entry.runs}
                    </span>
                  )}
                </span>

                {stats && (
                  <span className="font-mono text-[11px] text-muted-foreground tabular">
                    {stats}
                  </span>
                )}
              </div>

              <p className="truncate font-mono text-[11px] text-muted-foreground/70">
                {node} <span className="not-italic">{copy.detail}</span>
              </p>
            </div>
          </li>
        );
      })}
    </ol>
  );
}

/** Builds the initial all-pending map. */
export function initialProgress(): Record<string, NodeProgress> {
  return Object.fromEntries(
    PIPELINE_ORDER.map((node) => [node, { state: "pending" as NodeState, runs: 0 }]),
  );
}
