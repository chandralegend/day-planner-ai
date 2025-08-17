"""
Task Manager module for managing daily tasks.

This module provides a simple and clean interface for creating, updating,
deleting, and filtering tasks.
"""

import json
import os
import uuid
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class Task(BaseModel):
    """Represents a single task with all its attributes."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: Literal["pending", "in_progress", "completed"] = Field(default="pending")
    priority: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Priority level from 1 (lowest) to 5 (highest)",
    )
    estimate_hours: Optional[float] = Field(
        None, gt=0, description="Estimated time in hours"
    )
    due_date: Optional[str] = Field(None, description="Due date in YYYY-MM-DD format")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def mark_completed(self) -> None:
        """Mark task as completed and update timestamp."""
        self.status = "completed"
        self.updated_at = datetime.now()

    def mark_in_progress(self) -> None:
        """Mark task as in progress and update timestamp."""
        self.status = "in_progress"
        self.updated_at = datetime.now()


class TaskFilter(BaseModel):
    """Filter criteria for querying tasks."""

    status: Optional[List[Literal["pending", "in_progress", "completed"]]] = None
    min_priority: Optional[int] = Field(None, ge=1, le=5)
    max_priority: Optional[int] = Field(None, ge=1, le=5)
    has_due_date: Optional[bool] = None


class TaskUpdate(BaseModel):
    """Model for updating task attributes."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[Literal["pending", "in_progress", "completed"]] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    estimate_hours: Optional[float] = Field(None, gt=0)
    due_date: Optional[str] = None


class TaskManager:
    """Manages tasks with persistent storage."""

    def __init__(self, file_path: str = "tasks.json"):
        """Initialize task manager with file storage."""
        self.file_path = file_path
        self.tasks: List[Task] = []
        self._load_tasks()

    def _load_tasks(self) -> None:
        """Load tasks from file."""
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, "r", encoding="utf-8") as f:
                    tasks_data = json.load(f)
                    self.tasks = [Task(**task) for task in tasks_data]
            else:
                self._save_tasks()  # Create empty file
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading tasks: {e}. Starting with empty task list.")
            self.tasks = []

    def _save_tasks(self) -> None:
        """Save tasks to file."""
        try:
            os.makedirs(os.path.dirname(self.file_path) or ".", exist_ok=True)
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(
                    [task.model_dump(mode="json") for task in self.tasks],
                    f,
                    indent=2,
                    default=str,
                )
        except OSError as e:
            print(f"Error saving tasks: {e}")

    def create_task(
        self,
        title: str,
        description: Optional[str] = None,
        priority: int = 3,
        estimate_hours: Optional[float] = None,
        due_date: Optional[str] = None,
    ) -> Task:
        """Create a new task."""
        task = Task(
            title=title,
            description=description,
            priority=priority,
            estimate_hours=estimate_hours,
            due_date=due_date,
        )
        self.tasks.append(task)
        self._save_tasks()
        return task

    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """Get a task by its ID."""
        return next((task for task in self.tasks if task.id == task_id), None)

    def get_tasks(self, filter_criteria: Optional[TaskFilter] = None) -> List[Task]:
        """Get tasks with optional filtering."""
        filtered_tasks = self.tasks.copy()

        if filter_criteria:
            if filter_criteria.status:
                filtered_tasks = [
                    task
                    for task in filtered_tasks
                    if task.status in filter_criteria.status
                ]

            if filter_criteria.min_priority is not None:
                filtered_tasks = [
                    task
                    for task in filtered_tasks
                    if task.priority >= filter_criteria.min_priority
                ]

            if filter_criteria.max_priority is not None:
                filtered_tasks = [
                    task
                    for task in filtered_tasks
                    if task.priority <= filter_criteria.max_priority
                ]

            if filter_criteria.has_due_date is not None:
                if filter_criteria.has_due_date:
                    filtered_tasks = [
                        task for task in filtered_tasks if task.due_date is not None
                    ]
                else:
                    filtered_tasks = [
                        task for task in filtered_tasks if task.due_date is None
                    ]

        return sorted(
            filtered_tasks, key=lambda x: (x.priority, x.created_at), reverse=True
        )

    def update_task(self, task_id: str, updates: TaskUpdate) -> Task:
        """Update an existing task."""
        task = self.get_task_by_id(task_id)
        if not task:
            raise ValueError(f"Task with ID {task_id} not found")

        # Update fields if provided
        update_data = updates.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)

        task.updated_at = datetime.now()
        self._save_tasks()
        return task

    def delete_task(self, task_id: str) -> bool:
        """Delete a task by ID. Returns True if deleted, False if not found."""
        original_count = len(self.tasks)
        self.tasks = [task for task in self.tasks if task.id != task_id]

        if len(self.tasks) < original_count:
            self._save_tasks()
            return True
        return False

    def get_task_summary(self) -> dict:
        """Get a summary of all tasks."""
        total = len(self.tasks)
        pending = len([t for t in self.tasks if t.status == "pending"])
        in_progress = len([t for t in self.tasks if t.status == "in_progress"])
        completed = len([t for t in self.tasks if t.status == "completed"])

        return {
            "total": total,
            "pending": pending,
            "in_progress": in_progress,
            "completed": completed,
            "completion_rate": round((completed / total * 100) if total > 0 else 0, 1),
        }
