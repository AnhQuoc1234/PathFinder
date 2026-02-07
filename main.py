from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uuid
import sys
import os
import traceback
import logging

# Configure Log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn")

# Import System Path
sys.path.append(os.getcwd())

# Import agent module
agent_app = None
generate_quiz = None

try:
    from agent.graph import app as loaded_app

    agent_app = loaded_app
    print("Load Agent Graph Successful")
except Exception as e:
    print(f"Import Agent Graph Error: {e}")

try:
    from agent.quiz import generate_quiz

    print("Load Quiz Agent Successful")
except Exception as e:
    print(f"Import Quiz Agent Error: {e}")

# Initialize app
app = FastAPI(title="PathFinder AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Define data model

# Model for Chat
class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: Optional[str] = "No Response"
    thread_id: Optional[str] = ""
    plan: Optional[Dict[str, Any]] = None
    status: Optional[str] = "success"


# Model for Quiz
class QuizRequest(BaseModel):
    topic: str


# API Endpoints

@app.get("/")
def health_check():
    return {"status": "ok", "agent": "active" if agent_app else "inactive"}


# Endpoint: Chat & Generate Plan
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    current_thread_id = request.thread_id or str(uuid.uuid4())
    print(f"Receive Message: {request.message}")

    if agent_app is None:
        return ChatResponse(reply="Server Error: Agent is not working.", status="error")

    try:
        inputs = {
            "user_message": request.message,
            "current_plan": None,
            "dialogue_state": "start"
        }
        config = {"configurable": {"thread_id": current_thread_id}}

        # Call Agent Graph
        result = agent_app.invoke(inputs, config=config)

        # Handle current plan
        raw_plan = result.get("current_plan")
        final_plan = None
        if raw_plan:
            if hasattr(raw_plan, "dict"):
                final_plan = raw_plan.dict()
            elif hasattr(raw_plan, "model_dump"):
                final_plan = raw_plan.model_dump()
            elif isinstance(raw_plan, dict):
                final_plan = raw_plan

        # Generate answer
        dialogue_state = result.get("dialogue_state")
        bot_reply = "I have created a learning map for you below."

        if final_plan:
            topic = final_plan.get('topic', 'your topic')
            bot_reply = f"Here is the detailed roadmap for {topic}. Click 'Test Knowledge' to practice!"
        elif dialogue_state:
            bot_reply = str(dialogue_state)

        return ChatResponse(
            reply=bot_reply,
            thread_id=str(current_thread_id),
            plan=final_plan,
            status="success"
        )

    except Exception as e:
        error_msg = traceback.format_exc()
        print(f"Crash: {error_msg}")
        return ChatResponse(reply=f"System Error: {str(e)}", status="error")


# Endpoint: Generate Quiz
@app.post("/quiz")
async def quiz_endpoint(request: QuizRequest):
    print(f"Generating Quiz for topic: {request.topic}")

    if generate_quiz is None:
        return {"questions": []}

    try:
        # Call agent/quiz.py
        data = generate_quiz(request.topic)
        return data
    except Exception as e:
        print(f"Quiz Error: {e}")
        return {"questions": []}