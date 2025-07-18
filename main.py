from graph import build_graph
from schema import FeedbackState
from pprint import pprint
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()
graph_app = build_graph()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FeedbackItem(BaseModel):
    id: str
    text: str
    user_type: str
    source: str

class FeedbackInput(BaseModel):
    raw_feedback: List[FeedbackItem]

@app.post("/analyze")
def analyze_feedback(payload: FeedbackInput):
    input_data: FeedbackState = {
        "raw_feedback": [item.dict() for item in payload.raw_feedback],
        "processed_feedback": [],
        "recommendations": []
    }

    result = graph_app.invoke(input_data)

    print("\n📊 Final Processed Output:\n")
    pprint(result)

    return result


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)