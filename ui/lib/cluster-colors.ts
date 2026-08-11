/**
 * Cluster colours for the 3D explorer.
 *
 * Delegates to the validated categorical palette rather than keeping a second
 * list. The palette this file used to hold failed CVD validation — its worst
 * adjacent pair sat at deuteranopia ΔE 3.7, so a red-green colourblind reader
 * saw two clusters as one colour.
 *
 * Kept in its own module with no three.js imports: the explorer's legend needs
 * these colours, and importing them from the scene component would pull the
 * entire WebGL bundle into the page's eager chunk — including for devices that
 * fall back to the non-3D view.
 */

import { CATEGORICAL, MAX_SERIES, OTHER_COLOR, colorForId } from "@/lib/chart-colors";

export const CLUSTER_COLORS = CATEGORICAL;
export const UNCLUSTERED_COLOR = OTHER_COLOR;

/**
 * Colour for a theme, by its position in the run's theme ordering.
 *
 * Past the sixth theme everything is grey rather than wrapping back to blue.
 * Cycling would give two different themes the same colour in one plot, which
 * is worse than admitting the palette has run out — and the legend lists every
 * theme by name, so identity never rests on colour alone.
 */
export function colorForTheme(themeId: string | null, order: string[]): string {
  return colorForId(themeId, order);
}

export { MAX_SERIES };
