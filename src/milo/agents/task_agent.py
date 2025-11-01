"""Task agent for executing task-related operations via function calling."""

import traceback
import json
from typing import List, Dict, Optional
from openai import OpenAI

from milo.tasks.service import TaskService, functions
from milo.tasks.tools import execute_tool_call
from milo.shared.utils import (
    attach_task_list_to_prompt,
    attach_conversation_history_to_prompt,
    add_temporal_context_to_prompt,
)
from milo.shared.json_generator import jsonify
from milo.core.config import settings
from milo.core.logger.logger_setup import loguru_setup

logger = loguru_setup()


task_agent_instructions = """
You are a Task Agent for an AI Task Management System.

Your SOLE responsibility is to execute task-related actions by calling the appropriate functions.
You do NOT engage in conversation, provide explanations, or ask questions.
You ONLY output function calls to perform the requested operations.

## CONTEXT AWARENESS
- You will receive recent conversation history
- If the user refers to "this task", "that report", "it", etc., look at the conversation history
- If they just created a task and are now providing more details, UPDATE that task instead of creating a new one
- Pay attention to what was just discussed to understand implicit references


## DATE AND TIME HANDLING
- When users mention relative dates (tomorrow, next week, in 3 days, etc.), calculate the actual date
- Use the current date information provided at the start of this prompt
- Always express dates in ISO format: YYYY-MM-DD
- Common patterns:
  * "due tomorrow" → current date + 1 day
  * "due next week" → current date + 7 days
  * "due in X days" → current date + X days
  * "due next [weekday]" → calculate next occurrence of that weekday
  * "due by Friday" → calculate the next Friday
  * "due end of month" → last day of current month

## YOUR ROLE
- Analyze the user's request AND recent conversation to identify what task operations need to be performed
- Determine the correct sequence of function calls needed
- Execute those function calls with the appropriate parameters
- Handle multi-step operations by chaining function calls when necessary

## AVAILABLE TOOLS

### 1. list_all_tasks()
**Purpose**: Retrieve all tasks in the system
**When to use**: 
- When you need to see all tasks before performing an operation
- When the user asks to "show", "list", or "see" all tasks
- When you need to find a task by title/description (call this first, then operate on the result)
**Parameters**: None

### 2. list_tasks(status, priority, limit)
**Purpose**: Retrieve filtered tasks
**When to use**:
- When user specifies a status filter (e.g., "show pending tasks", "list completed tasks")
- When user specifies a priority filter (e.g., "show high priority tasks")
- When you need to narrow down results
**Parameters**:
- status: "pending" | "in_progress" | "completed" | "cancelled" (optional)
- priority: "low" | "medium" | "high" (optional)
- limit: integer, max results to return (optional, default: 50)

### 3. get_task(task_id)
**Purpose**: Retrieve a specific task by its ID
**When to use**:
- When you have a task ID and need to retrieve that specific task
- Before updating or deleting a task to verify it exists
**Parameters**:
- task_id: integer (required)

### 4. create_task(title, description, priority)
**Purpose**: Create a new task
**When to use**:
- When user wants to add, create, or make a new task
- When user describes something they need to do
**Parameters**:
- title: string, concise task name (required)
- description: string, detailed task information (optional)
- priority: "low" | "medium" | "high" (optional, defaults to "medium")

### 5. update_task(task_id, title, description, status, priority, due_date)
**Purpose**: Modify an existing task's fields
**When to use**:
- When user wants to change, modify, or update task details
- When user wants to change priority, status, or other fields
- When user says a task is "in progress" or changes its state
**Parameters**:
- task_id: integer (required)
- title: string (optional)
- description: string (optional)
- status: "pending" | "in_progress" | "completed" | "cancelled" (optional)
- priority: "low" | "medium" | "high" (optional)
- due_date: string in ISO format "YYYY-MM-DD" (optional)

### 6. complete_task(task_id) / mark_complete(task_id)
**Purpose**: Mark a task as completed
**When to use**:
- When user indicates a task is done, finished, or completed
- Prefer this over update_task when only marking complete
**Parameters**:
- task_id: integer (required)

### 7. delete_task(task_id)
**Purpose**: Remove a task from the system
**When to use**:
- When user wants to delete, remove, or get rid of a task
**Parameters**:
- task_id: integer (required)

## OPERATION PATTERNS

### Pattern 1: Direct Operations (ID Known)
If task_id is explicitly provided or clearly referenced:
- Call the function directly with the task_id

### Pattern 2: Search-Then-Operate (ID Unknown)
If user refers to a task by title/description/attribute:
1. First call list_all_tasks() or list_tasks() to find the task
2. Identify the correct task_id from the results
3. Then call the target operation (update, delete, complete, etc.)

### Pattern 3: Multiple Operations
If user requests multiple actions:
- Chain function calls in logical order
- Example: "Create 3 tasks" → call create_task() three times
- Example: "Complete all high priority tasks" → list_tasks(priority="high"), then complete_task() for each

### Pattern 4: Bulk Operations
If user wants to operate on multiple tasks:
1. First retrieve the task list with appropriate filters
2. Then perform the operation on each matching task

## IMPORTANT RULES

1. **NEVER respond with text** - Only output function calls
2. **Always verify before destructive operations** - Call list_all_tasks() or get_task() before delete/update if task_id is not certain
3. **Use exact parameter values** - Status and priority must match the enum values exactly
4. **Handle ambiguity** - If a task reference is unclear, call list_all_tasks() first to identify the correct task
5. **Chain operations logically** - When multiple steps are needed, call them in the correct sequence
6. **Prefer specific over general** - Use complete_task() instead of update_task(status="completed") when just marking complete
7. **Date format** - Always use ISO format (YYYY-MM-DD) for due_date parameters

## EXAMPLES

User: "Create a task to review the quarterly report"
→ create_task(title="Review quarterly report", priority="medium")

User: "Show me all my high priority tasks"
→ list_tasks(priority="high")

User: "Mark task 5 as completed"
→ complete_task(task_id=5)

User: "Delete the task about the team lunch"
→ list_all_tasks()  # First find the task
→ delete_task(task_id=<id_from_results>)  # Then delete it

User: "Change the quarterly report task to high priority"
→ list_all_tasks()  # Find the task
→ update_task(task_id=<id_from_results>, priority="high")

User: "Create three tasks: buy groceries, call mom, and finish presentation"
→ create_task(title="Buy groceries")
→ create_task(title="Call mom")
→ create_task(title="Finish presentation")

Remember: You are a function-calling agent. Your output should ONLY be function calls, nothing else.
"""


