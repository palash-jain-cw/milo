from typing import List, Optional
from datetime import datetime, date
import logging
import traceback

from sqlmodel import select

from milo.tasks.models import Task, TaskStatus, TaskPriority
from milo.shared.database import get_session


class TaskService:
    """
    Service layer that manages CRUD operations for tasks.
    Uses the context-managed database session from `get_session()`.
    Each method opens its own short-lived session.
    """

    # -----------------------------
    # CREATE
    # -----------------------------
    @staticmethod
    def create_task(
        title: str,
        description: Optional[str] = None,
        priority: Optional[str] = "medium",
        due_date: Optional[str | date] = None,
    ) -> Task:
        try:
            priority_enum = TaskService._parse_priority(priority)
            due_date_obj = TaskService._parse_due_date(due_date)

            with get_session() as session:
                task = Task(
                    title=title,
                    description=description,
                    priority=priority_enum,
                    due_date=due_date_obj,
                )
                session.add(task)
                session.flush()  # ensures task.id is assigned before commit
                session.refresh(task)
                logging.info("Created task '%s' with id %s", task.title, task.id)
                return task
        except Exception as exc:
            logging.error(
                "Failed to create task '%s': %s\n%s",
                title,
                exc,
                traceback.format_exc(),
            )
            raise

    # -----------------------------
    # READ
    # -----------------------------
    @staticmethod
    def get_task(task_id: int) -> Optional[Task]:
        try:
            with get_session() as session:
                task = session.get(Task, task_id)
                if task:
                    logging.info("Retrieved task with id %s", task_id)
                else:
                    logging.warning("Task with id %s not found", task_id)
                return task
        except Exception as exc:
            logging.error(
                "Failed to retrieve task '%s': %s\n%s",
                task_id,
                exc,
                traceback.format_exc(),
            )
            raise

    @staticmethod
    def list_tasks(
        status: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 50,
    ) -> List[Task]:
        try:
            with get_session() as session:
                query = select(Task)
                if status:
                    status_enum = TaskService._parse_status(status)
                    query = query.where(Task.status == status_enum)
                if priority:
                    priority_enum = TaskService._parse_priority(priority)
                    query = query.where(Task.priority == priority_enum)
                tasks = session.exec(query.limit(limit)).all()
                logging.info("Retrieved %s tasks", len(tasks))
                return tasks
        except Exception as exc:
            logging.error(
                "Failed to list tasks: %s\n%s",
                exc,
                traceback.format_exc(),
            )
            raise

    @staticmethod
    def list_all_tasks() -> List[Task]:
        try:
            with get_session() as session:
                tasks = session.exec(
                    select(Task).order_by(Task.created_at.desc())
                ).all()
                logging.info("Retrieved all tasks count=%s", len(tasks))
                return tasks
        except Exception as exc:
            logging.error(
                "Failed to list all tasks: %s\n%s",
                exc,
                traceback.format_exc(),
            )
            raise

    # -----------------------------
    # UPDATE
    # -----------------------------
    @staticmethod
    def update_task(
        task_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        due_date: Optional[str | date] = None,
    ) -> Optional[Task]:
        try:
            with get_session() as session:
                task = session.get(Task, task_id)
                if not task:
                    logging.warning("Task with id %s not found for update", task_id)
                    return None

                if title:
                    task.title = title
                if description:
                    task.description = description
                if status:
                    task.status = TaskService._parse_status(status)
                if priority:
                    task.priority = TaskService._parse_priority(priority)
                if due_date:
                    task.due_date = TaskService._parse_due_date(due_date)

                task.updated_at = datetime.now()
                session.add(task)
                session.flush()
                session.refresh(task)
                logging.info("Updated task with id %s", task_id)
                return task
        except Exception as exc:
            logging.error(
                "Failed to update task '%s': %s\n%s",
                task_id,
                exc,
                traceback.format_exc(),
            )
            raise

    # -----------------------------
    # DELETE
    # -----------------------------
    @staticmethod
    def delete_task(task_id: int) -> bool:
        try:
            with get_session() as session:
                task = session.get(Task, task_id)
                if not task:
                    logging.warning("Task with id %s not found for deletion", task_id)
                    return False
                session.delete(task)
                logging.info("Deleted task with id %s", task_id)
                return True
        except Exception as exc:
            logging.error(
                "Failed to delete task '%s': %s\n%s",
                task_id,
                exc,
                traceback.format_exc(),
            )
            raise

    # -----------------------------
    # COMPLETE
    # -----------------------------
    @staticmethod
    def mark_complete(task_id: int) -> Optional[Task]:
        try:
            with get_session() as session:
                task = session.get(Task, task_id)
                if not task:
                    logging.warning("Task with id %s not found for completion", task_id)
                    return None
                task.status = TaskStatus.completed
                task.updated_at = datetime.now()
                session.add(task)
                session.flush()
                session.refresh(task)
                logging.info("Marked task %s as completed", task_id)
                return task
        except Exception as exc:
            logging.error(
                "Failed to mark task '%s' as complete: %s\n%s",
                task_id,
                exc,
                traceback.format_exc(),
            )
            raise

    @staticmethod
    def complete_task(task_id: int) -> Optional[Task]:
        """Alias for mark_complete to match tooling expectations."""
        return TaskService.mark_complete(task_id)

    # -----------------------------
    # CLEANUP / UTILITY
    # -----------------------------
    @staticmethod
    def delete_all_tasks():
        try:
            with get_session() as session:
                session.exec("DELETE FROM tasks")
                logging.info("Deleted all tasks")
                return True
        except Exception as exc:
            logging.error(
                "Failed to delete all tasks: %s\n%s",
                exc,
                traceback.format_exc(),
            )
            raise

    # -----------------------------
    # HELPERS
    # -----------------------------

    @staticmethod
    def _parse_status(status: Optional[str | TaskStatus]) -> TaskStatus:
        if isinstance(status, TaskStatus):
            return status
        if status is None:
            return TaskStatus.pending
        try:
            return TaskStatus(status.lower())
        except ValueError as exc:
            logging.error(
                "Invalid status '%s': %s\n%s",
                status,
                exc,
                traceback.format_exc(),
            )
            raise

    @staticmethod
    def _parse_priority(priority: Optional[str | TaskPriority]) -> TaskPriority:
        if isinstance(priority, TaskPriority):
            return priority
        if priority is None:
            return TaskPriority.medium
        try:
            return TaskPriority(priority.lower())
        except ValueError as exc:
            logging.error(
                "Invalid priority '%s': %s\n%s",
                priority,
                exc,
                traceback.format_exc(),
            )
            raise

    @staticmethod
    def _parse_due_date(due_date: Optional[str | date]) -> Optional[date]:
        if due_date is None:
            return None
        if isinstance(due_date, date):
            return due_date
        try:
            return date.fromisoformat(due_date)
        except ValueError as exc:
            logging.error(
                "Invalid due_date '%s': %s\n%s",
                due_date,
                exc,
                traceback.format_exc(),
            )
            raise


