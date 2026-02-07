import os
import sys
import json
import warnings
import uuid

# Set up envi and gpt api
try:
    from dotenv import load_dotenv

    load_dotenv()
    print("Success add api from .env")
except ImportError:
    print("Please download dotenv")

warnings.filterwarnings("ignore", category=UserWarning)

# import opik and score result
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
            def __init__(self, value, reason=None, name=None):
                self.value = value
                self.reason = reason
                self.name = name
                self.scoring_failed = False

            # Path
sys.path.append(os.getcwd())

# Import Agent
try:
    from agent.graph import app as agent_app

    print("Agent loaded successfully.")
except ImportError:
    print("Agent not found.")
    sys.exit(1)

# Init Model
try:
    judge_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
except Exception as e:
    print(f"Init Error: {e}")
    sys.exit(1)


# Define Metrics
class JsonStructureMetric(BaseMetric):
    def __init__(self):
        super().__init__(name="JSON Structure Check")

    def score(self, input: str, output: dict, **kwargs) -> ScoreResult:
        try:
            plan = output.get("current_plan")
            if not plan:
                return ScoreResult(value=0.0, reason="No plan found", name=self.name)

            required_keys = ["topic", "difficulty", "schedule"]
            if all(k in plan for k in required_keys):
                return ScoreResult(value=1.0, reason="Valid JSON", name=self.name)
            return ScoreResult(value=0.5, reason="Missing keys", name=self.name)
        except:
            return ScoreResult(value=0.0, reason="Parse Error", name=self.name)


class PlanQualityMetric(BaseMetric):
    def __init__(self):
        super().__init__(name="Plan Quality")

    def score(self, input: str, output: dict, **kwargs) -> ScoreResult:
        user_msg = input if isinstance(input, str) else str(input)
        plan = output.get("current_plan")
        if not plan:
            return ScoreResult(value=0.0, reason="No plan", name=self.name)

        prompt = f"""
        Rate this plan (0.0 - 1.0).
        User: "{user_msg}"
        Plan: {json.dumps(plan, ensure_ascii=False)}
        Return ONLY number.
        """
        try:
            res = judge_llm.invoke(prompt).content.strip()
            import re
            match = re.search(r"0\.\d+|1\.0|0|1", res)
            val = float(match.group()) if match else 0.5
            return ScoreResult(value=val, reason="AI Judge", name=self.name)
        except:
            return ScoreResult(value=0.5, reason="Eval Error", name=self.name)


# Evaluation
raw_data = [
    {"input": "Learn Python in 2 weeks", "expected_topic": "Python"},
    {"input": "Study plan for ReactJS", "expected_topic": "ReactJS"},
    {"input": "How to cook Beef Pho", "expected_topic": "Cooking"},
    {"input": "English communication plan", "expected_topic": "English"}
]


def run_agent(item):
    msg = item["input"]
    inputs = {"user_message": msg, "current_plan": None, "dialogue_state": "start"}
    config = {"configurable": {"thread_id": f"eval_{uuid.uuid4()}"}}

    # Run Agent
    res = agent_app.invoke(inputs, config=config)

    # Return output for Opik
    return {
        "output": {
            "current_plan": res.get("current_plan"),
            "dialogue_state": res.get("dialogue_state")
        }
    }


if __name__ == "__main__":
    print("Initializing Opik")
    client = Opik()

    dataset_name = "PathFinder_Eval_Dataset"
    dataset = client.get_or_create_dataset(name=dataset_name)

    # Insert dat
    try:
        if dataset.get_item_count() == 0:
            dataset.insert(raw_data)
    except:
        dataset.insert(raw_data)

    print(f"Running Evaluation on '{dataset_name}'...")

    evaluate(
        dataset=dataset,
        task=run_agent,
        scoring_metrics=[JsonStructureMetric(), PlanQualityMetric()],
        experiment_name="PathFinder_Success_Run",
        project_name="PathFinder"
    )
    print("\n Success!")
