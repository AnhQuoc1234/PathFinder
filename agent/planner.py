import re
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List, Dict, Any


# Schema
class LLMOutput(BaseModel):
    topic: str = Field(description="The main subject of the roadmap")
    difficulty: str = Field(description="The difficulty level (e.g., Beginner, Intermediate)")
    schedule: List[str] = Field(description="List of learning steps as strings (e.g., 'Introduction to variables')")


# Set up LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
structured_llm = llm.with_structured_output(LLMOutput)

system_prompt = """You are an expert education consultant. 
Create a detailed learning roadmap based on the user's request. 
Return the schedule as a simple list of strings."""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("user", "{input}")
])

chain = prompt | structured_llm


# Main Processing Function
def generate_plan(user_input: str):
    try:
        print(f"DEBUG: Generating plan for '{user_input}'")

        # Invoke AI
        result = chain.invoke({"input": user_input})

        raw_schedule = result.schedule
        formatted_schedule = []

        # Iterate through the list and clean up the text
        for i, step in enumerate(raw_schedule, 1):
            # Regex to remove prefixes like "Week 1:", "Day 1:", "Step 1."
            # Example: "Week 1: Introduction" -> "Introduction"
            clean_text = re.sub(r'^(Week|Day|Step|Tuần)\s*\d+[:\.]?\s*', '', step, flags=re.IGNORECASE).strip()

            # Create a structured object for the Frontend
            formatted_schedule.append({
                "week": i,  # Frontend uses this integer to display the step number
                "topic": clean_text,  # Cleaned content (removing duplicates)
                "content": clean_text  # Backup key
            })

        print("DEBUG: Plan generated successfully")

        # Return the final Dict (matches AgentState structure)
        return {
            "topic": result.topic,
            "difficulty": result.difficulty,
            "schedule": formatted_schedule  # Returns List[Dict]
        }

    except Exception as e:
        print(f"Planner Error: {e}")
        # Return empty structure on error to prevent crashes
        return {
            "topic": "Error",
            "difficulty": "Unknown",
            "schedule": []
        }