from typing import TypedDict, Annotated, Literal

from agent.router import route_user_request
from agent.planner import generate_plan
from agent.adapter import adapt_plan
from agent.schemas import LearningRoadmap

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver


#Define State
class AgentState(TypedDict):
    user_message: str
    current_plan: dict | None
    dialogue_state: str

#Nodes. Each node receive State -> Working -> Return new State
def router_node(state: AgentState):
        """Read User Message to make decision."""
        decision = route_user_request(state["user_message"])
        print(f" Router decided: {decision}")
        return {"dialogue_state": decision}

def planner_node(state: AgentState):
    """Create a new Plan"""
    print("New Plan is generating")

    roadmap = generate_plan(state["user_message"])

    return {"current_plan": roadmap.dict()}

def adapter_node(state: AgentState):
    """Node for change old plan"""
    print("New plan is adapting")
    current_plan = state.get("current_plan")
    user_feedback = state.get("user_message")

    if not current_plan:
        print("No plan found. Switching to planner")
        return planner_node(state)

    new_roadmap = adapt_plan(current_plan, state["user_message"])
    return{"current_plan": new_roadmap.dict()}

#Build Graph
workflow = StateGraph(AgentState)

#Adding Nodes
workflow.add_node("router", router_node)
workflow.add_node("planner", planner_node)
workflow.add_node("adapter", adapter_node)

#Entry Point
workflow.set_entry_point("router")

#Adding Edges
def decide_next_step(state: AgentState) -> Literal["planner", "adapter"]:
    if state["dialogue_state"] == "generate_plan":
        return "planner"
    else:
        return "adapter"

workflow.add_conditional_edges(
    "router",
    decide_next_step
)

# Planner and adapter -> End
workflow.add_edge("planner", END)
workflow.add_edge("adapter", END)

# Using Memory Saver
memory = MemorySaver()

app = workflow.compile(checkpointer=memory)