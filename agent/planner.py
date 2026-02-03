from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List


# Schema
class Step(BaseModel):
    week: int = Field(description="Number of the week or day (e.g., 1, 2, 3)")
    topic: str = Field(description="Content of the topic, without 'Week X:' prefix")


# Learning Road map
class LearningRoadmap(BaseModel):
    topic: str = Field(description="The main subject")
    difficulty: str = Field(description="Level")
    schedule: List[Step] = Field(description="List of structured steps")


# Setup LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
structured_llm = llm.with_structured_output(LearningRoadmap)

system_prompt = """You are an education consultant. 
Create a detailed learning roadmap.
IMPORTANT: Break down the schedule into specific weeks/days."""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("user", "{input}")
])

chain = prompt | structured_llm


# Generate plan func
def generate_plan(user_input: str):
    try:
        print(f"DEBUG: Generating plan for '{user_input}'")

        # Call AI
        result = chain.invoke({"input": user_input})

        final_plan = result.model_dump()

        print("DEBUG: Plan generated with STRICT schema")
        return final_plan

    except Exception as e:
        print(f"Planner Error: {e}")
        return {
            "topic": "Error",
            "difficulty": "Unknown",
            "schedule": []
        }