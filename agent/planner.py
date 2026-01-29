import os
from dotenv import load_dotenv

load_dotenv()
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from agent.schemas import LearningRoadmap
#import opik

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)
structured_llm = llm.with_structured_output(LearningRoadmap)


#@opik.track(name="Planner Logic")
def generate_plan(user_input: str):
    """
    Generate a rich learning plan with Tasks and Resources.
    """

    system_prompt = """
    You are an expert Education Planner.

    Your task:
    1. Analyze the USER REQUEST to identify the TOPIC and DURATION.
    2. If duration is not specified, default to 2 weeks.
    3. Determine the DIFFICULTY level (Beginner/Intermediate/Advanced).

    IMPORTANT REQUIREMENTS:
    - You MUST fill 'daily_tasks' with 3-5 specific bullet points.
    - You MUST provide 'resources' (keywords for search).
    - Respect the 'total_weeks' strictly based on user input.
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "User Request: {input}")
    ])

    chain = prompt | structured_llm

    print(f"Generating rich plan for: {user_input}")
    # Call chain
    result = chain.invoke({"input": user_input})

    return result