import nomos as n
from tools import TaskManager, DayPlanner
from dotenv import load_dotenv

task_manager = TaskManager()
day_planner = DayPlanner(task_manager)

tools = [
    # Task Manager Tools
    task_manager.create_task,
    task_manager.get_tasks,
    task_manager.update_task,
    task_manager.delete_task,
    task_manager.get_task_by_id,
    task_manager.get_task_summary,
    # Day Planning Tools
    day_planner.add_time_slot,
    day_planner.get_today_plan,
    day_planner.create_today_plan,
    day_planner.add_time_slot,
    day_planner.assign_task_to_slot,
    day_planner.remove_time_slot,
    day_planner.get_scheduled_tasks,
    day_planner.get_day_summary,
]

if __name__ == "__main__":
    load_dotenv()

    # Create agent
    config = n.AgentConfig.from_yaml("config.agent.yaml")
    agent = n.Agent.from_config(config, tools=tools)
    sess = agent.create_session()

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break
        response = sess.next(user_input)
        print(f"AI: {response.decision.response}")
