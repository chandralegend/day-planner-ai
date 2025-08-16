import nomos as n
from tools import DayPlanner, TaskManager

task_manager = TaskManager()
day_planner = DayPlanner(directory="plans")

config = n.AgentConfig.from_yaml("config.agent.yaml")
agent = n.Agent.from_config(
    config,
    tools=[
        task_manager.add_task,
        task_manager.get_tasks,
        task_manager.update_task,
        task_manager.delete_task,
        day_planner.create_day_plan,
        day_planner.get_today_plan,
        day_planner.update_plan,
    ],
)


def main():
    print("Hello from day-planner-ai!")


if __name__ == "__main__":
    main()