# OpenAI function calling schema for task operations
functions = [
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Create a new task in the user's task list.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "The task title."},
                    "description": {
                        "type": "string",
                        "description": "Optional task details.",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Task priority level.",
                    },
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_tasks",
            "description": "List all tasks, optionally filtered by status or priority.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["pending", "in_progress", "completed", "cancelled"],
                        "description": "Filter tasks by status.",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Filter tasks by priority.",
                    },
                    "limit": {
                        "type": "integer",
                        "default": 50,
                        "description": "Maximum number of tasks to return.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_all_tasks",
            "description": "List all tasks in the system without any filters.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_task",
            "description": "Get a specific task by its ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "integer",
                        "description": "The ID of the task to retrieve.",
                    }
                },
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_task",
            "description": "Update fields of a specific task by ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "integer",
                        "description": "The ID of the task to update.",
                    },
                    "title": {
                        "type": "string",
                        "description": "New title for the task.",
                    },
                    "description": {
                        "type": "string",
                        "description": "New description for the task.",
                    },
                    "status": {
                        "type": "string",
                        "enum": ["pending", "in_progress", "completed", "cancelled"],
                        "description": "New status for the task.",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "New priority for the task.",
                    },
                    "due_date": {
                        "type": "string",
                        "format": "date",
                        "description": "New due date in ISO format (YYYY-MM-DD).",
                    },
                },
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_task",
            "description": "Delete a task by its ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "integer",
                        "description": "The ID of the task to delete.",
                    }
                },
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "complete_task",
            "description": "Mark a specific task as completed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "integer",
                        "description": "The ID of the task to mark as complete.",
                    }
                },
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mark_complete",
            "description": "Mark a specific task as completed (alias for complete_task).",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "integer",
                        "description": "The ID of the task to mark as complete.",
                    }
                },
                "required": ["task_id"],
            },
        },
    },
]
