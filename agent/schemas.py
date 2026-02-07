from pydantic import BaseModel, Field
from typing import TypedDict, List, Any

# Define single Week
class WeekModule(BaseModel):
    week_number: int = Field(..., description="The week number (1, 2, 3...)")
    topic: str = Field(..., description="Main topic for the week")
    description: str = Field(..., description="Description of the week")
    daily_tasks: List[str] = Field(..., description="3-5 specific sub-topics or tasks")
    resources: List[str] = Field(..., description="Suggested keywords for finding resources (e.g., 'Official Python Docs', 'YouTube: Corey Schafer')")

# Define Roadmap
class LearningRoadmap(BaseModel):
    goal: str = Field(..., description="The user's original learning goal")
    total_weeks: int = Field(..., description="Total duration of the plan")
    schedule: List[WeekModule] = Field(..., description="List of weekly modules")
    difficulty: str = Field(..., description="Beginner, Intermediate, or Advanced")

#Define AgentSate
class AgentState(TypedDict):
    user_message: str
    context: str
    messages: List[Any]
    dialogue_state: str
    current_plan: Any