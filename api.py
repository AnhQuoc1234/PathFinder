from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
import sys
import os
import traceback
import logging

# Log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn")

# Import Agent
sys.path.append(os.getcwd())
agent_app = None
try:
    from agent.graph import app as loaded_app

    agent_app = loaded_app
    print("Load Agent Successfully!")
except Exception as e:
    print(f"Agent Error: {e}")

app = FastAPI(title="PathFinder AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- MODEL INPUT ---
class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None


# --- MODEL OUTPUT  ---
class ChatResponse(BaseModel):
    reply: str
    thread_id: str
    plan: Optional[Dict[str, Any]] = None
    status: str = "success"


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    current_thread_id = request.thread_id or str(uuid.uuid4())
    print(f"Receive Message {request.message} (Thread: {current_thread_id})")

    # Checking Agent
    if agent_app is None:
        return ChatResponse(
            reply="Server Error, Agent not Respond.",
            thread_id=current_thread_id,
            status="error"
        )

    try:
        # Input
        inputs = {
            "user_message": request.message,
            "current_plan": None,
            "dialogue_state": "start"
        }
        config = {"configurable": {"thread_id": current_thread_id}}

        # Call Agent
        print("Handling")
        result = agent_app.invoke(inputs, config=config)
        print("Agent finished!")

        # Get Result
        final_plan = result.get("current_plan")
        dialogue_state = result.get("dialogue_state")

        # Generate Answer
        bot_reply = "Đã nhận thông tin."
        if final_plan:
            topic = final_plan.get('topic', 'New Topic')
            bot_reply = f"I have created plan for topic: {topic}"
        elif dialogue_state:
            bot_reply = f"AI Respond: {dialogue_state}"

        # Chat Response
        return ChatResponse(
            reply=str(bot_reply),
            thread_id=current_thread_id,
            plan=final_plan,
            status="success"
        )

    except Exception as e:
        # Catch Error
        error_msg = traceback.format_exc()
        print(f"Crash Logic : \n{error_msg}")

        return ChatResponse(
            reply=f"Sorry, there is a problem {str(e)}",
            thread_id=current_thread_id,
            status="error"
        )


@app.get("/")
def health_check():
    return {"status": "ok", "message": "PathFinder API is running"}