from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional, Dict, Any
from agent.planner import generate_plan

class AgentState(TypedDict):
    user_message: str
    current_plan: Optional[Dict[str, Any]]
    dialogue_state: str

def router_node(state: AgentState):
    if not state.get("current_plan"):
        return "generate_plan"
    return END

def planner_node(state: AgentState):
    print("Generating Plan...")
    # generate_plan return dict
    roadmap = generate_plan(state["user_message"])
    return {"current_plan": roadmap}

# Build Graph
workflow = StateGraph(AgentState)
workflow.add_node("planner", planner_node)
workflow.set_conditional_entry_point(
    router_node,
    {"generate_plan": "planner", END: END}
)
workflow.add_edge("planner", END)

app = workflow.compile()