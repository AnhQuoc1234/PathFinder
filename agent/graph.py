import os
import pandas as pd
from typing import TypedDict, Any, List
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import CSVLoader
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.callbacks.base import BaseCallbackHandler

from opik.integrations.langchain import OpikTracer

from agent.schemas import AgentState

#Config
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


# Retriever
def build_retriever():
    """Loads CSV and creates a local vector search engine."""
    file_path = "knowledge.csv"
    if not os.path.exists(file_path):
        print("Warning: knowledge.csv not found.")
        return None

    try:
        loader = CSVLoader(file_path=file_path)
        docs = loader.load()
        if not docs: return None

        embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
        vectorstore = FAISS.from_documents(docs, embeddings)
        return vectorstore.as_retriever(search_kwargs={"k": 2})
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return None


retriever = build_retriever()
tavily_tool = TavilySearchResults(k=3)


# Define Nodes

def retrieve_node(state: AgentState):
    """Step 1: Check CSV Knowledge Base"""
    query = state.get("user_message", "")  # Dùng .get để an toàn hơn
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
    """Step 2: Check Web (Tavily)"""
    query = state.get("user_message", "")
    existing_context = state.get("context", "")

    try:
        web_results = tavily_tool.invoke(query)
        web_content = "\n".join([r.get("content", "") for r in web_results])

        final_context = f"INTERNAL KNOWLEDGE (CSV):\n{existing_context}\n\nWEB SEARCH:\n{web_content}"
        return {"context": final_context}
    except Exception:
        return {"context": existing_context}


def generate_node(state: AgentState):
    """Step 3: Generate Answer (Traced by Opik)"""
    query = state.get("user_message", "")
    context = state.get("context", "")

    prompt = f"""
    You are PathFinder AI. Answer the user based on the context provided.

    CONTEXT:
    {context}

    USER QUESTION: {query}
    """

    # Initialize Opik Tracer
    opik_tracer = OpikTracer(tags=["PathFinder_Agent"])

    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)

    # Invoke LLM with the Opik callback to log the trace
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