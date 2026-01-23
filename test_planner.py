from agent.planner import generate_plan
import json

if __name__ == "__main__":
    # Test Request
    goal = "I want to learn Data Science from scratch"
    duration = "2 weeks"  # Short duration to test logic

    roadmap = generate_plan(goal, duration)

    # Print result
    print("\n Plan Generating")
    print(f"Topic: {roadmap.goal}")
    print(f"Difficulty: {roadmap.difficulty}")

    # Print the first week
    first_week = roadmap.schedule[0]
    print(f"Week 1: {first_week.topic}")
    for task in first_week.daily_tasks:
        print(f" - {task}")

    print("\n Checking OPIK Dashboard")