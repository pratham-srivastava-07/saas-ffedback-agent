from langchain.prompts import ChatPromptTemplate
from llm import llm
from schema import FeedbackState
import json

def classify_sentiment_and_intent(state: FeedbackState) -> FeedbackState:
    prompt = ChatPromptTemplate.from_template("""
        Classify the following SaaS feedback entry.

        Entry: {text}

        Respond in JSON with fields:
        - sentiment: "positive", "neutral", or "negative"
        - intent: "complaint", "praise", "feature-request", "bug-report", or "other"
        """)
    
    processed = []
    chain = prompt | llm

    for fb in state["raw_feedback"]:
        result = chain.invoke({"text": fb["text"]})
        parsed = json.loads(result.content)
        processed.append({
            **fb,
            "sentiment": parsed["sentiment"],
            "intent": parsed["intent"],
        })

    return {
        **state,
        "processed_feedback": processed
    }
