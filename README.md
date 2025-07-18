# 📊 Sentilytics.ai

**Sentilytics** is an AI-powered feedback analyzer for SaaS teams. It helps product and support teams extract sentiment, intent, and actionable insights from customer feedback across various sources like support tickets, reviews, and surveys.

---

## 🚀 Features

- ✨ Built with LangGraph + Gemini Pro
- 🧠 Understand user sentiment and categorize feedback
- 💡 Get product recommendations based on user pain points
- 🔄 Seamless API integration for real-time analysis
- ⚡ Frontend dashboard built with Next.js
- 🧩 Modular architecture with FastAPI backend

---

## 🛠️ Tech Stack

- Backend: **Python**, **FastAPI**, **LangGraph**
- LLM: **Gemini Pro (via Google Generative AI)**
- Frontend: **Next.js 15**, **TailwindCSS**
- Hosting: **Render**, **Vercel**

---

## 📦 Project Structure

├── main.py # FastAPI entrypoint
├── graph.py # LangGraph pipeline
├── llm.py # Gemini/Groq config
├── schema.py # Data schema (Pydantic)
├── nodes/ # LangGraph nodes
├── ui/ # Next.js frontend
├── requirements.txt
└── README.md



---

## ⚙️ Getting Started (Local)

```bash
# 1. Clone the repo
git clone https://github.com/pratham-srivastava-07/saas-ffedback-agent.git
cd saas-ffedback-agent

# 2. Create a virtual environment and activate it
python -m venv venv
source venv/bin/activate   # or venv\Scripts\activate on Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the FastAPI backend
uvicorn main:app --reload


```

**Sentilytics** was built to help you move fast with clarity — making your product better with every piece of feedback.
