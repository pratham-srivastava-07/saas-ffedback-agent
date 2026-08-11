"use client";

import { useMemo } from "react";
import {
  Background,
  BackgroundVariant,
  Controls,
  Handle,
  Position,
  ReactFlow,
  type Edge,
  type Node,
  type NodeProps,
} from "@xyflow/react";
import { Check, CircleDashed, Loader2, SkipForward } from "lucide-react";

import "@xyflow/react/dist/style.css";

import type { NodeProgress, NodeState } from "@/components/app/pipeline-monitor";
import { cn } from "@/lib/utils";

/**
 * The analysis pipeline, drawn as the graph it actually is.
 *
 * The backend is a LangGraph with a conditional branch and a bounded cycle —
 * facts a vertical checklist cannot express. `triage` can skip the entire
 * middle of the run, and `critique` can send `recommend` round a second time.
 * Those two edges are the whole reason this is a graph and not a list, so
 * they are drawn as edges and labelled.
 *
 * Layout is hand-placed rather than auto-laid-out. The topology is fixed and
 * known, and a solver would spend bundle weight rearranging something that
 * never changes — usually into something less legible.
 */

const STATE_ICON: Record<NodeState, React.ComponentType<{ className?: string }>> = {
  pending: CircleDashed,
  running: Loader2,
  done: Check,
  skipped: SkipForward,
};

interface StageData extends Record<string, unknown> {
  label: string;
  detail: string;
  progress?: NodeProgress;
  stat?: string | null;
  emphasis?: boolean;
}

function StageNode({ data }: NodeProps) {
  const { label, detail, progress, stat, emphasis } = data as StageData;
  const state: NodeState = progress?.state ?? "pending";
  const Icon = STATE_ICON[state];

  return (
    <div
      className={cn(
        "w-[188px] rounded-md border px-3 py-2.5 transition-colors",
        state === "running"
          ? "border-primary/50 bg-primary/8"
          : state === "done"
            ? "border-border bg-surface"
            : state === "skipped"
              ? "border-dashed border-border bg-surface/50"
              : "border-border bg-surface/60",
        emphasis && state === "pending" && "border-border/80",
      )}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!size-1.5 !border-0 !bg-border"
      />

      <div className="flex items-center gap-2">
        <Icon
          className={cn(
            "size-3.5 shrink-0",
            state === "running" && "animate-spin text-primary",
            state === "done" && "text-positive",
            state === "pending" && "text-muted-foreground/50",
            state === "skipped" && "text-muted-foreground/50",
          )}
          aria-hidden
        />
        <span
          className={cn(
            "min-w-0 flex-1 truncate text-[13px] font-medium",
            state === "pending" && "text-muted-foreground",
          )}
        >
          {label}
        </span>
        {progress && progress.runs > 1 && (
          <span className="type-meta rounded bg-secondary px-1 text-muted-foreground">
            ×{progress.runs}
          </span>
        )}
      </div>

      <p className="type-meta mt-1 truncate text-muted-foreground">
        {stat ?? detail}
      </p>

      <Handle
        type="source"
        position={Position.Bottom}
        className="!size-1.5 !border-0 !bg-border"
      />
    </div>
  );
}

const nodeTypes = { stage: StageNode };

/** Fixed topology, mirroring app/graph/build.py. */
const LAYOUT: Array<{
  id: string;
  label: string;
  detail: string;
  x: number;
  y: number;
}> = [
  { id: "normalize", label: "Clean", detail: "Trim and drop duplicates", x: 0, y: 0 },
  { id: "triage", label: "Triage", detail: "Reject noise", x: 0, y: 96 },
  { id: "analyze_one", label: "Read each item", detail: "One call per item", x: -110, y: 200 },
  { id: "embed", label: "Embed", detail: "One batched call", x: -110, y: 296 },
  { id: "cluster", label: "Cluster", detail: "Group by meaning", x: -110, y: 392 },
  { id: "resolve_taxonomy", label: "Match themes", detail: "Against themes on file", x: -110, y: 488 },
  { id: "name_themes", label: "Name new themes", detail: "Only new clusters", x: -110, y: 584 },
  { id: "prioritize", label: "Rank", detail: "Reach, severity, churn", x: -110, y: 680 },
  { id: "detect_trends", label: "Detect trends", detail: "Against prior runs", x: -110, y: 776 },
  { id: "recommend", label: "Recommend", detail: "Actions from evidence", x: -110, y: 872 },
  { id: "critique", label: "Audit", detail: "Check claims", x: -110, y: 968 },
  { id: "summarize", label: "Summarize", detail: "The brief", x: 0, y: 1080 },
];

