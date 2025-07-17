from schema import FeedbackState
from llm import llm
from langchain.prompts import ChatPromptTemplate

def generate_recommendations(state: FeedbackState) -> FeedbackState:
    prompt = ChatPromptTemplate.from_template("""
You're a SaaS product analyst. Based on the following feedback entries (with theme, intent, and urgency), suggest 3 product actions or improvements.

FEEDBACK:
{feedback}

Respond with a numbered list of clear, actionable product changes.
""")

    summarized_input = "\n".join([
        f"- {fb['theme']} ({fb['intent']}, {fb['urgency']})" for fb in state["processed_feedback"]
    ])
    
    chain = prompt | llm
    result = chain.invoke({"feedback": summarized_input})

    return {
        **state,
        "recommendations": result.content.strip().split("\n")
    }
