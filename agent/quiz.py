# agent/quiz.py
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List

# Question structure
class QuizQuestion(BaseModel):
    question: str = Field(description="The question text")
    options: List[str] = Field(description="List of 4 options")
    correct_index: int = Field(description="Index of the correct answer (0-3)")
    explanation: str = Field(description="Explanation why the answer is correct")

class QuizResponse(BaseModel):
    questions: List[QuizQuestion] = Field(description="List of 5 multiple choice questions")

# Setup AI
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
structured_llm = llm.with_structured_output(QuizResponse)

system_prompt = """You are a strict examiner.
Generate a hard 5-question multiple-choice quiz about the given topic.
- Ensure options are tricky but fair.
- Provide a clear explanation for the correct answer.
- Return strictly JSON."""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("user", "Create a quiz about: {topic}")
])

chain = prompt | structured_llm

#Generate quiz func
def generate_quiz(topic: str):
    try:
        print(f"DEBUG: Generating quiz for '{topic}'")
        result = chain.invoke({"topic": topic})
        return result.model_dump() # Trả về Dictionary
    except Exception as e:
        print(f"Quiz Error: {e}")
        return {"questions": []}