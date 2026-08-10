"use client";

import Link from "next/link";
import { useCallback, useMemo, useRef, useState } from "react";
import { Loader2, Play, Square } from "lucide-react";

import { PageHeader } from "@/components/app/shell";
import {
  PipelineMonitor,
  initialProgress,
  type NodeProgress,
} from "@/components/app/pipeline-monitor";
import {
  Recommendations,
  RunStats,
  SummaryPanel,
  ThemeTable,
} from "@/components/app/results";
import { EmptyState, ErrorState } from "@/components/app/states";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  MAX_CHARS,
  MAX_ITEMS,
  SOURCES,
  USER_TYPES,
  streamAnalyze,
  type AnalyzeResponse,
  type FeedbackInput,
  type Source,
  type UserType,
} from "@/lib/api";
import { SAMPLE_FEEDBACK } from "@/lib/sample-feedback";
import { cn } from "@/lib/utils";
import { Layers } from "lucide-react";

export default function AnalyzePage() {
  const [text, setText] = useState("");
  const [userType, setUserType] = useState<UserType>("paid");
  const [source, setSource] = useState<Source>("support");

  const [progress, setProgress] = useState<Record<string, NodeProgress>>(
    initialProgress,
  );
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const pipelineRef = useRef<HTMLDivElement | null>(null);

  const lines = useMemo(
    () => text.split("\n").map((line) => line.trim()).filter(Boolean),
    [text],
  );

  const tooMany = lines.length > MAX_ITEMS;
  const tooLong = lines.find((line) => line.length > MAX_CHARS);

  // Bounds mirrored from the backend so they are learned here, not through a 422.
  const validation = tooMany
    ? `That is ${lines.length} items. The limit is ${MAX_ITEMS} per run.`
    : tooLong
      ? `One line is over ${MAX_CHARS} characters. Split it up.`
      : null;

  const canRun = lines.length > 0 && !validation && !running;

  const handleEvent = useCallback((event: Parameters<Parameters<typeof streamAnalyze>[1]>[0]) => {
    if (event.event === "node_start") {
      setProgress((current) => {
        const existing = current[event.data.node];
        if (!existing) return current;
        return {
          ...current,
          [event.data.node]: {
            ...existing,
            state: "running",
            // A second pass happens when critique sends recommend round again.
            runs: existing.runs + 1,
            completed: undefined,
          },
        };
      });
    } else if (event.event === "node_end") {
      setProgress((current) => {
        const existing = current[event.data.node];
        if (!existing) return current;
        return {
          ...current,
          [event.data.node]: {
            ...existing,
            state: "done",
            stats: "stats" in event.data ? event.data.stats : existing.stats,
            completed:
              "completed" in event.data ? event.data.completed : existing.completed,
          },
        };
      });
    } else if (event.event === "complete") {
      setResult(event.data);
      // Anything still pending was genuinely skipped, which happens when
      // triage short-circuits a batch of pure noise straight to the summary.
      setProgress((current) =>
        Object.fromEntries(
          Object.entries(current).map(([node, entry]) => [
            node,
            entry.state === "pending" ? { ...entry, state: "skipped" as const } : entry,
          ]),
        ),
      );
    } else if (event.event === "error") {
      setError(event.data.message);
    }
  }, []);

  async function run() {
    setError(null);
    setResult(null);
    setProgress(initialProgress());
    setRunning(true);

    // Bring the pipeline into view. A long feedback box can push it entirely
    // below the fold, so hitting Run would otherwise look like nothing
    // happened. requestAnimationFrame waits for the node to exist, since it
    // only mounts once `running` is true.
    requestAnimationFrame(() => {
      pipelineRef.current?.scrollIntoView({
        behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
          ? "auto"
          : "smooth",
        block: "start",
      });
    });

    const controller = new AbortController();
    abortRef.current = controller;

    const payload: FeedbackInput[] = lines.map((line, index) => ({
      id: `item-${index + 1}`,
      text: line,
      user_type: userType,
      source,
    }));

    try {
      await streamAnalyze(payload, handleEvent, controller.signal);
    } catch (caught) {
      if ((caught as Error).name !== "AbortError") {
        setError((caught as Error).message);
      }
    } finally {
      setRunning(false);
      abortRef.current = null;
    }
  }

  function stop() {
    abortRef.current?.abort();
    setRunning(false);
  }

  return (
    <>
      <PageHeader
        title="Analyze"
        description="One item per line. Watch each stage report as it finishes."
      />

      {/*
        One column, stacked in the order the work happens: write feedback,
        watch the pipeline, read the result. The previous two-column split put
        the form and the pipeline in one scroll context and the results in
        another, so following a run meant tracking two places at once.
      */}
      <div className="space-y-6 px-5 py-6 sm:px-8">
        <div className="space-y-6">
          <div className="rounded-lg border bg-surface p-5">
            <div className="flex items-center justify-between gap-3">
              <Label htmlFor="feedback">Feedback</Label>
              <button
                type="button"
                onClick={() => setText(SAMPLE_FEEDBACK)}
                disabled={running}
                className="text-xs text-primary underline-offset-4 hover:underline disabled:opacity-50"
              >
                Load sample
              </button>
            </div>

            {/*
              Text left, controls right. Feedback lines are short, so a
              full-bleed textarea left most of the row empty; the settings that
              apply to the batch now fill it instead of stacking underneath and
              pushing everything down.
            */}
            <div className="mt-3 grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
              <div className="min-w-0">
                <Textarea
                  id="feedback"
                  value={text}
                  onChange={(event) => setText(event.target.value)}
                  disabled={running}
                  rows={14}
                  // field-sizing-fixed overrides the shared Textarea's
                  // field-sizing-content, which sizes the box to its content
                  // and silently ignores `rows` — leaving an empty box two
                  // lines tall. This one should open at a usable size and stay
                  // there, so a batch can be pasted without it jumping about.
                  className="resize-y font-mono text-[13px] field-sizing-fixed"
                  placeholder={
                    "Signup is broken after the update\nBilling charged me twice"
                  }
                  aria-invalid={Boolean(validation)}
                />

              </div>

              <div className="flex flex-col gap-4">
                {/*
                  Three mutually exclusive values, so a segmented control
                  rather than a select: every option is visible and reachable
                  in one click instead of two, and there is no popover to
                  open just to learn what the choices are.
                */}
                <fieldset disabled={running} className="grid gap-2">
                  <legend className="mb-2 text-sm font-medium">
                    Customer tier
                  </legend>
                  <div
                    role="radiogroup"
                    aria-label="Customer tier"
                    className="grid grid-cols-3 gap-1 rounded-md border border-input p-1"
                  >
                    {USER_TYPES.map((type) => (
                      <button
                        key={type}
                        type="button"
                        role="radio"
                        aria-checked={userType === type}
                        onClick={() => setUserType(type)}
                        className={cn(
                          "rounded px-2 py-1.5 text-xs capitalize transition-colors",
                          "focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-ring",
                          "disabled:cursor-not-allowed disabled:opacity-50",
                          userType === type
                            ? "bg-secondary font-medium text-foreground"
                            : "text-muted-foreground hover:text-foreground",
                        )}
                      >
                        {type}
                      </button>
                    ))}
                  </div>
                </fieldset>

                <div className="grid gap-2">
                  <Label htmlFor="source">Source</Label>
                  <Select
                    value={source}
                    onValueChange={(value) => setSource(value as Source)}
                    disabled={running}
                  >
                    {/* Seven options with no natural order — a select is the
                        right widget here, just a full-width one. */}
                    <SelectTrigger id="source" className="w-full">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {SOURCES.map((item) => (
                        <SelectItem key={item} value={item} className="capitalize">
                          {item.replace(/_/g, " ")}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <p className="text-xs leading-relaxed text-muted-foreground">
                  Applied to every line in this batch. Upload a CSV to set them
                  per row.{" "}
                  <Link
                    href="/app/ingest"
                    className="text-primary underline-offset-4 hover:underline"
                  >
                    Upload a file
                  </Link>
                </p>

                {/*
                  The count lives here rather than under the textarea: it is
                  what you check immediately before clicking Run, so it belongs
                  beside the button. It also fills what was otherwise dead space
                  between the settings and the action.
                */}
                <div className="mt-auto rounded-md border border-border bg-muted/30 px-4 py-3">
                  <div className="flex items-baseline gap-2">
                    <span className="font-mono text-2xl leading-none tabular">
                      {lines.length}
                    </span>
                    <span className="text-sm text-muted-foreground">
                      {lines.length === 1 ? "item" : "items"} ready
                    </span>
                  </div>
                  <p className="mt-1 font-mono text-[11px] text-muted-foreground tabular">
                    {MAX_ITEMS} max per batch
                  </p>
                  {validation && (
                    <p className="mt-2 text-xs text-destructive" role="alert">
                      {validation}
                    </p>
                  )}
                </div>

                <div className="flex gap-2">
                  <Button
                    onClick={run}
                    disabled={!canRun}
                    className="flex-1"
                    size="lg"
                  >
                    {running ? (
                      <Loader2 className="size-4 animate-spin" aria-hidden />
                    ) : (
                      <Play className="size-4" aria-hidden />
                    )}
                    {running ? "Running" : "Run analysis"}
                  </Button>
                  {running && (
                    <Button variant="outline" size="lg" onClick={stop}>
                      <Square className="size-4" aria-hidden />
                      Stop
                    </Button>
                  )}
                </div>
              </div>
            </div>
          </div>

          {(running || result) && (
            <div
              ref={pipelineRef}
              className="scroll-mt-4 rounded-lg border bg-surface p-5"
            >
              <h2 className="mb-4 font-display text-sm font-semibold tracking-tight">
                Pipeline
              </h2>
              <PipelineMonitor progress={progress} />
            </div>
          )}
        </div>

        <div className="space-y-6">
          {error && <ErrorState message={error} onRetry={canRun ? run : undefined} />}

          {!result && !error && (
            <EmptyState
              icon={Layers}
              title="No run yet"
              body="Paste feedback and run the analysis. Themes, trends and recommended actions land here."
            />
          )}

          {result && (
            <>
              <RunStats
                analyzed={result.analyzed.length}
                rejected={result.rejected.length}
                themes={result.themes.length}
                revisions={result.revision_count}
              />

              <SummaryPanel summary={result.summary} />

              {result.themes.length > 0 && (
                <section>
                  <h2 className="mb-3 font-display text-sm font-semibold tracking-tight">
                    Themes by impact
                  </h2>
                  <ThemeTable themes={result.themes} trends={result.trends} />
                </section>
              )}

              {result.recommendations.length > 0 && (
                <section>
                  <h2 className="mb-3 font-display text-sm font-semibold tracking-tight">
                    Recommended actions
                  </h2>
                  <Recommendations
                    recommendations={result.recommendations}
                    themes={result.themes}
                  />
                </section>
              )}

              {result.rejected.length > 0 && (
                <section>
                  <h2 className="mb-3 font-display text-sm font-semibold tracking-tight">
                    Rejected as noise
                  </h2>
                  <ul className="overflow-hidden rounded-lg border">
                    {result.rejected.map((item, index) => (
                      <li
                        key={`${item.id}-${index}`}
                        className={`flex items-baseline justify-between gap-4 bg-surface px-4 py-2.5 ${index > 0 ? "border-t border-border" : ""}`}
                      >
                        <span className="truncate text-sm text-muted-foreground">
                          {item.text || "(empty)"}
                        </span>
                        <span className="shrink-0 font-mono text-[11px] text-muted-foreground">
                          {item.reason.replace(/_/g, " ")}
                        </span>
                      </li>
                    ))}
                  </ul>
                </section>
              )}

              <p className="text-xs text-muted-foreground">
                Run{" "}
                <Link
                  href={`/app/runs/${encodeURIComponent(result.run_id)}`}
                  className="font-mono text-primary underline-offset-4 hover:underline"
                >
                  {result.run_id.slice(0, 8)}
                </Link>{" "}
                saved to this workspace.
              </p>
            </>
          )}
        </div>
      </div>
    </>
  );
}
