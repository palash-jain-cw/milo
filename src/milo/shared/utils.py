import json
from pydantic import BaseModel
from pydantic import ValidationError
import traceback
from logging import getLogger
from typing import List
from milo.shared.json_generator import jsonify
from datetime import datetime, date

logger = getLogger(__name__)


def attach_output_schema_to_prompt(prompt: str, output_schema: type[BaseModel]) -> str:
    schema = output_schema.model_json_schema()
    schema_str = json.dumps(schema, indent=2)
    return f"""
    {prompt}

    Adhere strictly to the following output schema:
    {schema_str}
    """


def validate_and_load_structured_output(
    output: str, output_schema: type[BaseModel]
) -> BaseModel:
    start = output.find("{")
    end = output.rfind("}") + 1
    json_str = output[start:end]
    try:
        parsed = json.loads(json_str)
        model_output = output_schema.model_validate(parsed)
        return model_output
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON: {json_str}")
        logger.error(traceback.format_exc())
        return f"Error parsing JSON: {json_str}, error: {e}"
    except ValidationError as e:
        logger.error(f"Error validating JSON: {json_str}")
        logger.error(traceback.format_exc())
        return f"Error validating JSON: {json_str}, error: {e}"


def attach_task_list_to_prompt(prompt: str, task_list: List) -> str:
    task_list_str = json.dumps(jsonify(task_list), indent=2)
    return f"""
    {prompt}

    Here is the current task list:
    {task_list_str}
    """


def attach_conversation_history_to_prompt(
    prompt: str, conversation_history: List, last_n: int = 5
) -> str:
    if last_n > 0:
        conversation_history_str = json.dumps(
            jsonify(conversation_history[-last_n:]), indent=2
        )
    else:
        conversation_history_str = json.dumps(jsonify(conversation_history), indent=2)
    return f"""
    {prompt}

    Here is the recent conversation history (most recent last):
    {conversation_history_str}
    """


def add_temporal_context_to_prompt(prompt: str) -> str:
    # Add current date/time context
    current_datetime = datetime.now()
    current_date = date.today()

    temporal_context = f"""

        ## CURRENT DATE AND TIME INFORMATION

        Today's date: {current_date.strftime("%Y-%m-%d")} ({current_date.strftime("%A, %B %d, %Y")})
        Current time: {current_datetime.strftime("%H:%M:%S")}
        Current day of week: {current_date.strftime("%A")}

        When the user mentions relative dates, calculate the actual date:
        - "today" → {current_date.strftime("%Y-%m-%d")}
        - "tomorrow" → calculate as today + 1 day
        - "next week" → calculate as today + 7 days
        - "in 3 days" → calculate as today + 3 days
        - "next Monday" → calculate the next occurrence of Monday
        - "end of week" → calculate the next Friday/Sunday depending on context
        - "end of month" → calculate the last day of current month

        Always convert relative dates to ISO format (YYYY-MM-DD) when calling functions.
        """
    return f"""
    {prompt}

    {temporal_context}
    """
