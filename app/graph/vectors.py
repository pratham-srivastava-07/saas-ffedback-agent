"""Vector helpers used by clustering and taxonomy matching."""

from __future__ import annotations

import numpy as np


def to_array(vectors: list[list[float]]) -> np.ndarray:
    return np.asarray(vectors, dtype=np.float32)


def l2_normalize(vector: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vector)
    if norm == 0:
        return vector
    return vector / norm


def centroid(vectors: list[list[float]]) -> list[float]:
    """Mean of a group of vectors, L2-normalised.

    Normalising means a centroid can be compared to another centroid with a
    plain dot product, and keeps stored theme centroids on the same scale
    regardless of how many items contributed to them.
    """
    if not vectors:
        return []
    mean = to_array(vectors).mean(axis=0)
    return l2_normalize(mean).tolist()


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    va = l2_normalize(np.asarray(a, dtype=np.float32))
    vb = l2_normalize(np.asarray(b, dtype=np.float32))
    return float(np.dot(va, vb))
