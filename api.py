from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
import sys
import os
import traceback
import logging

# Cấu hình Log
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


# --- 2. MODEL OUTPUT (PHIÊN BẢN AN TOÀN) ---
# Tôi đã thêm Optional và giá trị mặc định cho TẤT CẢ các trường
# Để dù có trường nào bị None, nó vẫn trả về được mà không lỗi 500.
class ChatResponse(BaseModel):
    reply: Optional[str] = "Không có phản hồi"
    thread_id: Optional[str] = ""
    plan: Optional[Dict[str, Any]] = None
    status: Optional[str] = "success"


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    # Đảm bảo thread_id luôn là string, không bao giờ None
    current_thread_id = request.thread_id or str(uuid.uuid4())

    # Log để debug
    print(f"📩 Nhận message: {request.message}")

    # Kiểm tra Agent
    if agent_app is None:
        return ChatResponse(
            reply="Lỗi Server: Agent chưa khởi động được.",
            thread_id=current_thread_id,
            status="error"
        )

    try:
        # Input cho Graph
        inputs = {
            "user_message": request.message,
            "current_plan": None,
            "dialogue_state": "start"
        }
        config = {"configurable": {"thread_id": current_thread_id}}

        # Gọi Agent
        result = agent_app.invoke(inputs, config=config)

        # --- XỬ LÝ KẾT QUẢ CẨN THẬN ---

        # 1. Lấy Plan (nếu có) và đảm bảo nó là Dict
        raw_plan = result.get("current_plan")
        final_plan = None
        if raw_plan:
            # Nếu nó là Pydantic object (do dùng thư viện mới), chuyển thành dict
            if hasattr(raw_plan, "dict"):
                final_plan = raw_plan.dict()
            elif hasattr(raw_plan, "model_dump"):  # Pydantic v2
                final_plan = raw_plan.model_dump()
            elif isinstance(raw_plan, dict):
                final_plan = raw_plan

        # 2. Xử lý câu trả lời text
        dialogue_state = result.get("dialogue_state")
        bot_reply = "Đã nhận thông tin."

        if final_plan:
            topic = final_plan.get('topic', 'chủ đề mới')
            bot_reply = f"Tôi đã tạo lộ trình học cho: {topic}"
        elif dialogue_state:
            bot_reply = f"AI phản hồi: {dialogue_state}"

        # 3. Trả về kết quả (Ép kiểu string để tránh Validation Error)
        return ChatResponse(
            reply=str(bot_reply) if bot_reply else "...",
            thread_id=str(current_thread_id),
            plan=final_plan,
            status="success"
        )

    except Exception as e:
        error_msg = traceback.format_exc()
        print(f"❌ CRASH LOGIC: \n{error_msg}")

        return ChatResponse(
            reply=f"Lỗi hệ thống: {str(e)}",
            thread_id=str(current_thread_id),
            status="error"
        )


@app.get("/")
def health_check():
    return {"status": "ok"}