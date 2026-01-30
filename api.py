from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
import sys
import os
import traceback
import logging

# Cấu hình Log để xem trên Render
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn")

# Import Agent
sys.path.append(os.getcwd())
agent_app = None
try:
    from agent.graph import app as loaded_app

    agent_app = loaded_app
    print("✅ LOAD AGENT THÀNH CÔNG!")
except Exception as e:
    print(f"❌ LỖI IMPORT AGENT: {e}")

app = FastAPI(title="PathFinder AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- 1. MODEL INPUT ---
class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None


# --- 2. MODEL OUTPUT (Đã sửa lỗi Validation) ---
class ChatResponse(BaseModel):
    reply: str
    thread_id: str
    plan: Optional[Dict[str, Any]] = None
    # 👇 QUAN TRỌNG: Thêm giá trị mặc định để không bao giờ bị lỗi "Field required"
    status: str = "success"


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    current_thread_id = request.thread_id or str(uuid.uuid4())
    print(f"📩 Nhận message: {request.message} (Thread: {current_thread_id})")

    # Kiểm tra Agent
    if agent_app is None:
        return ChatResponse(
            reply="Lỗi Server: Agent chưa khởi động được.",
            thread_id=current_thread_id,
            status="error"
        )

    try:
        # Chuẩn bị input cho Graph
        inputs = {
            "user_message": request.message,
            "current_plan": None,
            "dialogue_state": "start"
        }
        config = {"configurable": {"thread_id": current_thread_id}}

        # Gọi Agent
        print("⏳ Đang xử lý...")
        result = agent_app.invoke(inputs, config=config)
        print("✅ Agent xử lý xong!")

        # Lấy kết quả
        final_plan = result.get("current_plan")
        dialogue_state = result.get("dialogue_state")

        # Tạo câu trả lời
        bot_reply = "Đã nhận thông tin."
        if final_plan:
            topic = final_plan.get('topic', 'chủ đề mới')
            bot_reply = f"Tôi đã tạo lộ trình học cho: {topic}"
        elif dialogue_state:
            bot_reply = f"AI phản hồi: {dialogue_state}"

        # 👇 TRẢ VỀ KẾT QUẢ (Không bao giờ thiếu status nữa)
        return ChatResponse(
            reply=str(bot_reply),
            thread_id=current_thread_id,
            plan=final_plan,
            status="success"
        )

    except Exception as e:
        # Bắt lỗi và in ra logs
        error_msg = traceback.format_exc()
        print(f"❌ CRASH LOGIC: \n{error_msg}")

        return ChatResponse(
            reply=f"Xin lỗi, có lỗi xảy ra: {str(e)}",
            thread_id=current_thread_id,
            status="error"
        )


@app.get("/")
def health_check():
    return {"status": "ok", "message": "PathFinder API is running"}