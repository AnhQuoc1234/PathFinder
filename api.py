from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
import sys
import os

# Import Agent Graph
sys.path.append(os.getcwd())
from agent.graph import app as agent_app

# Initialize Api
app = FastAPI(title="PathFinder AI API")

# Configure CORS so Frontend can be able to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong production nên đổi thành domain cụ thể của bạn
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
    plan: Optional[Dict[str, Any]] = None
    status: str


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        # Create thread id
        thread_id = request.thread_id or str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        # Call Agent
        final_state = agent_app.invoke(
            {"user_message": request.message},
            config=config
        )

        # Get Result from state
        dialogue_status = final_state.get("dialogue_status")
        current_plan = final_state.get("current_plan")

        # Handle Plan: Convert Pydantic object into dict
        plan_data = None
        if current_plan:
            # Check if object Pydantic use .dict()
            if hasattr(current_plan, 'dict'):
                plan_data = current_plan.dict()
            else:
                plan_data = current_plan

        # Create agent response
        bot_reply = "I've processed your request."
        if dialogue_status == "generate_plan":
            bot_reply = "I've crafted a new learning path for you. Check it out on the right! 👉"
        elif dialogue_status == "update_progress":
            bot_reply = "I've updated the plan based on your feedback. 🚀"

        return ChatResponse(
            reply=bot_reply,
            thread_id=thread_id,
            plan=plan_data,
            status=dialogue_status
        )

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# To run server use: uvicorn api:app --reload