"""Clarifier agent for handling ambiguous user messages."""

import traceback
from typing import List, Tuple, Dict
from openai import OpenAI

from milo.agents.models import ClarifierResponse, ClarificationResolutionResponse
from milo.shared.utils import (
    attach_output_schema_to_prompt,
    attach_task_list_to_prompt,
    attach_conversation_history_to_prompt,
    validate_and_load_structured_output,
)
from milo.core.config import settings
from milo.core.logger.logger_setup import loguru_setup

logger = loguru_setup()


clarifier_instructions = """
You are a Clarifier Agent for an AI Task Manager.

Your goal is to help clarify the user's message when their intent or reference is ambiguous.
You are NOT performing any task actions yourself — only asking a question to make the user's request clear.

Use the provided conversation history and the current task list to understand what the user might be referring to.
Ask ONE short, natural question to clarify what they meant. Give the user all the options to choose from whenever needed. 
When referring to tasks, integrate the task naturally into the question instead of using the task name and avoid sounding robotic.

Guidelines:
- Be specific (e.g., "Did you mean the team meeting or the 1:1 with your manager?")
- Be polite and concise — sound like a helpful assistant.
- If the user's intent is partially clear, focus the question on the missing detail.
- Never output multiple questions, or assume the meaning.
- Always respond in JSON only.
"""


clarification_resolution_instructions = """
You are a Clarification Resolver for a Task Manager AI.

Your job:
Given the recent conversation and the user's clarification,
restate what the user *actually intends to do* as a clear, explicit message
that the task manager can understand and route normally.

Rules:
- Use the clarifier's last question and the user's response to infer intent.
- **PRESERVE ALL CONTEXT** from the original message (dates, task names, etc.)
- If the user confirmed (e.g., "Yes"), resolve it into a full message like:
  "Yes, delete the 'team meeting' task." → becomes "Delete the 'team meeting' task."
- If they negated ("No, the other one"), specify that clearly.
- If they're clarifying a date or detail, include that in the resolved message
- If ambiguous, restate what is still unclear.
- Respond ONLY with the rewritten user message (no explanations, no reasoning).
- The message should be rewritten from the user's perspective, not the assistant's.

Example Input:
  Original: "Do I have tasks due on my birthday?"
  Clarifier: "What date is your birthday?"
  User: "November 11th"
Example Output:
  "Do I have any tasks due on November 11th?"

Example Input:
  Clarifier: "Did you mean the 'team meeting'?"
  User: "Yes."
Example Output:
  "Delete the 'team meeting' task."
"""


def get_clarifier_prompt(task_list: List, conversation_history: List[dict]) -> str:
    """
    Build the clarifier system prompt with context.

    Args:
        task_list: Current list of tasks
        conversation_history: Recent conversation messages

    Returns:
        Complete system prompt for the clarifier
    """
    try:
        prompt = attach_conversation_history_to_prompt(
            clarifier_instructions, conversation_history, last_n=-1
        )
        prompt = attach_task_list_to_prompt(prompt, task_list)
        prompt = attach_output_schema_to_prompt(prompt, ClarifierResponse)
        return prompt
    except Exception as e:
        logger.error(f"Error building clarifier prompt: {e}\n{traceback.format_exc()}")
        raise


def get_clarification_resolution_prompt(
    task_list: List, conversation_history: List[dict]
) -> str:
    """
    Build the clarification resolution system prompt with context.

    Args:
        task_list: Current list of tasks
        conversation_history: Recent conversation messages

    Returns:
        Complete system prompt for clarification resolution
    """
    try:
        prompt = attach_conversation_history_to_prompt(
            clarification_resolution_instructions, conversation_history, last_n=-1
        )
        prompt = attach_task_list_to_prompt(prompt, task_list)
        prompt = attach_output_schema_to_prompt(
            prompt, ClarificationResolutionResponse
        )
        return prompt
    except Exception as e:
        logger.error(
            f"Error building clarification resolution prompt: {e}\n{traceback.format_exc()}"
        )
        raise


def handle_clarification(
    conversation_history: List[dict],
    task_list: List,
    client: OpenAI,
) -> Dict:
    """
    Handle clarification flow: ask question, wait for response.

    Args:
        conversation_history: Recent conversation messages
        task_list: Current list of tasks
        client: OpenAI client instance

    Returns:
        Dict with response, conversation_history, and needs_user_input flag
    """
    try:
        logger.info("❓ Handling clarification...")

        # Generate clarifying question
        clarifier_response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": get_clarifier_prompt(task_list, conversation_history),
                },
            ],
        )

        clarifier_output = validate_and_load_structured_output(
            clarifier_response.choices[0].message.content, ClarifierResponse
        )

        question = clarifier_output.clarifying_question
        logger.info(f"❓ Clarifying question: {question}")

        # Add clarification to history
        conversation_history.append(
            {
                "role": "assistant",
                "content": clarifier_response.choices[0].message.content,
            }
        )

        return {
            "response": question,
            "conversation_history": conversation_history,
            "needs_user_input": True,  # Signal that we need user to respond
        }

    except Exception as e:
        logger.error(f"Error handling clarification: {e}\n{traceback.format_exc()}")
        raise


def resolve_clarification(
    user_response: str,
    conversation_history: List[dict],
    task_list: List,
    client: OpenAI,
) -> Tuple[str, List[dict]]:
    """
    Resolve the user's clarification response into an explicit message.

    Args:
        user_response: User's clarification response
        conversation_history: Recent conversation messages
        task_list: Current list of tasks
        client: OpenAI client instance

    Returns:
        Tuple of (resolved_message, updated_conversation_history)
    """
    try:
        logger.info("🔍 Resolving clarification...")

        # Add user's clarification response to history
        conversation_history.append({"role": "user", "content": user_response})

        # Resolve the clarification
        resolution_response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": get_clarification_resolution_prompt(
                        task_list, conversation_history
                    ),
                },
            ],
        )

        resolution_output = validate_and_load_structured_output(
            resolution_response.choices[0].message.content,
            ClarificationResolutionResponse,
        )

        resolved_message = resolution_output.resolution
        logger.info(f"✅ Resolved to: {resolved_message}")

        # Add resolution to history
        conversation_history.append(
            {
                "role": "assistant",
                "content": resolution_response.choices[0].message.content,
            }
        )

        return resolved_message, conversation_history

    except Exception as e:
        logger.error(f"Error resolving clarification: {e}\n{traceback.format_exc()}")
        raise

