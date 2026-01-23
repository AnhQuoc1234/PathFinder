from agent.adapter import adapt_plan

if __name__ == "__main__":
    #Example plan
    example_plan = {
        "goal": "Learn Python Basics",
        "total_weeks": 2,
        "difficulty": "Intermediate",
        "schedule": [
            {
                "week_number": 1,
                "topic": "Advanced Decorators & Generators",  # Quá khó cho người mới!
                "daily_tasks": ["Study closures", "Build a generator"],
                "resources": ["Expert Python Book"]
            }
        ]
    }

    # User Feedback
    feedback = "I am a total beginner. Week 1 is way too hard! I don't understand what a Decorator is."

    #Adapter Node
    new_plan = adapt_plan(example_plan, feedback)

    #Print Result
    print("\n Here is your new plan:")
    print(f"Old Difficulty: {example_plan['difficulty']}")
    print(f"New Difficulty: {new_plan.difficulty}")

    print(f"New Week 1 Topic: {new_plan.schedule[0].topic}")
