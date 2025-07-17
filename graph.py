from langgraph.graph import StateGraph, END
from schema import FeedbackState
from nodes import *

def build_graph():
    workflow = StateGraph(FeedbackState)
    workflow.add_node("clean_feedback", clean_feedback)
    workflow.add_node("classify", classify_sentiment_and_intent)
    workflow.add_node("score", score_urgency)
    workflow.add_node("cluster", cluster_themes)
    workflow.add_node("recommend", generate_recommendations)

    workflow.set_entry_point("clean_feedback")
    workflow.add_edge("clean_feedback", "classify")
    workflow.add_edge("classify", "score")
    workflow.add_edge("score", "cluster")
    workflow.add_edge("cluster", "recommend")
    workflow.add_edge("recommend", END)

    return workflow.compile()
