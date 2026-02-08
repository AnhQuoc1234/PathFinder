# PathFinder AI Backend 

This is the backend API for the PathFinder AI Agent. It utilizes **FastAPI** for the web server and **LangGraph** (built on LangChain) to orchestrate stateful AI workflows, web search, and memory.

## Tech Stack

- Core:** Python 3.9+
- API:** FastAPI, Uvicorn
- AI Orchestration:LangChain, LangGraph
- LLM Provider:OpenAI (GPT-4o/Mini)
- Vector Store: FAISS (CPU)
- Tools: Tavily (Web Search), Pandas (Data Processing)
- bservability:Opik

## ⚙Installation

    1.Clone the repository:
   ``` bash
   git clone https://github.com/AnhQuoc1234/PathFinder#
   cd PathFinder

   2. Create a virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   3. Install dependencies:
       pip install -r requirements.txt

   4. Configuration
       # Core Keys
       OPENAI_API_KEY=sk-...
       TAVILY_API_KEY=tvly-...

       # Opik (Optional - for tracing/logging)
       OPIK_API_KEY=...
       OPIK_WORKSPACE=...
 
    5. Running the Server
        uvicorn main:app --reload

    6. API Documentation
        Swagger UI: http://localhost:8000/docs
        ReDoc: http://localhost:8000/redoc
