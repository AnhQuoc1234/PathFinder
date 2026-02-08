from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from agent.graph import app as agent_app

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = "default"

class QuizRequest(BaseModel):
    topic: str

@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    try:
        inputs = {"user_message": req.message, "messages": []}
        result = agent_app.invoke(inputs)
        data = result.get("final_response", {})
        return {
            "reply": data.get("chat_message", ""),
            "plan": data.get("roadmap"),
            "status": "success"
        }
    except Exception as e:
        print(f"Error: {e}")
        return {"reply": "System Error.", "status": "error"}

@app.post("/quiz")
def quiz_endpoint(req: QuizRequest):
    from langchain_openai import ChatOpenAI
    from agent.schemas import QuizData
    try:
        llm = ChatOpenAI(model="gpt-4o", temperature=0)
        structured_llm = llm.with_structured_output(QuizData)
        quiz = structured_llm.invoke(f"Create a 5-question quiz for: {req.topic}")
        return quiz.dict()
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)