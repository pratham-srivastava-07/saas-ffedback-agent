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
    
    chain = prompt | llm  
    enriched = []

    for fb in state["processed_feedback"]:
        response = chain.invoke({"text": fb["text"]})
        content = getattr(response, "content", str(response)).strip()
        fb["theme"] = content
        enriched.append(fb)

    return {
        **state,
        "processed_feedback": enriched
    }
