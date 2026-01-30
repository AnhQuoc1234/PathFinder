from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
import sys
import os
import traceback
import json

# Import Agent Graph
sys.path.append(os.getcwd())
try:
    from agent.graph import app as agent_app
except ImportError:
    print("Error: module agent.graph not available")
    agent_app = None

# Initialize Api
app = FastAPI(title="PathFinder AI API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Defining Input
class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None


# Defining Output
class ChatResponse(BaseModel):
    reply: str
    thread_id: str
    plan: Optional[Dict[str, Any]] = None  # Đây là nơi chứa Roadmap
    status: str


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):

    current_thread_id = request.thread_id or str(uuid.uuid4())

    try:
        # Log
        print(f"User Input: {request.message}")
        print(f"Thread ID: {current_thread_id}")

        if agent_app is None:
            raise Exception("Agent Graph chưa được load.")

        # Input
        inputs = {
            "user_message": request.message,
            "current_plan": None,  # Khởi tạo rỗng
            "dialogue_state": "start"
        }

        config = {"configurable": {"thread_id": current_thread_id}}

        # Call Agent
        print("Call Agent")
        result = agent_app.invoke(inputs, config=config)

        # Handle result
        print(f"Result {result}")

        final_plan = result.get("current_plan")
        dialogue_state = result.get("dialogue_state")

        # Generating reply
        bot_reply = "Handling request"

        if final_plan:
            bot_reply = f"Here is the plan I have created {final_plan.get('topic', 'Unknown Topic')}"
        elif dialogue_state:
            bot_reply = f"Status {dialogue_state}"

        # Return ChatResponse
        return ChatResponse(
            reply=bot_reply,
            thread_id=current_thread_id,
            plan=final_plan,  # Trả về Json Plan vào đúng chỗ của nó
            status="success"
        )

    except Exception as e:
        print("Crash:")
        traceback.print_exc()

        return ChatResponse(
            reply=f"Server Error: {str(e)}",
            thread_id=current_thread_id,
            status="error"
        )