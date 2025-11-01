"""Router agent for intent classification and message routing."""

import traceback
from typing import List
from openai import OpenAI

from milo.agents.models import IntentClassificationResponse
from milo.shared.utils import (
    attach_output_schema_to_prompt,
    attach_task_list_to_prompt,
    validate_and_load_structured_output,
)
from milo.core.config import settings
from milo.core.logger.logger_setup import loguru_setup

logger = loguru_setup()


router_instructions = """
You are a routing model that decides how the Task Manager system should handle a user's message.

Your goal is to determine what kind of response the system should produce based on the user's intent and the current task list.

**IMPORTANT - CONVERSATION CONTEXT**: 
You have access to the full conversation history. Use it to understand the user's message:
- If the user says "Did you find any?", look at what they asked about previously
- If they mention "it", "that", "them", "then", check the recent context
- If they mentioned a date/task earlier, use that information
- Only classify as "clarify" if the context truly doesn't provide enough information

You must classify the message into one of the following categories:

1. "conversational" —
The message is social, emotional, or general discussion.
These are expressions of mood, greetings, gratitude, or reflection that do not request an action.
(e.g. the user is chatting, sharing how they feel, or stating general information.)

2. "agent" —
The message expresses an intention to act or manage tasks.
This includes:
- Direct requests to list, create, update, complete, or remove tasks. Basically, anything that is a task-related action.
- Indirect or implied actions (for example, indicating that something is finished, needs to be done, or should be changed).
- Multiple task-related statements in the same message.
- Follow-up questions about tasks that were just discussed (e.g., "Did you find any?" after asking about tasks)
If a message mixes conversational and actionable content, **prioritize the actionable parts** and classify as "agent".

3. "clarify" —
The message refers to something ambiguous or incomplete that CANNOT be resolved from conversation history.
If you cannot confidently tell what the user wants to act on EVEN WITH the conversation context, classify as "clarify".

If the message could reasonably refer to multiple possible tasks or actions, or the object of the action is unclear, classify as 'clarify'.
It is always better to ask for clarification than to act incorrectly.
**BUT**: Check the conversation history first - the answer might be there!
"""


def get_router_prompt(task_list: List) -> str:
    """
    Build the router system prompt with task list and output schema.

    Args:
        task_list: Current list of tasks

    Returns:
        Complete system prompt for the router
    """
    try:
        prompt = attach_task_list_to_prompt(router_instructions, task_list)
        prompt = attach_output_schema_to_prompt(prompt, IntentClassificationResponse)
        return prompt
    except Exception as e:
        logger.error(f"Error building router prompt: {e}\n{traceback.format_exc()}")
        raise


def route_message(
    user_message: str,
    conversation_history: List[dict],
    task_list: List,
    client: OpenAI,
) -> IntentClassificationResponse:
    """
    Route a user message to the appropriate handler.

    Args:
        user_message: The user's input message
        conversation_history: List of previous messages
        task_list: Current list of tasks
        client: OpenAI client instance

    Returns:
        IntentClassificationResponse with route and reasoning
    """
    try:
        logger.info("🔀 Routing message...")

        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": get_router_prompt(task_list),
                },
            ]
            + conversation_history,
        )

        route_output = validate_and_load_structured_output(
            response.choices[0].message.content, IntentClassificationResponse
        )

        logger.info(f"📍 Route: {route_output.route} - {route_output.reasoning}")
        return route_output

    except Exception as e:
        logger.error(f"Error routing message: {e}\n{traceback.format_exc()}")
        raise

