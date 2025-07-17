from langchain.prompts import ChatPromptTemplate
from llm import llm
from schema import FeedbackState
import json

def classify_sentiment_and_intent(state: FeedbackState) -> FeedbackState:
    prompt = ChatPromptTemplate.from_template("""
You are an intelligent feedback classifier.

Classify the following SaaS feedback entry strictly in valid JSON format.

Entry: {text}

Respond with ONLY this JSON structure:
{{
  "sentiment": "positive" | "neutral" | "negative",
  "intent": "complaint" | "praise" | "feature-request" | "bug-report" | "other"
}}
""")

    chain = prompt | llm
    processed = []

    for fb in state["raw_feedback"]:
        try:
            result = chain.invoke({"text": fb["text"]})

            # Handle possible format variations
            content = getattr(result, "content", None) or getattr(result, "text", None) or str(result)
            print("Raw response:", content)

            if not content:
                raise ValueError("Empty or missing LLM response")

            parsed = json.loads(content)

            sentiment = parsed.get("sentiment", "unknown")
            intent = parsed.get("intent", "other")

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"[ERROR] Failed to classify feedback: {fb['text']}")
            print(f"[ERROR] Reason: {e}")
            sentiment = "unknown"
            intent = "other"

        processed.append({
            **fb,
            "sentiment": sentiment,
            "intent": intent,
        })

    return {
        **state,
        "processed_feedback": processed
    }
