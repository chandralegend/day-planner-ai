import os
import json
from typing import List, Literal, Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime


class UpdateTask(BaseModel):
    id: str
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[Literal["pending", "in_progress", "completed"]] = None
    priority: Optional[int] = Field(
        None, ge=1, le=5, description="Priority level from 1 to 5"
    )
    estimate: Optional[float] = Field(
        None, description="Estimated time to complete the task in hours"
    )
    due_date: Optional[str] = Field(None, description="ISO 8601 format (YYYY-MM-DD)")


class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    status: Literal["pending", "in_progress", "completed"] = Field(default="pending")
    priority: int = Field(default=1, ge=1, le=5)
    estimate: Optional[float] = Field(
        None, description="Estimated time to complete the task in hours"
    )
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    due_date: Optional[str] = Field(None, description="ISO 8601 format (YYYY-MM-DD)")

    def update(self, task: UpdateTask):
        self.title = task.title or self.title
        self.description = task.description or self.description
        self.status = task.status or self.status
        self.priority = task.priority or self.priority
        self.due_date = task.due_date or self.due_date
        self.updated_at = datetime.now()


class Filter(BaseModel):
    status: List[Literal["pending", "in_progress", "completed"]] = Field(
        ["in_progress", "pending"]
    )
    min_priority: Optional[int] = Field(None, ge=1, le=5)
    max_priority: Optional[int] = Field(None, ge=1, le=5)


class TaskManager:
    def __init__(self, file_path: str = "tasks.json"):
        self.file_path = file_path
        self.tasks = []
        self.load_tasks()

    def load_tasks(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, "r") as f:
                tasks_data = json.load(f)
                self.tasks = [Task(**task) for task in tasks_data]
        else:
            with open(self.file_path, "w") as f:
                json.dump([], f)

    def save_tasks(self):
        with open(self.file_path, "w") as f:
            json.dump([task.model_dump(mode="json") for task in self.tasks], f)

    def add_task(self, task: Task):
        self.tasks.append(task)
        self.save_tasks()

    def get_tasks(self, filter: Filter) -> list[Task]:
        filtered_tasks = self.tasks
        if filter.status:
            filtered_tasks = [
                task for task in filtered_tasks if task.status == filter.status
            ]
        if filter.min_priority:
            filtered_tasks = [
                task for task in filtered_tasks if task.priority >= filter.min_priority
            ]
        if filter.max_priority:
            filtered_tasks = [
                task for task in filtered_tasks if task.priority <= filter.max_priority
            ]
        return filtered_tasks

    def update_task(self, updates: UpdateTask):
        for i, existing_task in enumerate(self.tasks):
            if existing_task.id == updates.id:
                self.tasks[i].update(updates)
                self.save_tasks()
                return
        raise ValueError("Task not found")

    def delete_task(self, task_id: str):
        self.tasks = [task for task in self.tasks if task.id != task_id]
        self.save_tasks()
