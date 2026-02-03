from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List, Optional


# Define Learning Roadmap
class LearningRoadmap(BaseModel):
    topic: str = Field(description="The main subject of the learning plan")

    # Add Difficult
    difficulty: str = Field(
        description="Target difficulty level (Beginner, Intermediate, or Advanced)",
        default="Beginner"
    )

    schedule: List[str] = Field(description="List of weekly learning goals or steps")


# Setup Model & Prompt
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

system_prompt = """You are an expert education consultant.
Create a structured learning roadmap based on the user's request.
Ensure the output matches the required JSON structure strictly."""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("user", "{input}")
])

# Connect LLM with structured output
structured_llm = llm.with_structured_output(LearningRoadmap)

# Chain
chain = prompt | structured_llm


# Plan Func
def generate_plan(user_input: str):
    """
    Generate learning plan. from user input.
    Return object LearningRoadmap (contain topic, difficulty, schedule).
    """
    try:
        result = chain.invoke({"input": user_input})
        return result.dict()
    except Exception as e:
        # Fallback if LLM error
        print(f"Error generating plan: {e}")
        return {
            "topic": "General Learning",
            "difficulty": "Beginner",
            "schedule": ["Step 1: Research basics", "Step 2: Practice daily"]
        }