from __future__ import annotations
from typing import Optional
from datetime import datetime, date, timedelta
from enum import Enum
from sqlmodel import SQLModel, Field


class TaskStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class TaskPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Task(SQLModel, table=True):
    """
    Represents a user task managed by the AI Agent.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True, description="Short summary of the task")
    description: Optional[str] = Field(
        default=None, description="Optional task details"
    )

    status: TaskStatus = Field(
        default=TaskStatus.pending, description="Current state of the task"
    )
    priority: TaskPriority = Field(
        default=TaskPriority.medium, description="Task priority level"
    )

    due_date: Optional[date] = Field(default=None, description="Optional due date")
    created_at: datetime = Field(default_factory=datetime.now, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.now, nullable=False)

    # Helper methods
    def mark_complete(self):
        self.status = TaskStatus.completed
        self.updated_at = datetime.now()

    def update_task(self, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self, k) and v is not None:
                setattr(self, k, v)
        self.updated_at = datetime.now()


# -------------------------------------------------------------------
# SAMPLE DATA
# -------------------------------------------------------------------


def get_sample_tasks() -> list[dict]:
    """
    Returns a list of sample task data dictionaries.
    Can be used to seed the database with example tasks.

    Returns:
        List of dictionaries containing task data
    """
    today = date.today()

    return [
        {
            "title": "Complete quarterly report",
            "description": "Compile financial data and write the Q4 quarterly report for stakeholders",
            "status": TaskStatus.in_progress,
            "priority": TaskPriority.high,
            "due_date": today + timedelta(days=3),
        },
        {
            "title": "Review team proposals",
            "description": "Review and provide feedback on the three project proposals submitted by the team",
            "status": TaskStatus.pending,
            "priority": TaskPriority.medium,
            "due_date": today + timedelta(days=7),
        },
        {
            "title": "Schedule client meeting",
            "description": "Coordinate with client to schedule next quarter planning meeting",
            "status": TaskStatus.pending,
            "priority": TaskPriority.high,
            "due_date": today + timedelta(days=5),
        },
        {
            "title": "Update documentation",
            "description": "Update API documentation with new endpoints and examples",
            "status": TaskStatus.pending,
            "priority": TaskPriority.low,
            "due_date": today + timedelta(days=14),
        },
        {
            "title": "Prepare presentation slides",
            "description": "Create presentation slides for the upcoming conference",
            "status": TaskStatus.in_progress,
            "priority": TaskPriority.medium,
            "due_date": today + timedelta(days=10),
        },
        {
            "title": "Code review PR #123",
            "description": "Review the pull request #123 for the authentication module",
            "status": TaskStatus.completed,
            "priority": TaskPriority.high,
            "due_date": today - timedelta(days=1),
        },
        {
            "title": "Organize team lunch",
            "description": "Plan and organize monthly team lunch event",
            "status": TaskStatus.pending,
            "priority": TaskPriority.low,
            "due_date": today + timedelta(days=21),
        },
    ]


def create_sample_tasks():
    """
    Creates sample tasks in the database.
    Uses TaskService to properly create tasks with all validations.

    Note: Import this function in your scripts/notebooks and call after init_db()
    Example:
        from milo.shared.database import init_db
        from milo.tasks.models import create_sample_tasks

        init_db()
        create_sample_tasks()
    """
    import logging
    import traceback
    from milo.tasks.service import TaskService

    try:
        service = TaskService()
        sample_data = get_sample_tasks()

        created_count = 0
        for task_data in sample_data:
            try:
                # Convert enum to string for service method
                priority_str = task_data["priority"].value
                due_date_str = (
                    task_data["due_date"].isoformat() if task_data["due_date"] else None
                )

                task = service.create_task(
                    title=task_data["title"],
                    description=task_data["description"],
                    priority=priority_str,
                    due_date=due_date_str,
                )

                # Update status if not pending (service defaults to pending)
                if task_data["status"] != TaskStatus.pending:
                    status_str = task_data["status"].value
                    service.update_task(task.id, status=status_str)

                created_count += 1
                logging.info(f"Created sample task: {task.title} (id: {task.id})")
            except Exception as e:
                logging.error(
                    f"Failed to create task '{task_data['title']}': {e}\n{traceback.format_exc()}"
                )

        logging.info(f"Successfully created {created_count} sample tasks")
        return created_count
    except Exception as e:
        logging.error(f"Error creating sample tasks: {e}\n{traceback.format_exc()}")
        raise
