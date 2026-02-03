import os
import sys
import json
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

from opik import Opik
from opik.evaluation import evaluate
from langchain_openai import ChatOpenAI

try:
    from opik.evaluation.metrics import BaseMetric, ScoreResult
except ImportError:
    try:
        from opik.evaluation import ScoreResult
        from opik.evaluation.metrics import BaseMetric
    except ImportError:
        from opik.evaluation.metrics import BaseMetric


        class ScoreResult:
            def __init__(self, value, reason=None):
                self.value = value
                self.reason = reason

# Set up env
sys.path.append(os.getcwd())

# Import Agent
try:
    from agent.graph import app as agent_app

    print("Agent loaded successfully.")
except ImportError:
    print("Agent not found. Chạy script từ thư mục gốc của project.")
    sys.exit(1)

# Init grading model
judge_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


# Define metrics for grading
class JsonStructureMetric(BaseMetric):
    def __init__(self):
        super().__init__(name="JSON Structure Check")

    def score(self, input: str, output: dict, **kwargs) -> ScoreResult:
        try:
            plan = output.get("current_plan")
            if not plan:
                return ScoreResult(value=0.0, reason="No plan found")

            required_keys = ["topic", "schedule", "difficulty"]
            for key in required_keys:
                if key not in plan:
                    return ScoreResult(value=0.5, reason=f"Missing key: {key}")
            return ScoreResult(value=1.0, reason="Valid JSON")
        except:
            return ScoreResult(value=0.0, reason="Error parsing output")


class PlanQualityMetric(BaseMetric):
    def __init__(self):
        super().__init__(name="Plan Quality")

    def score(self, input: str, output: dict, **kwargs) -> ScoreResult:
        user_msg = input if isinstance(input, str) else str(input)
        plan = output.get("current_plan")
        if not plan: return ScoreResult(value=0.0, reason="No plan")

        prompt = f"""
        Rate this learning plan from 0.0 to 1.0.
        User: "{user_msg}"
        Plan: {json.dumps(plan)}
        Return ONLY the number.
        """
        try:
            res = judge_llm.invoke(prompt).content.strip()
            return ScoreResult(value=float(res), reason="AI Judge")
        except:
            return ScoreResult(value=0.5, reason="Error")


# Raw Data(List)
raw_data = [
    {"input": "Learn Python in 2 weeks", "expected_topic": "Python"},
    {"input": "Study plan for ReactJS", "expected_topic": "ReactJS"},
    {"input": "How to cook Beef Pho", "expected_topic": "Cooking"},
    {"input": "English communication plan", "expected_topic": "English"}
]


# Agent Func
def run_agent(item):
    msg = item["input"]
    inputs = {"user_message": msg, "current_plan": None, "dialogue_state": "start"}

    # Randomly Thread Id
    import uuid
    config = {"configurable": {"thread_id": f"eval_{uuid.uuid4()}"}}

    res = agent_app.invoke(inputs, config=config)
    return {
        "output": {
            "current_plan": res.get("current_plan"),
            "dialogue_state": res.get("dialogue_state")
    }
}

# MAIN EXECUTION
if __name__ == "__main__":
    print("Initializing Opik")

    client = Opik()

    # Create Dataset on Opik
    dataset_name = "PathFinder_Dataset"
    dataset = client.get_or_create_dataset(name=dataset_name)

    # Push input to dataset
    dataset.insert(raw_data)
    print(f"Dataset '{dataset_name}' ready with {len(raw_data)} items.")

    print("Running Evaluation")

    evaluate(
        dataset=dataset,
        task=run_agent,
        scoring_metrics=[JsonStructureMetric(), PlanQualityMetric()],
        experiment_name="PathFinder_Run_Final",
        project_name="PathFinder"
    )

    print("Done! Go to Opik Dashboard to see results.")