import nomos as n
from tools import DayPlanner

config = n.AgentConfig.from_yaml("config.agent.yaml")
agent = n.Agent.from_config(config, tools=[])

def main():
    print("Hello from day-planner-ai!")


if __name__ == "__main__":
    main()