def get_task_agent_prompt(
    task_list: List, conversation_history: Optional[List[dict]] = None
) -> str:
    """
    Prepare the task agent prompt with context.

    Args:
        task_list: Current list of tasks
        conversation_history: Recent conversation messages (optional)

    Returns:
        Complete system prompt for the task agent
    """
    try:
        prompt = add_temporal_context_to_prompt(task_agent_instructions)
        prompt = attach_task_list_to_prompt(prompt, task_list)

        # Add recent conversation context
        if conversation_history:
            prompt = attach_conversation_history_to_prompt(
                prompt, conversation_history, last_n=3
            )

        return prompt

    except Exception as e:
        logger.error(f"Error building task agent prompt: {e}\n{traceback.format_exc()}")
        raise


def run_task_agent(
    user_message: str,
    task_service: TaskService,
    client: OpenAI,
    max_iterations: int = 10,
    conversation_history: Optional[List[dict]] = None,
) -> Dict:
    """
    Execute the task agent with an agentic loop that handles multiple tool calls.

    Args:
        user_message: The user's request
        task_service: TaskService instance
        client: OpenAI client instance
        max_iterations: Maximum number of agent iterations (default: 10)
        conversation_history: Recent conversation messages (optional)

    Returns:
        dict with tool_results, messages, iterations, and final_message
    """
    try:
        logger.info(f"🤖 Starting Task Agent for: '{user_message}'")

        messages = [
            {
                "role": "system",
                "content": get_task_agent_prompt(
                    task_service.list_all_tasks(),
                    conversation_history,
                ),
            },
            {
                "role": "user",
                "content": user_message,
            },
        ]

        tool_results = []
        iteration = 0
        final_message = "Task completed"

        while iteration < max_iterations:
            iteration += 1
            logger.info(f"📍 Iteration {iteration}/{max_iterations}")

            # Call the LLM
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                tools=functions,
                tool_choice="auto",
            )

            assistant_message = response.choices[0].message

            # Check if the model wants to call tools
            if not assistant_message.tool_calls:
                logger.info("✅ Agent finished - no more tool calls")
                final_message = (
                    assistant_message.content
                    if assistant_message.content
                    else "Task completed"
                )
                break

            # Add assistant message to conversation
            messages.append(
                {
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in assistant_message.tool_calls
                    ],
                }
            )

            # Execute each tool call
            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                logger.info(f"🔧 Calling {function_name}({function_args})")

                # Execute the function
                result = execute_tool_call(function_name, function_args, task_service)

                # Store the result
                tool_results.append(
                    {
                        "function": function_name,
                        "arguments": function_args,
                        "result": result,
                    }
                )

                # Convert result to JSON for the LLM
                result_json = json.dumps(jsonify(result), indent=2)

                # Add tool result to messages
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": result_json,
                    }
                )
        else:
            # Max iterations reached
            logger.warning(f"⚠️ Max iterations ({max_iterations}) reached")
            final_message = "Max iterations reached"

        logger.info(
            f"🎯 Completed {len(tool_results)} tool calls in {iteration} iterations"
        )

        return {
            "tool_results": tool_results,
            "messages": messages,
            "iterations": iteration,
            "final_message": final_message,
        }

    except Exception as e:
        logger.error(f"Error running task agent: {e}\n{traceback.format_exc()}")
        raise


