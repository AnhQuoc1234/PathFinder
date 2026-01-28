import sys
import os
from typing import final

sys.path.append(os.getcwd())

from agent.graph import app

def run_chat_session():
    config = {"configurable": {"thread_id": "user123"}}

    print("Test 1: Create a new plan")
    user_input_1 = "I want to learn Python in 3 days"

    #Test 1: no plan so router will call planner
    app.invoke(
        {"user_message": user_input_1},
        config= config
    )

    #
    state_snapshot = app.get_state(config)
    current_plan = state_snapshot.values.get("current_plan")

    if current_plan:
        print(f"Memory Saved. Goal: {current_plan.get('goal')}")
    else:
        print(f"Memory Failed")
        return

    print("\n Test 2: Complaining (will stop old memory)")
    user_input_2 = "Day 1 is too hard for me, remove complex parts"

    #Test 2: Router will call adapter. Adapter will auto get plan from memory
    final_state = app.invoke(
        {"user_message": user_input_2},
        config= config
    )

    updated_plan = final_state["current_plan"]
    print(f"Updated plan Goal: {updated_plan.get('goal')}")

    #Print topic day 1 to check change or not
    first_topic = updated_plan['schedule'][0]['topic']
    print(f"Changing topic: {first_topic}")

if __name__ == "__main__":
    run_chat_session()
