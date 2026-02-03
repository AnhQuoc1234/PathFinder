from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field


# Schema
class LearningResponse(BaseModel):
    content: str = Field(description="Detailed learning content in Markdown format.")
    diagram_code: str = Field(description="Mermaid.js code for a mindmap.")


# Set up LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
structured_llm = llm.with_structured_output(LearningResponse)

system_prompt = """You are an expert tutor.
1. Explain the topic clearly using Markdown (Use ## for headers, * for bullets).
2. Create a MINDMAP code using Mermaid.js syntax to visualize the concepts.

Example of Mermaid syntax:
mindmap
  root((Topic))
    Branch1
      Sub-branch
    Branch2
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("user", "{input}")
])

chain = prompt | structured_llm


def generate_plan(user_input: str):
    try:
        print(f"DEBUG: Generating content for '{user_input}'")
        result = chain.invoke({"input": user_input})

        return {
            "markdown": result.content,
            "mermaid": result.diagram_code
        }
    except Exception as e:
        print(f"Error: {e}")
        return {
            "markdown": "Sorry, I encountered an error.",
            "mermaid": ""
        }