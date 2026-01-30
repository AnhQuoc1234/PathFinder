from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
import sys
import os
import traceback

from langchain_core.messages import HumanMessage

# Import Agent Graph
sys.path.append(os.getcwd())
try:
    from agent.graph import app as agent_app
except ImportError:
    #Fallback to check error
    print("Module not found.")
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
    plan: Optional[Dict[str, Any]] = None
    status: str


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):

    current_thread_id = request.thread_id or str(uuid.uuid4())

    try:
        # Print Log
        print(f"User Input: {request.message}")
        print(f"Thread Id: {current_thread_id}")

        if agent_app is None:
            raise Exception("Agent Graph chưa được load thành công.")

        # Input
        inputs = {"messages": [HumanMessage(content=request.message)]}
        config = {"configurable": {"thread_id": current_thread_id}}

        # Call Agent
        print("Call Agent")
        result = agent_app.invoke(inputs, config=config)

        # Print raw log for debug
        print(f"Raw result: {result}")

        # Handle bot replie
        bot_reply = "Sorry, I can't answer."  # Giá trị mặc định

        if result and "messages" in result and len(result["messages"]) > 0:
            last_msg = result["messages"][-1]
            bot_reply = last_msg.content

        # Return ChatResponse
        return ChatResponse(
            reply=str(bot_reply),
            thread_id=current_thread_id,
            status="success"
        )

    except Exception as e:
        print("Crash")
        traceback.print_exc()

        # To json for front end not crash
        return ChatResponse(
            reply=f"Server Error: {str(e)}",
            thread_id=current_thread_id,
            status="error"
        )