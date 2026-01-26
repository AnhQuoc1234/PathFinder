from agent.graph import app
import json

def run_test(user_input, existing_plan=None):
    print(f"\n Users says: {user_input}")

    #Initial State
    initial_state = {
        "user_message": user_input,
        "current_plan": existing_plan,
        "dialogue_status": ""
    }

    #Run Graph
    final_state = app.invoke(initial_state)

    #Get Result
    plan = final_state.get["current_plan"]
    if plan:
        print(f"Result: Plan Goal = '{plan.get('goal')}'")
        print(f"First Topic = '{plan['schedule'][0]['topic']}'")
    else:
        print(f"No Plan is generated")
    return plan

if __name__ == "__main__":
    #Test Case 1
    print("Test Case1: New User")
    plan_v1 = run_test("I want to learn Docker in 1 Week")

    #Test Case 2
    print(f"Test Case 2: Complaining User")
    run_test("Week 1 is too hard, I don't know Linux", existing_plan=plan_v1)
