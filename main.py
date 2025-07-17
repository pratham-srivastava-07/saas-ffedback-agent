from graph import build_graph
from schema import FeedbackState
from pprint import pprint

app = build_graph()

if __name__ == "__main__":
    input_data: FeedbackState = {
        "raw_feedback": [
            {
                "id": "1",
                "text": "The dashboard is super slow, I might cancel.",
                "user_type": "paid",
                "source": "support"
            },
            {
                "id": "2",
                "text": "Can we get dark mode?",
                "user_type": "free",
                "source": "review"
            },
            {
                "id": "3",
                "text": "Love the new update",
                "user_type": "paid",
                "source": "nps"
            }
        ],
        "processed_feedback": [],
        "recommendations": []
    }

    result = app.invoke(input_data)

    print("\n📊 Final Processed Output:\n")
    pprint(result)
