def calculate_urgency(text: str, sentiment: str, intent: str, user_type: str) -> str:
    # Example rules
    if intent == "bug-report" and sentiment == "negative":
        return "high"
    elif intent == "feature-request":
        return "medium"
    elif user_type == "enterprise" and sentiment == "negative":
        return "high"
    else:
        return "low"
