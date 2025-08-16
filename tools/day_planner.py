from tools.task_manager import Task
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import os
import json
import uuid


class DayPlan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: datetime
    tasks: dict[str, Task] = Field(default_factory=dict)


class DayPlanner:
    def __init__(self, directory: str):
        self.directory = directory
        self.plans: list[DayPlan] = []

    def load_plans(self):
        for filename in os.listdir(self.directory):
            if filename.endswith(".json"):
                with open(os.path.join(self.directory, filename), "r") as f:
                    plan_data = json.load(f)
                    self.plans.append(DayPlan(**plan_data))

    def create_day_plan(self, tasks: dict[str, Task]):
        new_plan = DayPlan(date=datetime.now(), tasks=tasks)
        self.plans.append(new_plan)
        self.save_plan(new_plan)

    def save_plan(self, plan: DayPlan):
        with open(os.path.join(self.directory, f"{plan.id}.json"), "w") as f:
            json.dump(plan.model_dump(mode="json"), f, default=str)

    def get_today_plan(self) -> DayPlan:
        today = datetime.now().date()
        for plan in self.plans:
            if plan.date.date() == today:
                return plan
        raise ValueError("Plan not found for today")

    def get_plans(self, last_n_days: int) -> list[DayPlan]:
        cutoff_date = datetime.now() - timedelta(days=last_n_days)
        return [plan for plan in self.plans if plan.date >= cutoff_date]

    def get_all_plans(self) -> list[tuple[str, str]]:
        return [(plan.id, plan.date.isoformat()) for plan in self.plans]

    def get_plan_by_id(self, plan_id: str) -> DayPlan:
        for plan in self.plans:
            if plan.id == plan_id:
                return plan
        raise ValueError("Plan not found")

    def update_plan(self, plan_id: str, tasks: dict[str, Task]):
        for plan in self.plans:
            if plan.id == plan_id:
                plan.tasks = tasks
                self.save_plan(plan)
                return
        raise ValueError("Plan not found")
