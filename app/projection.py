"""Project a run's embeddings into 3D for the cluster explorer.

Embeddings exist only inside graph state during a run. Storing the projection
gives the frontend a point cloud of the real embedding space without keeping a
768-dimension vector per row in SQLite, which is not a vector store.

**PCA is fit per run.** Each run gets its own basis, so coordinates from two
different runs are not comparable and must never share axes. That is why the
endpoint is per-run.
"""

from __future__ import annotations

import logging

import numpy as np

logger = logging.getLogger(__name__)

Point = tuple[float, float, float]
_ORIGIN: Point = (0.0, 0.0, 0.0)
_DIMENSIONS = 3


def project_to_3d(embeddings: dict[str, list[float]]) -> dict[str, Point]:
    """Reduce each embedding to normalised (x, y, z).

    Coordinates are scaled into roughly [-1, 1] using a single global factor
    rather than per-axis, which would stretch the cloud and misrepresent the
    relative distances the plot exists to show.

    Never raises: a scatter plot is a nice-to-have and must not be able to
    fail a run.
    """
    usable = {
        item_id: vector for item_id, vector in embeddings.items() if vector
    }
    if not usable:
        return {}

    item_ids = list(usable)

    # PCA needs at least two points to find a direction of variance, and one
    # point has no meaningful position relative to anything.
    if len(item_ids) < 2:
        return {item_ids[0]: _ORIGIN}

    try:
        matrix = np.asarray([usable[item_id] for item_id in item_ids], dtype=np.float64)
        components = min(_DIMENSIONS, matrix.shape[0], matrix.shape[1])

        if components < 1:
            return {item_id: _ORIGIN for item_id in item_ids}

        # Identical vectors have no variance for PCA to decompose; sklearn
        # divides by a zero total and yields NaN. Short-circuit instead: the
        # honest picture of "every item is the same" is a single dot.
        if not np.any(matrix.var(axis=0) > 0):
            return {item_id: _ORIGIN for item_id in item_ids}

        from sklearn.decomposition import PCA

        projected = PCA(n_components=components).fit_transform(matrix)

        if not np.all(np.isfinite(projected)):
            logger.warning("PCA produced non-finite coordinates; using origin")
            return {item_id: _ORIGIN for item_id in item_ids}

        # Fewer than three components available (few items, or a low-rank
        # space such as identical vectors). Pad the missing axes with zeros
        # so the frontend always receives three coordinates.
        if components < _DIMENSIONS:
            padding = np.zeros((projected.shape[0], _DIMENSIONS - components))
            projected = np.hstack([projected, padding])

        scale = float(np.max(np.abs(projected)))
        if scale > 0:
            projected = projected / scale
        # scale == 0 means every point is identical, which collapses the whole
        # cloud onto the origin. That is the honest picture, not an error.

        return {
            item_id: (
                round(float(coords[0]), 6),
                round(float(coords[1]), 6),
                round(float(coords[2]), 6),
            )
            for item_id, coords in zip(item_ids, projected)
        }

    except Exception as exc:  # noqa: BLE001 - never fail a run over a plot
        logger.warning("3D projection failed, falling back to origin: %s", exc)
        return {item_id: _ORIGIN for item_id in item_ids}
