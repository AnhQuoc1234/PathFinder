from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
from langchain_core.messages import HumanMessage, AIMessage

from agent.graph import app as agent_app
from database import init_db, register_user, login_user, save_chat_message, get_chat_history

# Initialize DB
init_db()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- IN-MEMORY STORE FOR GUESTS ---
# (Resets when server restarts - perfect for temporary guest sessions)
guest_memory: Dict[str, List] = {}


class AuthRequest(BaseModel):
    username: str
    password: str


class ChatRequest(BaseModel):
    message: str
    thread_id: str
    username: Optional[str] = None  # If None, treated as Guest


class QuizRequest(BaseModel):
    topic: str


# --- AUTH ENDPOINTS ---
@app.post("/register")
def register(req: AuthRequest):
    if register_user(req.username, req.password):
        return {"status": "success", "message": "Registered successfully!"}
    return {"status": "error", "message": "Username taken."}


@app.post("/login")
def login(req: AuthRequest):
    if login_user(req.username, req.password):
        return {"status": "success", "username": req.username}
    return {"status": "error", "message": "Invalid credentials."}


# --- CHAT ENDPOINT ---
@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    try:
        # 1. Retrieve History based on User Type
        history = []
        if req.username:
            # Logged In: Get from DB
            raw_history = get_chat_history(req.username, req.thread_id)
            # Convert tuples back to Message objects
            history = [HumanMessage(content=msg) if role == "human" else AIMessage(content=msg) for role, msg in
                       raw_history]
        else:
            # Guest: Get from RAM
            if req.thread_id not in guest_memory:
                guest_memory[req.thread_id] = []
            history = guest_memory[req.thread_id]

        # 2. Run Agent with History
        inputs = {"user_message": req.message, "history": history}
        result = agent_app.invoke(inputs)
        data = result.get("final_response", {})

        reply = data.get("chat_message", "")
        plan = data.get("roadmap")

        # 3. Save New Interaction
        if req.username:
            # Save to DB
            save_chat_message(req.username, req.thread_id, "user", req.message)
            save_chat_message(req.username, req.thread_id, "ai", reply)
        else:
            # Save to RAM
            guest_memory[req.thread_id].append(HumanMessage(content=req.message))
            guest_memory[req.thread_id].append(AIMessage(content=reply))

        return {
            "reply": reply,
            "plan": plan,
            "status": "success"
        }
    except Exception as e:
        print(f"Error: {e}")
        return {"reply": "Error processing request.", "status": "error"}


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