def handle_task_agent(
    user_message: str,
    conversation_history: List[dict],
    task_service: TaskService,
    client: OpenAI,
) -> Dict:
    """
    Handle task operations by calling the task agent and generating a conversational response.

    Args:
        user_message: The user's request
        conversation_history: Recent conversation messages
        task_service: TaskService instance
        client: OpenAI client instance

    Returns:
        Dict with response, conversation_history, and tool_results
    """
    try:
        logger.info("🤖 Handling task operation...")

        # Run the task agent WITH conversation history
        agent_result = run_task_agent(
            user_message,
            task_service,
            client,
            conversation_history=conversation_history,
        )

        # Import response generator here to avoid circular imports
        from milo.agents.response_generator import generate_conversational_response

        # Generate a natural, conversational response
        response_text = generate_conversational_response(
            user_message, agent_result, conversation_history, client
        )

        logger.info(f"✅ Response generated: {response_text[:100]}...")

        # Add response to conversation history
        conversation_history.append({"role": "assistant", "content": response_text})

        return {
            "response": response_text,
            "conversation_history": conversation_history,
            "tool_results": agent_result["tool_results"],
        }

    except Exception as e:
        logger.error(f"Error handling task agent: {e}\n{traceback.format_exc()}")
        raise


def generate_agent_summary(agent_result: Dict) -> str:
    """
    Generate a natural language summary of what the task agent did.

    Args:
        agent_result: Result dict from run_task_agent

    Returns:
        Natural language summary string
    """
    try:
        tool_results = agent_result["tool_results"]

        if not tool_results:
            return "I couldn't perform any actions."

        # Simple summary generation
        summaries = []

        for result in tool_results:
            func = result["function"]
            args = result["arguments"]
            res = result["result"]

            if func == "create_task":
                summaries.append(f"Created task: '{args['title']}'")
            elif func == "delete_task":
                if res:
                    summaries.append(f"Deleted task (ID: {args['task_id']})")
                else:
                    summaries.append(
                        f"Could not find task to delete (ID: {args['task_id']})"
                    )
            elif func == "complete_task" or func == "mark_complete":
                if res:
                    summaries.append(f"Marked task as complete (ID: {args['task_id']})")
                else:
                    summaries.append(
                        f"Could not find task to complete (ID: {args['task_id']})"
                    )
            elif func == "update_task":
                if res:
                    summaries.append(f"Updated task (ID: {args['task_id']})")
                else:
                    summaries.append(
                        f"Could not find task to update (ID: {args['task_id']})"
                    )
            elif func == "list_tasks" or func == "list_all_tasks":
                if isinstance(res, list):
                    summaries.append(f"Found {len(res)} tasks")

        return " ".join(summaries) if summaries else "Operation completed."

    except Exception as e:
        logger.error(f"Error generating agent summary: {e}\n{traceback.format_exc()}")
        return "Operation completed with errors."

