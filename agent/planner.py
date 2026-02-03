import re
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List, Dict, Any  # <-- Thêm Dict, Any


# Schema
class LearningRoadmap(BaseModel):
    topic: str = Field(description="The main subject")
    difficulty: str = Field(description="Level", default="Beginner")

    schedule: List[Any] = Field(description="List of weekly goals")


# Setup LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

class LLMOutput(BaseModel):
    topic: str
    difficulty: str
    schedule: List[str]  # LLM trả về list string cho dễ


structured_llm = llm.with_structured_output(LLMOutput)

system_prompt = "You are an education consultant. Create a learning roadmap."
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("user", "{input}")
])

chain = prompt | structured_llm


# Generate plan
def generate_plan(user_input: str):
    try:
        # Call AI
        result = chain.invoke({"input": user_input})

        raw_schedule = result.schedule
        formatted_schedule = []

        for i, step in enumerate(raw_schedule, 1):
            clean_step = re.sub(r'^(Week|Tuần)\s*\d+[:\.]?\s*', '', step, flags=re.IGNORECASE)

            formatted_schedule.append({
                "week": i,
                "content": clean_step,
                "topic": clean_step
            })

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