from typing import List, Optional
from datetime import datetime, date
import traceback

from sqlmodel import select

from milo.tasks.models import Task, TaskStatus, TaskPriority
from milo.shared.database import get_session
from milo.core.logger.logger_setup import loguru_setup

logger = loguru_setup()


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
                logger.info(f"Created task '{task.title}' with id {task.id}")
                return task
        except Exception as exc:
            logger.error(
                f"Failed to create task '{title}': {exc}\n{traceback.format_exc()}"
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
                    logger.info(f"Retrieved task with id {task_id}")
                else:
                    logger.warning(f"Task with id {task_id} not found")
                return task
        except Exception as exc:
            logger.error(
                f"Failed to retrieve task '{task_id}': {exc}\n{traceback.format_exc()}"
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
                logger.info(f"Retrieved {len(tasks)} tasks")
                return tasks
        except Exception as exc:
            logger.error(f"Failed to list tasks: {exc}\n{traceback.format_exc()}")
            raise

    @staticmethod
    def list_all_tasks() -> List[Task]:
        try:
            with get_session() as session:
                tasks = session.exec(
                    select(Task).order_by(Task.created_at.desc())
                ).all()
                logger.info(f"Retrieved all tasks count={len(tasks)}")
                return tasks
        except Exception as exc:
            logger.error(f"Failed to list all tasks: {exc}\n{traceback.format_exc()}")
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
                    logger.warning(f"Task with id {task_id} not found for update")
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
                logger.info(f"Updated task with id {task_id}")
                return task
        except Exception as exc:
            logger.error(
                f"Failed to update task '{task_id}': {exc}\n{traceback.format_exc()}"
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
                    logger.warning(f"Task with id {task_id} not found for deletion")
                    return False
                session.delete(task)
                logger.info(f"Deleted task with id {task_id}")
                return True
        except Exception as exc:
            logger.error(
                f"Failed to delete task '{task_id}': {exc}\n{traceback.format_exc()}"
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
                    logger.warning(f"Task with id {task_id} not found for completion")
                    return None
                task.status = TaskStatus.completed
                task.updated_at = datetime.now()
                session.add(task)
                session.flush()
                session.refresh(task)
                logger.info(f"Marked task {task_id} as completed")
                return task
        except Exception as exc:
            logger.error(
                f"Failed to mark task '{task_id}' as complete: {exc}\n{traceback.format_exc()}"
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
                logger.info("Deleted all tasks")
                return True
        except Exception as exc:
            logger.error(f"Failed to delete all tasks: {exc}\n{traceback.format_exc()}")
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
            logger.error(f"Invalid status '{status}': {exc}\n{traceback.format_exc()}")
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
            logger.error(
                f"Invalid priority '{priority}': {exc}\n{traceback.format_exc()}"
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
            logger.error(
                f"Invalid due_date '{due_date}': {exc}\n{traceback.format_exc()}"
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
