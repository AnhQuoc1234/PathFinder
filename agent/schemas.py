from pydantic import BaseModel, Field
from typing import List, Optional

# --- PLAN STRUCTURE ---
class DayTask(BaseModel):
    day: str = Field(..., description="Day identifier (e.g., 'Day 1')")
    task: str = Field(..., description="The specific topic or exercise")

class WeekModule(BaseModel):
    title: str = Field(..., description="Theme of the week")
    days: List[DayTask] = Field(..., description="List of tasks for this week")

class LearningRoadmap(BaseModel):
    topic: str = Field(..., description="The subject being learned")
    weeks: List[WeekModule] = Field(..., description="4-week breakdown")

# --- QUIZ STRUCTURE ---
class QuizQuestion(BaseModel):
    question: str
    options: List[str] = Field(..., description="4 possible answers")
    correct_answer: str
    explanation: str

class QuizData(BaseModel):
    topic: str
    questions: List[QuizQuestion]

# --- CHAT RESPONSE STRUCTURE ---
class AgentResponse(BaseModel):
    chat_message: str = Field(..., description="Friendly reply text")
    roadmap: Optional[LearningRoadmap] = Field(None, description="Structured plan if requested")
    mermaid_code: Optional[str] = Field(None, description="Mermaid.js code if requested")