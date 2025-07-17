from typing import TypedDict, Literal

class RawFeedback(TypedDict):
    id: str
    text: str
    user_type: Literal["free", "paid"]
    source: Literal["support", "nps", "review"]

class ProcessedFeedback(TypedDict):
    id: str
    text: str
    sentiment: Literal["positive", "neutral", "negative"]
    intent: Literal["complaint", "praise", "feature-request", "bug-report", "other"]
    theme: str
    urgency: Literal["low", "medium", "high"]

class FeedbackState(TypedDict):
    raw_feedback: list[RawFeedback]
    processed_feedback: list[ProcessedFeedback]
    recommendations: list[str]