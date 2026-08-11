/**
 * The categorical palette, and the rules that come with it.
 *
 * These six hues are not a taste decision. They were run through the
 * dataviz validator in both light and dark mode and pass every check:
 * lightness band, chroma floor, CVD separation, normal-vision floor, and
 * contrast against both surfaces.
 *
 * The palette they replace did not. Its worst adjacent pair — teal against
 * pink — sat at deuteranopia ΔE 3.7, meaning a red-green colourblind reader
 * saw two themes as the same colour, and five of its ten hues were outside
 * the dark-mode lightness band entirely.
 *
 * Two rules travel with this list:
 *
 *  1. **Order is fixed, never cycled.** Hues are assigned by position and a
 *     seventh series does not wrap around to slot one — it folds into
 *     "other". Cycling would give two different themes the same colour.
 *  2. **Every mark needs a direct label.** Tritan separation is 7.1, inside
 *     the 6–8 floor band, which is only legal alongside a second encoding.
 *     Colour alone is never the whole signal here.
 */

export const CATEGORICAL = [
  "#4a7fe3", // blue
  "#cc7a2b", // orange
  "#9265d6", // violet
  "#98831c", // ochre
  "#2b9fb3", // cyan
  "#d05a5a", // red
] as const;

/** Anything past the sixth series, and anything unclustered. */
export const OTHER_COLOR = "#8a8a86";

export const MAX_SERIES = CATEGORICAL.length;

/**
 * Colour for one entity, by its position in a stable ordering.
 *
 * The ordering must follow the entity, not its rank in the current view —
 * otherwise filtering a series out repaints everything that survives.
 */
export function colorAt(index: number): string {
  return index >= 0 && index < MAX_SERIES ? CATEGORICAL[index] : OTHER_COLOR;
}

export function colorForId(id: string | null, order: readonly string[]): string {
  if (!id) return OTHER_COLOR;
  return colorAt(order.indexOf(id));
}
