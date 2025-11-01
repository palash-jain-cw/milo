"""Tool execution logic for task operations."""

import logging
import traceback
from typing import Dict, Any

from milo.tasks.service import TaskService

logger = logging.getLogger(__name__)


def execute_tool_call(
    function_name: str, function_args: Dict[str, Any], task_service: TaskService
) -> Any:
    """
    Execute a single tool call and return the result.

    Args:
        function_name: Name of the function to execute
        function_args: Arguments to pass to the function
        task_service: TaskService instance to use for operations

    Returns:
        Result of the function call
    """
    try:
        if function_name == "list_all_tasks":
            result = task_service.list_all_tasks()
        elif function_name == "list_tasks":
            result = task_service.list_tasks(**function_args)
        elif function_name == "get_task":
            result = task_service.get_task(**function_args)
        elif function_name == "create_task":
            result = task_service.create_task(**function_args)
        elif function_name == "update_task":
            result = task_service.update_task(**function_args)
        elif function_name == "delete_task":
            result = task_service.delete_task(**function_args)
        elif function_name in ["complete_task", "mark_complete"]:
            result = task_service.complete_task(**function_args)
        else:
            result = {"error": f"Unknown function: {function_name}"}

        logger.info(f"✓ Executed {function_name} successfully")
        return result

    except Exception as e:
        logger.error(
            f"✗ Error executing {function_name}: {e}\n{traceback.format_exc()}"
        )
        return {"error": str(e)}

