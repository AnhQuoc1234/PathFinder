from pydantic import BaseModel, Field
from typing import List, Optional


# 1. The Plan Structure (For the first step)
class DayTask(BaseModel):
    day: str = Field(..., description="Day 1, Day 2, etc.")
    task: str = Field(..., description="The specific topic or exercise")
    resources: str = Field(..., description="A specific search term or link description")


class WeekModule(BaseModel):
    title: str = Field(..., description="Theme of the week (e.g., 'Basics')")
    days: List[DayTask] = Field(..., description="List of daily tasks")


class LearningRoadmap(BaseModel):
    topic: str
    weeks: List[WeekModule]


# 2. The Quiz Structure (For the review step)
class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: str
    explanation: str


class QuizData(BaseModel):
    topic: str
    questions: List[QuizQuestion]