import sys
import os
import uuid
import logging
import traceback
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Set up logging and path
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn")

sys.path.append(os.getcwd())

# Import Agent modules
from agent.graph import app as agent_app
from agent.quiz import generate_quiz
from agent.schemas import LearningRoadmap

#Initialize API
app = FastAPI(title="PathFinder AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Data models

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    thread_id: str
    # We return the structured plan (JSON) if it exists, so the UI can render it
    plan: Optional[Dict[str, Any]] = None
    status: str = "success"


class QuizRequest(BaseModel):
    topic: str
    context: Optional[str] = ""  # Optional: Pass previous chat context for better questions


# --- 5. ENDPOINTS ---

@app.get("/")
def health_check():
    return {"status": "running", "service": "PathFinder AI"}


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    # 1. Manage Thread ID (Conversation History)
    current_thread_id = request.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": current_thread_id}}

    logger.info(f"Thread: {current_thread_id} | User: {request.message}")

    try:
        # Prepare Input for Graph
        inputs = {
            "user_message": request.message
        }

        # Invoke Agent Graph
        # 'result' will be the Final State of the graph after processing
        result = agent_app.invoke(inputs, config=config)

        # Extract Data from Final State

        # Get Bot Reply (The last message in the history)
        messages = result.get("messages", [])
        bot_reply = "No response generated."
        if messages and len(messages) > 0:
            # LangGraph messages can be objects or dicts depending on setup
            last_msg = messages[-1]
            if isinstance(last_msg, dict):
                bot_reply = last_msg.get("content", "")
            else:
                bot_reply = last_msg.content

        # Get Current Plan (if any exists in state)
        final_plan = result.get("current_plan")

        # If the plan is a Pydantic object, convert to dict
        if hasattr(final_plan, "dict"):
            final_plan = final_plan.dict()
        elif hasattr(final_plan, "model_dump"):
            final_plan = final_plan.model_dump()

        return ChatResponse(
            reply=bot_reply,
            thread_id=current_thread_id,
            plan=final_plan,
            status="success"
        )

    except Exception as e:
        logger.error(f"Chat Error: {traceback.format_exc()}")
        return ChatResponse(
            reply="I'm sorry, I encountered an internal error.",
            thread_id=current_thread_id,
            status="error"
        )


@app.post("/quiz")
async def quiz_endpoint(request: QuizRequest):
    """
    Direct endpoint to generate a quiz.
    Useful if the User clicks 'Take a Quiz' button on a specific roadmap.
    """
    logger.info(f"Generating Quiz for: {request.topic}")

    try:
        # Call the logic from agent/quiz.py
        # We pass the topic and optional context
        quiz_data = generate_quiz(topic=request.topic, context=request.context)

        if quiz_data:
            return quiz_data.dict()  # Return JSON directly
        else:
            raise HTTPException(status_code=500, detail="Failed to generate quiz")

    except Exception as e:
        logger.error(f"Quiz Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)