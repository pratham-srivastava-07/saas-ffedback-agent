/**
 * Cluster palette.
 *
 * Deliberately kept in its own module with no three.js imports. The explorer's
 * legend needs these colours, and importing them from the scene component
 * would pull the entire WebGL bundle into the page's eager chunk — including
 * for devices that fall back to the non-3D view.
 */

/** Distinct hues that stay legible on both light and dark backdrops. */
export const CLUSTER_COLORS = [
  "#6366f1",
  "#ec4899",
  "#14b8a6",
  "#f59e0b",
  "#8b5cf6",
  "#06b6d4",
  "#ef4444",
  "#84cc16",
  "#f97316",
  "#3b82f6",
];

export const UNCLUSTERED_COLOR = "#94a3b8";

export function colorForTheme(themeId: string | null, order: string[]): string {
  if (!themeId) return UNCLUSTERED_COLOR;
  const index = order.indexOf(themeId);
  return index === -1
    ? UNCLUSTERED_COLOR
    : CLUSTER_COLORS[index % CLUSTER_COLORS.length];
}
