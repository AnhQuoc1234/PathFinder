from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List


# Schema
class Step(BaseModel):
    week: int = Field(description="The week or day number (Example: 1, 2, 3)")
    topic: str = Field(description="The content of the topic. DO NOT include 'Week X' or 'Day X' prefix here.")


class RoadmapResponse(BaseModel):
    topic: str = Field(description="The main subject")
    difficulty: str = Field(description="The difficulty level")
    schedule: List[Step] = Field(description="List of learning steps")


# LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
structured_llm = llm.with_structured_output(RoadmapResponse)

system_prompt = """You are an expert education consultant.
Create a detailed learning roadmap.
IMPORTANT:
1. Separate the week number and the topic content.
2. The 'topic' must NOT contain 'Week 1:' or 'Day 1:' text."""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("user", "{input}")
])

chain = prompt | structured_llm


# Generate plan func
def generate_plan(user_input: str):
    try:
        print(f"DEBUG: Planning for '{user_input}'...")

        #Call AI
        result = chain.invoke({"input": user_input})

        final_plan = result.model_dump()

        print("DEBUG: Plan generated successfully with STRICT schema.")
        return final_plan

    except Exception as e:
        print(f"ERROR in Planner: {e}")
        return {
            "topic": "Error generating plan",
            "difficulty": "Unknown",
            "schedule": []
        }