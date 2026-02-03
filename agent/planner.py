from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List, Optional


# Schema
class LearningRoadmap(BaseModel):
    topic: str = Field(description="The main subject")
    difficulty: str = Field(description="Level", default="Beginner")
    schedule: List[str] = Field(description="List of weekly goals")


# Setup LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
structured_llm = llm.with_structured_output(LearningRoadmap)

system_prompt = "You are an education consultant. Create a learning roadmap."
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("user", "{input}")
])

chain = prompt | structured_llm


# Generate plan
def generate_plan(user_input: str):
    try:
        # Gọi AI
        result = chain.invoke({"input": user_input})

        raw_schedule = result.schedule
        formatted_schedule = []

        for i, step in enumerate(raw_schedule, 1):
            formatted_schedule.append({
                "week": i,
                "content": step,
                "topic": step
            })

        return {
            "topic": result.topic,
            "difficulty": result.difficulty,
            "schedule": formatted_schedule  # Return Object
        }

    except Exception as e:
        print(f"Planner Error: {e}")
        return {
            "topic": "Error",
            "difficulty": "Unknown",
            "schedule": []
        }