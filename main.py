from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# Import the compiled graph (this will work now)
from agent.graph import app as agent_app
from agent.quiz import generate_quiz_data  # Assuming you have quiz logic, or see below

app = FastAPI()

# Enable CORS for your Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request Models
class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = "default"


class QuizRequest(BaseModel):
    topic: str


@app.get("/")
def home():
    return {"status": "PathFinder AI is Running"}


@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    try:
        # Run the LangGraph Agent
        inputs = {"user_message": req.message, "messages": []}
        result = agent_app.invoke(inputs)

        # Extract structured data
        data = result.get("final_response", {})

        return {
            "reply": data.get("chat_message", ""),
            "plan": data.get("roadmap"),
            "mermaid": data.get("mermaid_code"),
            "status": "success"
        }
    except Exception as e:
        print(f"Error: {e}")
        return {"reply": "Something went wrong.", "status": "error"}


@app.post("/quiz")
def quiz_endpoint(req: QuizRequest):
    from langchain_openai import ChatOpenAI
    from agent.schemas import QuizData

    try:
        llm = ChatOpenAI(model="gpt-4o", temperature=0)
        structured_llm = llm.with_structured_output(QuizData)

        quiz = structured_llm.invoke(f"Create a hard 5-question quiz for: {req.topic}")
        return quiz.dict()
    except Exception as e:
        return {"error": str(e)}


# For Render execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)