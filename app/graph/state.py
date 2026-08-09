"""Graph state.

The reducers matter. ``analyzed`` and ``rejected`` are written by multiple
branches — ``analyzed`` by every parallel ``Send`` fan-out branch — so they
need ``operator.add`` to accumulate. Without a reducer, concurrent branches
overwrite one another and you silently keep only the last result.
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


class CleanItem(TypedDict):
    id: str
    text: str
    user_type: str
    source: str


class RejectedItem(TypedDict):
    id: str
    text: str
    reason: str


class AnalyzedItem(TypedDict, total=False):
    id: str
    text: str
    user_type: str
    source: str
    sentiment: str
    emotion: str
    intent: str
    severity: int
    feature_area: str
    churn_risk: bool
    theme_id: str | None
    status: str
    error: str | None


class Cluster(TypedDict):
    index: int
    item_ids: list[str]
    centroid: list[float]


class ResolvedTheme(TypedDict, total=False):
    id: str
    name: str
    description: str
    is_new: bool
    count: int
    share: float
    item_ids: list[str]
    centroid: list[float]
    impact_score: float
    avg_severity: float
    sentiment_breakdown: dict[str, int]
    churn_risk_count: int


class TrendSignal(TypedDict, total=False):
    theme_id: str
    theme_name: str
    direction: str
    current_share: float
    baseline_share: float | None
    change_ratio: float | None
    detail: str


class AnalysisState(TypedDict, total=False):
    run_id: str
    # Tenancy travels in the state, not on the Runtime: the Runtime is built
    # once at startup and shared by every request, so it cannot carry
    # per-request scope.
    workspace_id: str
    raw: list[dict[str, Any]]
    clean: list[CleanItem]
    rejected: Annotated[list[RejectedItem], operator.add]
    analyzed: Annotated[list[AnalyzedItem], operator.add]
    embeddings: dict[str, list[float]]
    clusters: list[Cluster]
    themes: list[ResolvedTheme]
    trends: list[TrendSignal]
    recommendations: list[dict[str, Any]]
    critique: dict[str, Any] | None
    revision_count: int
    summary: str
