from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
import sys
import os
import traceback
import logging

#OPIK
try:
    from opik.integrations.langchain import OpikTracer
    print("Load Opik Tracer Successful")
except Exception as e:
    print(f" Import Opik Tracer Error: {e}")
    OpikTracer = None

# Configure Log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn")

# Import Agent
sys.path.append(os.getcwd())
agent_app = None
try:
    from agent.graph import app as loaded_app

    agent_app = loaded_app
    print("Load Agent Successful")
except Exception as e:
    print(f" Import Agent Error: {e}")

app = FastAPI(title="PathFinder AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


#Model Input
class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None


# Model Output
class ChatResponse(BaseModel):
    reply: Optional[str] = "No Response"
    thread_id: Optional[str] = ""
    plan: Optional[Dict[str, Any]] = None
    status: Optional[str] = "success"


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    # Make sure thread id is string
    current_thread_id = request.thread_id or str(uuid.uuid4())

    # Log for debug
    print(f"Receive Message: {request.message}")

    # Check Agent
    if agent_app is None:
        return ChatResponse(
            reply="Server Error: Agent is not working.",
            thread_id=current_thread_id,
            status="error"
        )

    try:
        # Input for Graph
        inputs = {
            "user_message": request.message,
            "current_plan": None,
            "dialogue_state": "start"
        }
        config = {"configurable": {"thread_id": current_thread_id}}

        # Call Agent
        result = agent_app.invoke(inputs, config=config)

        # Get Plan
        raw_plan = result.get("current_plan")
        final_plan = None
        if raw_plan:
            # If pydantic is object change into dict
            if hasattr(raw_plan, "dict"):
                final_plan = raw_plan.dict()
            elif hasattr(raw_plan, "model_dump"):  # Pydantic v2
                final_plan = raw_plan.model_dump()
            elif isinstance(raw_plan, dict):
                final_plan = raw_plan

        # Handle
        dialogue_state = result.get("dialogue_state")
        bot_reply = "Information Receive."

        if final_plan:
            topic = final_plan.get('topic', '')
            bot_reply = f"Here is the new plan: {topic}"
        elif dialogue_state:
            bot_reply = f"AI Respond: {dialogue_state}"

        # Chat Response (Convert to string to avoid Validation Error)
        return ChatResponse(
            reply=str(bot_reply) if bot_reply else "...",
            thread_id=str(current_thread_id),
            plan=final_plan,
            status="success"
        )

    except Exception as e:
        error_msg = traceback.format_exc()
        print(f" CRASH LOGIC: \n{error_msg}")

        return ChatResponse(
            reply=f"System Error: {str(e)}",
            thread_id=str(current_thread_id),
            status="error"
        )


@app.get("/")
def health_check():
    return {"status": "ok"}