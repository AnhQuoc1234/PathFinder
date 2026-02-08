from typing import TypedDict, Optional, Literal
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from agent.schemas import LearningRoadmap, QuizData

# Output structured data strictly
llm = ChatOpenAI(model="gpt-4o", temperature=0)


class AgentState(TypedDict):
    user_message: str
    plan_data: Optional[dict]  # Store the plan here!
    next_action: Optional[Literal["visualize", "quiz", "none"]]


def planner_node(state: AgentState):
    """Generates the text-based plan (JSON)"""
    planner = llm.with_structured_output(LearningRoadmap)
    plan = planner.invoke(f"Create a 4-week study plan for: {state['user_message']}")

    return {"plan_data": plan.dict(), "next_action": "none"}


def visualizer_node(state: AgentState):
    """Generates ONLY the Mermaid Code based on the existing plan"""
    if not state.get("plan_data"):
        return {}  # No plan to visualize

    prompt = f"Convert this learning plan into a Mermaid.js Mindmap string. Return ONLY the code, no markdown:\n{state['plan_data']}"
    # We ask for raw text here for simplicity, or use a schema for stricter safety
    code = llm.invoke(prompt).content.replace("```mermaid", "").replace("```", "")
    return {"mermaid_code": code}

# ... (Quiz node logic is similar: takes plan_data -> generates QuizData)