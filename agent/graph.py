import os
from typing import TypedDict, Optional, List, Any
from langgraph.graph import StateGraph, END, START
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

from agent.schemas import AgentResponse, LearningRoadmap

load_dotenv()


# Define State
class AgentState(TypedDict):
    messages: List[Any]  # Chat history
    user_message: str  # Current input
    final_response: Optional[dict]  # Output for main.py


# Initialize LLM
llm = ChatOpenAI(model="gpt-4o", temperature=0)


# Nodes

def router_node(state: AgentState):
    """Decides if user wants a plan, a diagram, or just chat."""
    msg = state['user_message'].lower()

    if "mermaid" in msg or "visualize" in msg or "diagram" in msg:
        return "visualizer"
    else:
        return "planner"


def planner_node(state: AgentState):
    """Generates the Study Plan OR Chat Response"""

    structured_llm = llm.with_structured_output(AgentResponse)

    system_prompt = """
    You are PathFinder, an expert curriculum designer.
    - If the user asks to learn a skill, generate a strict 'roadmap' (JSON) AND a 'chat_message'.
    - If the user just says hello, just provide a 'chat_message'.
    - DO NOT generate mermaid code in this node.
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{user_message}"),
    ])

    chain = prompt | structured_llm
    response = chain.invoke({"user_message": state['user_message']})

    return {"final_response": response.dict()}


def visualizer_node(state: AgentState):
    """Generates ONLY Mermaid Code"""

    # Simple prompt to get just the code
    prompt = f"Create a Mermaid.js MindMap (graph TD) for the topic: {state['user_message']}. Return ONLY the code inside the string. No markdown formatting."

    result = llm.invoke(prompt)
    clean_code = result.content.replace("```mermaid", "").replace("```", "").strip()

    # Return a response object with JUST the mermaid code
    return {
        "final_response": {
            "chat_message": "Here is your visual roadmap.",
            "roadmap": None,
            "mermaid_code": clean_code
        }
    }


#Graph

workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("planner", planner_node)
workflow.add_node("visualizer", visualizer_node)

# Add Conditional Routing
workflow.add_conditional_edges(
    START,
    router_node,
    {
        "planner": "planner",
        "visualizer": "visualizer"
    }
)

workflow.add_edge("planner", END)
workflow.add_edge("visualizer", END)

app = workflow.compile()