import os
from dotenv import load_dotenv
load_dotenv()

from opik import Opik, track
from opik.evaluation import evaluate
from opik.evaluation.metrics import LevenshteinRatio
from agent.graph import app

# Config
os.environ["OPIK_PROJECT_NAME"] = "PathFinder"

# Opik
client = Opik()

# Get dataset
dataset = client.get_dataset(name="PathFinder")


# Task
@track
def evaluation_task(item):
    # 'topic'
    user_input = item.get("topic")

    # Call Agent
    print(f"Testing: {user_input}")
    try:
        # Get Graph
        result = app.invoke(
            {"user_message": user_input},
            config={"configurable": {"thread_id": "eval_run"}}
        )

        # Get answer
        agent_answer = result.get("dialogue_state", "")
        return {
            "output": agent_answer,
            "reference": item.get("content")  # Cột content trong dataset làm đáp án mẫu
        }
    except Exception as e:
        print(f"Error: {e}")
        return {"output": "Error"}


# Experiment
print("Running")

evaluate(
    dataset=dataset,
    task=evaluation_task,
    experiment_name="Test_RAG_Logic_v1",
    scoring_metrics=[LevenshteinRatio()]
)

print("Done.Please go to dashboard and check  results")