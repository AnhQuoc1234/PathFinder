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
        # Search web to supplement internal knowledge
        web_results = tavily_tool.invoke(query)
        web_content = "\n".join([r.get("content", "") for r in web_results])
        final_context = f"{existing_context}\n\nWeb Search Info:\n{web_content}"
        return {"context": final_context}
    except Exception:
        return {"context": existing_context}


def generate_node(state: AgentState):
    """Step 3: Generate Answer (Natural Style)"""
    query = state.get("user_message", "")
    context = state.get("context", "")

    # --- UPDATED PROMPT: NATURAL & FRIENDLY ---
    # No more "Part 1 / Part 2" headers.
    prompt = f"""
    You are PathFinder AI, a friendly and expert educational consultant.

    USER QUESTION: "{query}"

    CONTEXT:
    {context}

    INSTRUCTIONS:
    1. Answer the user's request naturally and comprehensively. Use a helpful, encouraging tone.
    2. Structure your text using clean Markdown (headers, bullet points) so it is easy to read.
    3. AT THE VERY END of your response, strictly append a Mermaid diagram code block to visualize the plan.
       - Use `graph TD` or `mindmap`.
       - Do NOT announce it (e.g., avoid saying "Here is the diagram part"). Just put the code block at the bottom.
    """

    # We keep Opik to track errors, but it won't affect the style
    opik_tracer = OpikTracer(tags=["PathFinder_Chat"])

    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)

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