import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from agent.schemas import LearningRoadmap
import opik

load_dotenv()

# Initialize LLM with Structured Output (JSON Mode)
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)
structured_llm = llm.with_structured_output(LearningRoadmap)


@opik.track(name="Planner Node")  # Tracks inputs/outputs by using OPIK
def generate_plan(user_goal: str, duration: str = "4 weeks"):
    """
    Generates a structured learning path based on goal and duration.
    """

    #Prompt
    system_prompt = """
    You are PathFinder, an expert curriculum designer.
    Create a detailed, step-by-step learning path for the user.

    Rules:
    - Be realistic. Don't overload the user.
    - Structure the response strictly as JSON.
    - Include specific search terms for resources.
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "Goal: {goal}\nDuration: {duration}")
    ])

    #Chain
    chain = prompt | structured_llm

    #Run
    print(f" Generating plan for: {user_goal}")
    result = chain.invoke({"goal": user_goal, "duration": duration})

    return result