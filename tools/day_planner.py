"""
Day Planner module for managing today's tasks and schedule.

This module provides a simple interface for planning the current day
by organizing tasks into time slots and tracking progress.
"""

import json
import os
from datetime import datetime, date
from typing import List, Optional, Dict

from pydantic import BaseModel, Field

from tools.task_manager import Task, TaskManager


class TimeSlot(BaseModel):
    """Represents a time slot in the day plan."""

    start_time: str = Field(..., description="Start time in HH:MM format")
    end_time: str = Field(..., description="End time in HH:MM format")
    task_id: Optional[str] = None
    notes: Optional[str] = None


class DayPlan(BaseModel):
    """Represents a complete day plan."""

    date: str = Field(..., description="Date in YYYY-MM-DD format")
    time_slots: List[TimeSlot] = Field(default_factory=list)
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class DayPlanner:
    """Manages daily planning with time slots and task assignments."""

    def __init__(self, task_manager: TaskManager, plans_file: str = "day_plans.json"):
        """Initialize day planner with task manager integration."""
        self.task_manager = task_manager
        self.plans_file = plans_file
        self.plans: Dict[str, DayPlan] = {}
        self._load_plans()

    def _load_plans(self) -> None:
        """Load existing day plans from file."""
        try:
            if os.path.exists(self.plans_file):
                with open(self.plans_file, "r", encoding="utf-8") as f:
                    plans_data = json.load(f)
                    self.plans = {
                        date_str: DayPlan(**plan_data)
                        for date_str, plan_data in plans_data.items()
                    }
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading plans: {e}. Starting with empty plans.")
            self.plans = {}

    def _save_plans(self) -> None:
        """Save day plans to file."""
        try:
            os.makedirs(os.path.dirname(self.plans_file) or ".", exist_ok=True)
            with open(self.plans_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        date_str: plan.model_dump(mode="json")
                        for date_str, plan in self.plans.items()
                    },
                    f,
                    indent=2,
                    default=str,
                )
        except OSError as e:
            print(f"Error saving plans: {e}")

    def get_today_date(self) -> str:
        """Get today's date as a string."""
        return date.today().isoformat()

    def create_today_plan(self, notes: Optional[str] = None) -> DayPlan:
        """Create a new plan for today."""
        today = self.get_today_date()

        plan = DayPlan(date=today, notes=notes)

        self.plans[today] = plan
        self._save_plans()
        return plan

    def get_today_plan(self) -> Optional[DayPlan]:
        """Get today's plan if it exists."""
        today = self.get_today_date()
        return self.plans.get(today)

    def get_or_create_today_plan(self) -> DayPlan:
        """Get today's plan or create one if it doesn't exist."""
        plan = self.get_today_plan()
        if plan is None:
            plan = self.create_today_plan()
        return plan

    def add_time_slot(
        self,
        start_time: str,
        end_time: str,
        task_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> TimeSlot:
        """Add a time slot to today's plan."""
        plan = self.get_or_create_today_plan()

        # Validate task exists if provided
        if task_id and not self.task_manager.get_task_by_id(task_id):
            raise ValueError(f"Task with ID {task_id} not found")

        time_slot = TimeSlot(
            start_time=start_time, end_time=end_time, task_id=task_id, notes=notes
        )

        plan.time_slots.append(time_slot)
        plan.updated_at = datetime.now()
        self._save_plans()
        return time_slot

    def assign_task_to_slot(self, slot_index: int, task_id: str) -> TimeSlot:
        """Assign a task to an existing time slot."""
        plan = self.get_today_plan()
        if not plan:
            raise ValueError("No plan exists for today")

        if slot_index >= len(plan.time_slots):
            raise ValueError("Time slot index out of range")

        # Validate task exists
        if not self.task_manager.get_task_by_id(task_id):
            raise ValueError(f"Task with ID {task_id} not found")

        plan.time_slots[slot_index].task_id = task_id
        plan.updated_at = datetime.now()
        self._save_plans()
        return plan.time_slots[slot_index]

    def remove_time_slot(self, slot_index: int) -> bool:
        """Remove a time slot from today's plan."""
        plan = self.get_today_plan()
        if not plan:
            return False

        if slot_index >= len(plan.time_slots):
            return False

        plan.time_slots.pop(slot_index)
        plan.updated_at = datetime.now()
        self._save_plans()
        return True

    def get_scheduled_tasks(self) -> List[Task]:
        """Get all tasks that are scheduled for today."""
        plan = self.get_today_plan()
        if not plan:
            return []

        scheduled_task_ids = [slot.task_id for slot in plan.time_slots if slot.task_id]

        scheduled_tasks = []
        for task_id in scheduled_task_ids:
            task = self.task_manager.get_task_by_id(task_id)
            if task:
                scheduled_tasks.append(task)

        return scheduled_tasks

    def get_unscheduled_tasks(self) -> List[Task]:
        """Get all tasks that are not scheduled for today."""
        all_tasks = self.task_manager.get_tasks()
        scheduled_task_ids = set(
            slot.task_id
            for slot in (
                self.get_today_plan() or DayPlan(date=self.get_today_date())
            ).time_slots
            if slot.task_id
        )

        return [task for task in all_tasks if task.id not in scheduled_task_ids]

    def get_day_summary(self) -> dict:
        """Get a summary of today's plan."""
        plan = self.get_today_plan()
        if not plan:
            return {
                "date": self.get_today_date(),
                "has_plan": False,
                "total_slots": 0,
                "scheduled_slots": 0,
                "unscheduled_slots": 0,
            }

        total_slots = len(plan.time_slots)
        scheduled_slots = len([slot for slot in plan.time_slots if slot.task_id])

        return {
            "date": plan.date,
            "has_plan": True,
            "total_slots": total_slots,
            "scheduled_slots": scheduled_slots,
            "unscheduled_slots": total_slots - scheduled_slots,
            "notes": plan.notes,
        }
