import Link from "next/link";
import { CircleAlert, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

/** An empty screen is an invitation to act, so it always carries the next step. */
export function EmptyState({
  icon: Icon,
  title,
  body,
  actionLabel,
  actionHref,
  onAction,
  className,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  body: string;
  actionLabel?: string;
  actionHref?: string;
  onAction?: () => void;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-lg border border-dashed border-border px-6 py-16 text-center",
        className,
      )}
    >
      <Icon className="size-6 text-muted-foreground" aria-hidden />
      <h3 className="mt-4 font-display text-base font-semibold">{title}</h3>
      <p className="mt-1.5 max-w-sm text-sm text-muted-foreground">{body}</p>
      {actionLabel && actionHref && (
        <Button asChild size="sm" className="mt-5">
          <Link href={actionHref}>{actionLabel}</Link>
        </Button>
      )}
      {actionLabel && onAction && !actionHref && (
        <Button size="sm" className="mt-5" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </div>
  );
}

/** Errors state what happened and how to recover. They do not apologise. */
export function ErrorState({
  message,
  onRetry,
  className,
}: {
  message: string;
  onRetry?: () => void;
  className?: string;
}) {
  return (
    <div
      role="alert"
      className={cn(
        "flex items-start gap-3 rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-3",
        className,
      )}
    >
      <CircleAlert className="mt-0.5 size-4 shrink-0 text-destructive" aria-hidden />
      <div className="min-w-0 flex-1">
        <p className="text-sm text-foreground">{message}</p>
        {onRetry && (
          <Button
            variant="outline"
            size="sm"
            className="mt-3"
            onClick={onRetry}
          >
            <RefreshCw className="size-3.5" aria-hidden />
            Try again
          </Button>
        )}
      </div>
    </div>
  );
}

/** Skeletons match the shape of what is loading, so nothing shifts on arrival. */
export function SkeletonRows({
  rows = 5,
  className,
}: {
  rows?: number;
  className?: string;
}) {
  return (
    <div className={cn("space-y-px overflow-hidden rounded-lg border", className)}>
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} className="flex items-center gap-4 bg-surface px-4 py-4">
          <div className="h-3 w-8 animate-pulse rounded bg-muted" />
          <div className="flex-1 space-y-2">
            <div
              className="h-3 animate-pulse rounded bg-muted"
              style={{ width: `${55 + ((index * 13) % 30)}%` }}
            />
            <div className="h-2.5 w-1/3 animate-pulse rounded bg-muted/70" />
          </div>
          <div className="h-5 w-20 animate-pulse rounded bg-muted" />
        </div>
      ))}
    </div>
  );
}

export function SkeletonCard({ className }: { className?: string }) {
  return (
    <div className={cn("rounded-lg border bg-surface p-5", className)}>
      <div className="h-3 w-24 animate-pulse rounded bg-muted" />
      <div className="mt-4 h-7 w-32 animate-pulse rounded bg-muted" />
      <div className="mt-3 h-2.5 w-full animate-pulse rounded bg-muted/70" />
    </div>
  );
}
