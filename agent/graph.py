import os
import asyncio
from typing import Literal

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage

from langgraph.checkpoint.memory import MemorySaver  # Vẫn giữ để backup
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool

from agent.schemas import AgentState
from agent.router import route_question
from agent.planner import create_plan
from agent.adapter import call_llm
from agent.quiz import generate_quiz


# Node Define
def router_node(state: AgentState):
    question = state["messages"][-1].content
    route = route_question(question)
    return {"route": route}


def planner_node(state: AgentState):
    question = state["messages"][-1].content
    plan = create_plan(question)
    return {
        "messages": [SystemMessage(content=f"Here is your learning plan:\n{plan}")],
        "plan": plan
    }


def chat_node(state: AgentState):
    response = call_llm(state)
    return {"messages": [response]}


def quiz_node(state: AgentState):
    # Get plan from state
    plan_content = state.get("plan", "")
    if not plan_content:
        # Get last message from previous conversation
        plan_content = state["messages"][-1].content

    quiz = generate_quiz(plan_content)
    return {
        "messages": [SystemMessage(content=f"Here is a quiz to test your knowledge:\n{quiz}")],
    }


# Build Graph
workflow = StateGraph(AgentState)

workflow.add_node("router", router_node)
workflow.add_node("planner", planner_node)
workflow.add_node("chat", chat_node)
workflow.add_node("quiz", quiz_node)

workflow.set_entry_point("router")

workflow.add_conditional_edges(
    "router",
    lambda x: x["route"],
    {
        "plan": "planner",
        "chat": "chat",
        "quiz": "quiz"
    }
)

workflow.add_edge("planner", END)
workflow.add_edge("chat", END)
workflow.add_edge("quiz", END)

# Database

# Connection String
DB_URI = os.getenv("DATABASE_URL")

if DB_URI:
    print("Found DATABASE_URL, connecting to PostgreSQL")

    connection_kwargs = {
        "autocommit": True,
        "prepare_threshold": 0,
    }

    # Connection Pool
    pool = ConnectionPool(
        conninfo=DB_URI,
        max_size=20,
        kwargs=connection_kwargs,
    )

    # Checkpointer with PostgreSQL
    checkpointer = PostgresSaver(pool)

    # auto create table
    checkpointer.setup()

    print("Connected to Supabase PostgreSQL successfully!")
else:
    print("No DATABASE_URL found.")
    checkpointer = MemorySaver()

# Compile Graph
app = workflow.compile(checkpointer=checkpointer)