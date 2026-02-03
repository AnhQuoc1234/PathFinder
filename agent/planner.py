from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List, Optional

# Define Schema
class LearningRoadmap(BaseModel):
    topic: str = Field(description="The main subject")
    difficulty: str = Field(description="Level", default="Beginner")
    schedule: List[str] = Field(description="Weekly goals")

# Setup LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
structured_llm = llm.with_structured_output(LearningRoadmap)

system_prompt = "You are an education consultant. Create a learning roadmap."
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("user", "{input}")
])

chain = prompt | structured_llm

def generate_plan(user_input: str):
    try:
        result = chain.invoke({"input": user_input})

        if hasattr(result, "model_dump"):
            return result.model_dump()
        else:
            return result.dict()
    except Exception as e:
        print(f"Planner Error: {e}")
        return {
            "topic": "Error",
            "difficulty": "Beginner",
            "schedule": ["Error generating plan"]
        }