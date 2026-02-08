from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
from langchain_core.messages import HumanMessage, AIMessage

from agent.graph import app as agent_app
from database import init_db, register_user, login_user, save_message, get_history, get_user_threads

init_db()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for Guests
guest_store: Dict[str, List] = {}

class AuthRequest(BaseModel):
    username: str
    password: str

class ChatRequest(BaseModel):
    message: str
    thread_id: str
    username: Optional[str] = None

class HistoryRequest(BaseModel):
    username: str
    thread_id: str

class QuizRequest(BaseModel):
    topic: str

@app.post("/register")
def register(req: AuthRequest):
    if register_user(req.username, req.password):
        return {"status": "success"}
    return {"status": "error", "message": "Username taken"}

@app.post("/login")
def login(req: AuthRequest):
    if login_user(req.username, req.password):
        return {"status": "success", "username": req.username}
    return {"status": "error", "message": "Invalid credentials"}

# --- NEW: Get list of previous sessions ---
@app.get("/threads/{username}")
def get_threads_endpoint(username: str):
    threads = get_user_threads(username)
    return {"threads": threads}

# --- NEW: Get specific chat history ---
@app.post("/history")
def get_history_endpoint(req: HistoryRequest):
    rows = get_history(req.username, req.thread_id)
    # Convert to JSON friendly format
    history = [{"role": r[0], "content": r[1]} for r in rows]
    return {"history": history}

@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    try:
        messages = []
        if req.username:
            db_rows = get_history(req.username, req.thread_id)
            for role, content in db_rows:
                if role == "user": messages.append(HumanMessage(content=content))
                else: messages.append(AIMessage(content=content))
        else:
            messages = guest_store.get(req.thread_id, [])

        messages.append(HumanMessage(content=req.message))

        result = agent_app.invoke({"messages": messages})
        data = result.get("final_response", {})
        reply = data.get("chat_message", "")
        plan = data.get("roadmap")

        # Create a combined string for DB if there is a plan, to ensure it shows in history
        # (Simple workaround to save complex state in text-only DB column)
        db_content = reply
        if plan:
            db_content += f"\n\n[PLAN_CREATED]: {plan.get('topic')}"

        if req.username:
            save_message(req.username, req.thread_id, "user", req.message)
            save_message(req.username, req.thread_id, "ai", db_content)
        else:
            if req.thread_id not in guest_store: guest_store[req.thread_id] = []
            guest_store[req.thread_id].append(HumanMessage(content=req.message))
            guest_store[req.thread_id].append(AIMessage(content=reply))

        return {"reply": reply, "plan": plan, "status": "success"}
    except Exception as e:
        print(f"Error: {e}")
        return {"reply": "Error processing request", "status": "error"}

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