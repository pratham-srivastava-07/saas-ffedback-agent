import { cn } from "@/lib/utils";

/**
 * Share-of-run over consecutive runs.
 *
 * No filled background track: the shape of the line is the whole message, and
 * a track would add ink without adding information. A single point renders as
 * a dot, because one reading is not a trend and should not look like one.
 */
export function Sparkline({
  values,
  className,
  width = 96,
  height = 28,
}: {
  values: number[];
  className?: string;
  width?: number;
  height?: number;
}) {
  if (values.length === 0) {
    return <span className={cn("text-xs text-muted-foreground", className)}>No history</span>;
  }

  const pad = 3;
  const max = Math.max(...values, 0.0001);
  const min = Math.min(...values, 0);
  const span = max - min || max || 1;

  const pointAt = (value: number, index: number) => {
    const x =
      values.length === 1
        ? width / 2
        : pad + (index / (values.length - 1)) * (width - pad * 2);
    const y = height - pad - ((value - min) / span) * (height - pad * 2);
    return [x, y] as const;
  };

  const points = values.map(pointAt);
  const [lastX, lastY] = points[points.length - 1];

  return (
    <svg
      className={cn("overflow-visible", className)}
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label={`Share across ${values.length} run${values.length === 1 ? "" : "s"}, most recent ${(values[values.length - 1] * 100).toFixed(1)} percent`}
    >
      {points.length > 1 && (
        <polyline
          points={points.map(([x, y]) => `${x},${y}`).join(" ")}
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="text-muted-foreground"
        />
      )}
      <circle cx={lastX} cy={lastY} r="2.5" className="fill-primary" />
    </svg>
  );
}
