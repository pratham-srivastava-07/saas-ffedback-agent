from schema import FeedbackState
from utils import calculate_urgency

def score_urgency(state: FeedbackState) -> FeedbackState:
    scored = []

    for fb in state["processed_feedback"]:
        urgency = calculate_urgency(
            fb["text"], fb["sentiment"], fb["intent"], fb["user_type"]
        )
        fb["urgency"] = urgency
        scored.append(fb)

    return {
        **state,
        "processed_feedback": scored
    }
