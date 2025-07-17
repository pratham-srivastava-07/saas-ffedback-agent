from langchain.prompts import ChatPromptTemplate
from llm import llm
from schema import FeedbackState

def cluster_themes(state: FeedbackState) -> FeedbackState:
    prompt = ChatPromptTemplate.from_template("""
Assign a concise theme to the following SaaS user feedback:
"{text}"

Examples: "Pricing Confusion", "Bug in Signup Flow", "Performance Lag", "Feature Request: Dark Mode"
Only output the theme name.
""")
    
    chain = llm | prompt
    enriched = []

    for fb in state["processed_feedback"]:
        response = chain.invoke({"text": fb["text"]})
        fb["theme"] = response.content.strip()
        enriched.append(fb)

    return {
        **state,
        "processed_feedback": enriched
    }
