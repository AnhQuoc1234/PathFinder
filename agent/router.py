import os
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import opik


#Define Base Model
class RouteDecision(BaseModel):
    decision: str = Field(
        description="Select 'generate_plan' if user wants a new plan. Select 'update_progress' if user is talking about current progress/struggles.",
        enum=["generate_plan", "update_progress"]
    )


#Initial LLM
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
structured_llm = llm.with_structured_output(RouteDecision)


@opik.track(name="Router Node")
def route_user_request(user_message: str):
    """
    User Behaviour:.
    """
    system_prompt = """
    You are the Router for a Learning Agent.
    Classify the user's intent based on their message.

    Examples:
    - "I want to learn Java" -> generate_plan
    - "Teach me cooking" -> generate_plan
    - "I finished week 1" -> update_progress
    - "This is too hard" -> update_progress
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{message}")
    ])

    chain = prompt | structured_llm
    result = chain.invoke({"message": user_message})

    return result.decision