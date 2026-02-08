import os
from typing import TypedDict, Any, List
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import CSVLoader
from langchain_community.tools.tavily_search import TavilySearchResults
from opik.integrations.langchain import OpikTracer

from agent.schemas import AgentState

# Config
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


# Retriever
def build_retriever():
    file_path = "knowledge.csv"
    if not os.path.exists(file_path):
        return None
    try:
        loader = CSVLoader(file_path=file_path)
        docs = loader.load()
        if not docs: return None
        embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
        vectorstore = FAISS.from_documents(docs, embeddings)
        return vectorstore.as_retriever(search_kwargs={"k": 2})
    except Exception:
        return None


retriever = build_retriever()
tavily_tool = TavilySearchResults(k=3)


# Define Nodes

def retrieve_node(state: AgentState):
    query = state.get("user_message", "")
    context = ""
    if retriever:
        try:
            results = retriever.invoke(query)
            if results:
                context = "\n\n".join([doc.page_content for doc in results])
        except Exception:
            pass
    return {"context": context}


def web_search_node(state: AgentState):
    query = state.get("user_message", "")
    existing_context = state.get("context", "")
    try:
        web_results = tavily_tool.invoke(query)
        web_content = "\n".join([r.get("content", "") for r in web_results])
        final_context = f"{existing_context}\n\nWeb Search Info:\n{web_content}"
        return {"context": final_context}
    except Exception:
        return {"context": existing_context}


def generate_node(state: AgentState):
    """Step 3: Generate Answer (Strict Roadmap & Graph Only)"""
    query = state.get("user_message", "")
    context = state.get("context", "")

    # Prompt
    prompt = f"""
    You are PathFinder, an expert curriculum designer.

    USER REQUEST: "{query}"
    CONTEXT: {context}

    YOUR TASK:
    You must generate a response in exactly two parts.

    PART 1: THE TEXT ROADMAP
    - Create a detailed, step-by-step learning path (e.g., Week 1, Week 2).
    - Use clear Markdown (Bold headers, bullet points).
    - Tone: Professional, encouraging, and direct.
    - NEGATIVE CONSTRAINT: DO NOT generate any quizzes, exams, or multiple-choice questions.

    PART 2: THE VISUALIZATION
    - Immediately after the text, provide a Mermaid.js code block.
    - The diagram MUST strictly represent the "Weeks" or "Steps" you wrote in Part 1.
    - Syntax: Use `graph TD` (Top-Down) or `mindmap`.
    - NEGATIVE CONSTRAINT: Do NOT explain how to use Mermaid. Do NOT provide generic examples. Just output the code.

    EXAMPLE OUTPUT FORMAT:

    Here is your plan for [Topic]...
    * **Week 1:** Basics...
    * **Week 2:** Advanced...

    ```mermaid
    graph TD
      Start((Start)) --> W1[Week 1: Basics]
      W1 --> T1(Variables)
      W1 --> T2(Loops)
      Start --> W2[Week 2: Advanced]
    ```
    """

    opik_tracer = OpikTracer(tags=["PathFinder_Chat"])

    # Reduced temperature to 0.5 to make it less "imaginative" and more "accurate"
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.5)

    response = llm.invoke(prompt, config={"callbacks": [opik_tracer]})

    return {
        "dialogue_state": response.content,
        "messages": [response]
    }


# Build Graph
workflow = StateGraph(AgentState)
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("web_search", web_search_node)
workflow.add_node("generate", generate_node)

workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "web_search")
workflow.add_edge("web_search", "generate")
workflow.add_edge("generate", END)

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)