export function PipelineGraph({
  progress,
  statFor,
  className,
}: {
  progress: Record<string, NodeProgress>;
  statFor?: (node: string) => string | null;
  className?: string;
}) {
  const nodes: Node[] = useMemo(
    () =>
      LAYOUT.map((stage) => ({
        id: stage.id,
        type: "stage",
        position: { x: stage.x, y: stage.y },
        data: {
          label: stage.label,
          detail: stage.detail,
          progress: progress[stage.id],
          stat: statFor?.(stage.id) ?? null,
        } satisfies StageData,
        draggable: false,
        selectable: false,
      })),
    [progress, statFor],
  );

  const edges: Edge[] = useMemo(() => {
    const active = (from: string) => progress[from]?.state === "done";
    const line = (id: string, source: string, target: string): Edge => ({
      id,
      source,
      target,
      animated: progress[target]?.state === "running",
      style: {
        stroke: active(source) ? "var(--color-primary)" : "var(--color-border)",
        strokeWidth: 1.5,
      },
    });

    return [
      line("e1", "normalize", "triage"),
      {
        ...line("e2", "triage", "analyze_one"),
        label: "actionable",
      },
      {
        // The branch that makes this a graph: a batch of pure noise skips
        // everything between triage and the summary.
        ...line("e-skip", "triage", "summarize"),
        label: "nothing actionable",
        style: {
          stroke: progress.summarize?.state === "done" && !progress.analyze_one?.completed
            ? "var(--color-primary)"
            : "var(--color-border)",
          strokeWidth: 1.5,
          strokeDasharray: "4 4",
        },
      },
      line("e3", "analyze_one", "embed"),
      line("e4", "embed", "cluster"),
      line("e5", "cluster", "resolve_taxonomy"),
      line("e6", "resolve_taxonomy", "name_themes"),
      line("e7", "name_themes", "prioritize"),
      line("e8", "prioritize", "detect_trends"),
      line("e9", "detect_trends", "recommend"),
      line("e10", "recommend", "critique"),
      {
        // The bounded cycle: an audit that fails sends the recommendations
        // back for one more pass, at most twice.
        ...line("e-loop", "critique", "recommend"),
        label: "unsupported",
        type: "smoothstep",
        style: {
          stroke:
            (progress.recommend?.runs ?? 0) > 1
              ? "var(--color-signal-new)"
              : "var(--color-border)",
          strokeWidth: 1.5,
          strokeDasharray: "4 4",
        },
      },
      line("e11", "critique", "summarize"),
    ];
  }, [progress]);

  return (
    <div className={cn("h-[30rem] w-full", className)}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.12 }}
        proOptions={{ hideAttribution: true }}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        minZoom={0.3}
        maxZoom={1.4}
        className="[&_.react-flow__edge-text]:!fill-[var(--color-muted-foreground)] [&_.react-flow__edge-text]:!text-[10px] [&_.react-flow__edge-textbg]:!fill-[var(--color-background)]"
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={18}
          size={1}
          color="var(--color-border)"
        />
        <Controls
          showInteractive={false}
          className="!rounded-md !border !border-border !bg-surface !shadow-none [&_button]:!border-border [&_button]:!bg-surface [&_button]:!text-foreground [&_button:hover]:!bg-surface-hover [&_button_svg]:!fill-current"
        />
      </ReactFlow>
    </div>
  );
}
