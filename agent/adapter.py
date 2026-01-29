import json
import os
from dotenv import load_dotenv
load_dotenv()
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from agent.schemas import LearningRoadmap
#import opik

#Initialize LLM
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.5)
structured_llm = llm.with_structured_output(LearningRoadmap)


#@opik.track(name="Adapter Node")
def adapt_plan(current_plan: dict, user_feedback: str):
    """
    Refine Based on User Feedback and Plan.
    """

    # Convert dict into  JSON for LLM to read
    plan_str = json.dumps(current_plan, indent=2)

    system_prompt = """
    You are PathFinder's Adaptation Engine.
    Your job is to MODIFY an existing learning plan based on user feedback.

    INPUTS:
    1.Current Plan (JSON)
    2.User Feedback (e.g., "Too hard", "I'm behind schedule")

    INSTRUCTIONS:
    - If user says "Too hard": Simplify topics, add more basics, extend timeline.
    - If user says "Too easy": Add advanced topics, speed up.
    - If user says "I missed a week": Shift the schedule.
    - ALWAYS return the full valid JSON structure.
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "Current Plan:\n{plan}\n\nUser Feedback: {feedback}")
    ])

    # Chain
    chain = prompt | structured_llm

    print(f"Re-planning based on: '{user_feedback}'")
    result = chain.invoke({"plan": plan_str, "feedback": user_feedback})

    return result