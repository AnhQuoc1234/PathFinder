import os
from typing import TypedDict, Optional, List, Any
from langgraph.graph import StateGraph, END, START
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from agent.schemas import AgentResponse

load_dotenv()


class AgentState(TypedDict):
    messages: List[Any]
    user_message: str
    final_response: Optional[dict]


llm = ChatOpenAI(model="gpt-4o", temperature=0)


def planner_node(state: AgentState):
    structured_llm = llm.with_structured_output(AgentResponse)

    system_prompt = """
    You are PathFinder, an expert curriculum designer.
    - If the user asks to learn a skill, generate a structured 'roadmap' and a friendly 'chat_message'.
    - If the user just says hello, just provide a 'chat_message'.
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{user_message}"),
    ])

    chain = prompt | structured_llm
    response = chain.invoke({"user_message": state['user_message']})

    return {"final_response": response.dict()}


workflow = StateGraph(AgentState)
workflow.add_node("planner", planner_node)
workflow.add_edge(START, "planner")
workflow.add_edge("planner", END)

app = workflow.compile()