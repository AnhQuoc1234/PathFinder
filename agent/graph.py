import os
import json
from typing import TypedDict, Any, List
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import CSVLoader
from langchain_community.tools.tavily_search import TavilySearchResults
from opik.integrations.langchain import OpikTracer

from agent.schemas import AgentState
from agent.quiz import generate_quiz

# --- CONFIG ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


# --- RETRIEVER SETUP ---
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


# --- NODES ---

def retrieve_node(state: AgentState):
    """Step 1: Get data from local CSV (if any)"""
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
    """Step 2: Get data from the Web"""
    query = state.get("user_message", "")
    existing_context = state.get("context", "")

    # Skip search if user is just asking for a quiz based on previous context
    if "quiz" in query.lower() or "test" in query.lower():
        return {"context": existing_context}

    try:
        web_results = tavily_tool.invoke(query)
        web_content = "\n".join([r.get("content", "") for r in web_results])
        final_context = f"{existing_context}\n\nWeb Search Info:\n{web_content}"
        return {"context": final_context}
    except Exception:
        return {"context": existing_context}


def generate_node(state: AgentState):
    """Step 3: Generate Answer (Smart Router)"""
    user_message = state.get("user_message", "").lower()
    context = state.get("context", "")

    # --- SCENARIO A: GENERATE QUIZ ---
    if "quiz" in user_message or "test" in user_message or "exam" in user_message:
        print("--- GENERATING QUIZ ---")

        # 1. Generate the Quiz Object
        quiz_obj = generate_quiz(topic="Learning Plan", context=context)

        if quiz_obj:
            # 2. Return as JSON string wrapped in markdown for the Frontend to parse
            # We use json.dumps to ensure it is valid JSON text
            json_output = json.dumps(quiz_obj.dict())
            return {
                "messages": [
                    {"role": "assistant", "content": f"```json\n{json_output}\n```"}
                ]
            }
        else:
            return {
                "messages": [
                    {"role": "assistant", "content": "I couldn't generate a quiz for this topic. Please try again."}
                ]
            }

    # --- SCENARIO B: VISUAL DIAGRAM (Only if explicitly asked) ---
    if "diagram" in user_message or "visual" in user_message or "mermaid" in user_message:
        prompt = f"""
        User wants a visual diagram for: "{user_message}"
        Context: {context}

        TASK: Output ONLY a Mermaid.js code block (graph TD or mindmap).
        Do not write any other text.
        """
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.0)
        response = llm.invoke(prompt)
        return {"messages": [response]}

    # --- SCENARIO C: TEXT ROADMAP (Default) ---
    # (Removed all Mermaid instructions as requested)
    prompt = f"""
    You are PathFinder, an expert curriculum designer.

    USER REQUEST: "{user_message}"
    CONTEXT: {context}

    YOUR TASK:
    Create a detailed, step-by-step learning path (e.g., Week 1, Week 2).
    - Use clear Markdown (Bold headers, bullet points).
    - Tone: Professional, encouraging, and direct.
    - If the user asks a general question, answer it clearly based on the context.
    - NEGATIVE CONSTRAINT: DO NOT generate any quizzes or exams here.
    - NEGATIVE CONSTRAINT: DO NOT generate any Mermaid diagrams or code blocks.

    End your response by suggesting: "Would you like me to generate a **visual roadmap** or a **practice quiz** for this?"
    """

    opik_tracer = OpikTracer(tags=["PathFinder_Chat"])
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.5)

    response = llm.invoke(prompt, config={"callbacks": [opik_tracer]})

    return {
        "dialogue_state": response.content,
        "messages": [response]
    }


# --- GRAPH BUILD ---
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