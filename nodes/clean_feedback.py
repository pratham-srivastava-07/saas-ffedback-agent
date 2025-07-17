from schema import FeedbackState


def clean_feedback(state: FeedbackState) -> FeedbackState:
    seen = set()
    cleaned_data = []

    for fb in state["raw_feedback"]:
        text = fb["text"].strip().replace("\n", " ")
        if text and text not in seen:
            seen.add(text)
            cleaned_data.append({**fb, "text": text})

    return {
        **state,
        "raw_feedback": cleaned_data,
    }
