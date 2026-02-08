import operator
from typing import TypedDict, List, Any, Annotated, Optional
from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages

# Roadmap

class WeekModule(BaseModel):
    week_number: int = Field(..., description="The week number (1, 2, 3...)")
    topic: str = Field(..., description="Main topic for the week")
    goal: str = Field(..., description="The specific learning outcome for this week")
    # specific tasks are better than just a list of strings for UI rendering
    daily_tasks: List[str] = Field(..., description="3-5 specific sub-topics or actionable tasks (e.g., 'Day 1: Install Python')")
    resources: List[str] = Field(..., description="2-3 specific search terms for resources (e.g., 'Corey Schafer Python Lists')")

class LearningRoadmap(BaseModel):
    topic: str = Field(..., description="The main subject (e.g., 'Python for Data Science')")
    total_weeks: int = Field(..., description="Total duration of the plan")
    difficulty: str = Field(..., description="Beginner, Intermediate, or Advanced")
    schedule: List[WeekModule] = Field(..., description="List of weekly modules")

# Quiz

class QuizQuestion(BaseModel):
    question: str = Field(..., description="The question text")
    options: List[str] = Field(..., description="A list of exactly 4 possible answers")
    correct_answer: str = Field(..., description="The correct answer text (must match one of the options)")
    explanation: str = Field(..., description="Brief explanation of why the answer is correct")

class Quiz(BaseModel):
    topic: str = Field(..., description="The topic being tested")
    questions: List[QuizQuestion] = Field(..., description="List of 5-10 questions")

# Graph

class AgentState(TypedDict):
    # 'add_messages' ensures new messages are appended to history, not overwritten
    messages: Annotated[List[Any], add_messages]
    user_message: str
    context: str
    # Store the structured plan here so we can pass it to the Quiz Generator later
    current_plan: Optional[dict]
    dialogue_state: str