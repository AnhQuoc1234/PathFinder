import re
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List, Dict, Any  # <--- QUAN TRỌNG: Phải có Dict, Any


#Schema
class LLMOutput(BaseModel):
    topic: str
    difficulty: str
    schedule: List[str]


#Set up llm
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
structured_llm = llm.with_structured_output(LLMOutput)  # Dùng schema đơn giản cho AI

system_prompt = "You are an education consultant. Create a learning roadmap."
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("user", "{input}")
])

chain = prompt | structured_llm


# Generate plan func
def generate_plan(user_input: str):
    try:
        # Gọi AI
        result = chain.invoke({"input": user_input})

        raw_schedule = result.schedule
        formatted_schedule = []

        for i, step in enumerate(raw_schedule, 1):
            clean_step = re.sub(r'^(Week|Tuần)\s*\d+[:\.]?\s*', '', step, flags=re.IGNORECASE).strip()

            # convert into object
            formatted_schedule.append({
                "week": i,  # Số nguyên (Frontend dùng cái này hiển thị số tuần)
                "topic": clean_step,  # Nội dung chính (đã làm sạch)
                "content": clean_step  # Dự phòng
            })

        # return result
        return {
            "topic": result.topic,
            "difficulty": result.difficulty,
            "schedule": formatted_schedule
        }

    except Exception as e:
        print(f"Planner Error: {e}")
        return {
            "topic": "Error",
            "difficulty": "Unknown",
            "schedule": []
        }