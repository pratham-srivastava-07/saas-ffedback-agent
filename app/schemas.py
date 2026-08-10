"""Pydantic models: the public API contract and LLM structured-output shapes.

Structured-output models are what we hand to ``.with_structured_output()``. They
replace the previous approach of calling ``json.loads`` on raw model text, which
silently degraded every response wrapped in a markdown fence.
"""

from typing import Literal

from pydantic import BaseModel, Field

Sentiment = Literal["positive", "neutral", "negative"]
Intent = Literal[
    "complaint", "praise", "feature-request", "bug-report", "question", "other"
]
Emotion = Literal[
    "angry", "frustrated", "confused", "neutral", "satisfied", "delighted"
]
# "enterprise" was previously branched on in utils.py but absent from the
# schema, making that branch unreachable. It is a real tier; it belongs here.
UserType = Literal["free", "paid", "enterprise"]
Source = Literal[
    "support", "nps", "review", "app_store", "slack", "sales_call", "other"
]
TrendDirection = Literal[
    "emerging", "spiking", "steady", "declining", "insufficient_history"
]


# --------------------------------------------------------------------------
# API request / response
# --------------------------------------------------------------------------


class FeedbackItemIn(BaseModel):
    id: str | None = None
    text: str = Field(min_length=1, max_length=5000)
    user_type: UserType = "free"
    source: Source = "other"


class AnalyzeRequest(BaseModel):
    raw_feedback: list[FeedbackItemIn] = Field(min_length=1, max_length=200)


class AppStoreRequest(BaseModel):
    """Pull an app's public reviews. No credentials needed from the user."""

    app_id: str = Field(min_length=1, max_length=32)
    country: str = Field(default="us", min_length=2, max_length=2)
    # Apple returns ~50 reviews per page. Capped so one request cannot fan out
    # into an unbounded number of upstream fetches.
    pages: int = Field(default=1, ge=1, le=5)


class AnalyzedItemOut(BaseModel):
    id: str
    text: str
    user_type: UserType
    source: Source
    sentiment: Sentiment
    emotion: Emotion
    intent: Intent
    severity: int
    feature_area: str
    churn_risk: bool
    theme_id: str | None = None
    status: Literal["ok", "failed"] = "ok"
    error: str | None = None


class RejectedItemOut(BaseModel):
    id: str
    text: str
    reason: str


class ThemeOut(BaseModel):
    id: str
    name: str
    description: str
    count: int
    is_new: bool
    impact_score: float
    avg_severity: float
    sentiment_breakdown: dict[str, int]
    churn_risk_count: int
    sample_item_ids: list[str]


class TrendOut(BaseModel):
    theme_id: str
    theme_name: str
    direction: TrendDirection
    current_share: float
    baseline_share: float | None = None
    change_ratio: float | None = None
    detail: str


class RecommendationOut(BaseModel):
    title: str
    rationale: str
    theme_ids: list[str]
    effort: Literal["low", "medium", "high"]


class AnalyzeResponse(BaseModel):
    run_id: str
    summary: str
    analyzed: list[AnalyzedItemOut]
    rejected: list[RejectedItemOut]
    themes: list[ThemeOut]
    trends: list[TrendOut]
    recommendations: list[RecommendationOut]
    revision_count: int


class RunOut(BaseModel):
    id: str
    created_at: str
    status: str
    item_count: int
    rejected_count: int
    theme_count: int
    summary: str | None = None


# --------------------------------------------------------------------------
# LLM structured output
# --------------------------------------------------------------------------


class ItemAnalysis(BaseModel):
    """Everything we need from one feedback item, in a single call.

    Previously sentiment/intent and theme were two separate per-item calls.
    Merging them halves cost and latency, and the theme signal benefits from
    being produced by a model that just reasoned about intent.
    """

    sentiment: Sentiment
    emotion: Emotion
    intent: Intent
    severity: int = Field(
        ge=1, le=5, description="1 = cosmetic nitpick, 5 = blocking or data loss"
    )
    feature_area: str = Field(
        description="Short product area, e.g. 'signup', 'billing', 'search'"
    )
    churn_risk: bool = Field(
        description="True only if the user signals they may stop paying or leave"
    )


class ThemeNaming(BaseModel):
    name: str = Field(description="Under 6 words, specific and product-oriented")
    description: str = Field(description="One sentence on what users are reporting")


class LLMRecommendation(BaseModel):
    title: str
    rationale: str = Field(description="Must cite the evidence it rests on")
    theme_ids: list[str] = Field(description="Theme ids this addresses")
    effort: Literal["low", "medium", "high"]


class RecommendationSet(BaseModel):
    recommendations: list[LLMRecommendation]


class CritiqueVerdict(BaseModel):
    """Whether the recommendations are actually supported by the themes."""

    approved: bool
    issues: list[str] = Field(
        default_factory=list, description="Specific unsupported claims found"
    )
    guidance: str = Field(
        default="", description="How to fix them, if not approved"
    )
