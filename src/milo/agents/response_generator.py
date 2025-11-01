"""Response generator for creating natural conversational responses from tool results."""

import logging
import traceback
import json
from typing import List, Dict
from openai import OpenAI

from milo.shared.json_generator import jsonify
from milo.core.config import settings

logger = logging.getLogger(__name__)


def generate_conversational_response(
    user_message: str,
    agent_result: Dict,
    conversation_history: List[dict],
    client: OpenAI,
) -> str:
    """
    Generate a natural, conversational response based on what the agent did.

    Args:
        user_message: Original user message
        agent_result: Results from the task agent including tool_results
        conversation_history: Recent conversation context
        client: OpenAI client instance

    Returns:
        Natural language response string
    """
    try:
        tool_results = agent_result.get("tool_results", [])

        if not tool_results:
            return "I wasn't able to perform any actions. Could you rephrase your request?"

        # Prepare context for the LLM
        tool_summary = []
        for result in tool_results:
            func = result["function"]
            args = result["arguments"]
            res = result["result"]

            tool_summary.append(
                {
                    "function": func,
                    "arguments": args,
                    "result": jsonify(res) if res else None,
                }
            )

        # Include recent conversation for context
        recent_context = ""
        if len(conversation_history) > 1:
            recent_messages = conversation_history[-6:]  # Last 3 exchanges
            recent_context = "\n\nRecent conversation:\n"
            for msg in recent_messages:
                role = "User" if msg["role"] == "user" else "Assistant"
                content = msg["content"][:200]  # Truncate long messages
                recent_context += f"{role}: {content}\n"

        response_generator_prompt = f"""
You are a friendly AI assistant for a task management system.
{recent_context}

The user just said: "{user_message}"

The system has ALREADY COMPLETED these operations:
{json.dumps(tool_summary, indent=2)}

CRITICAL RULES:
1. The operations are COMPLETE - do NOT say "I'll check" or "Just a moment" or "Let me look"
2. Present the ACTUAL RESULTS from the operations above
3. If tasks were found, LIST THEM with details
4. If no tasks were found, say so clearly: "You don't have any tasks due on [date]"
5. Be conversational but ALWAYS include the actual data

Your job is to:
1. Generate a natural, conversational response that presents the ACTUAL RESULTS
2. Be friendly and helpful
3. Consider the conversation context - if this is a follow-up, acknowledge it
4. If tasks were listed, provide a clear summary with key details (titles, priorities, due dates)
5. If tasks were created/updated/deleted, confirm the action with specifics
6. Keep it concise but informative
7. Use a warm, helpful tone

Guidelines for task summaries:
- If the user asked about tasks due on a specific date, show ONLY those tasks (or say none found)
- Don't just say "Found X tasks" - actually describe them
- Group by status if showing multiple tasks (pending, in progress, completed)
- Highlight important information (high priority, due soon, overdue)
- Use bullet points for lists of tasks
- For each task, include: title, priority (if high), status (if in progress), due date (if set)
- Be conversational, not robotic

Guidelines for actions:
- Confirm what was done clearly with specifics
- If multiple operations, explain them in order
- Be encouraging and positive

Generate your response NOW with the actual results:
"""

        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful, friendly task management assistant. ALWAYS present actual results from completed operations. NEVER say you'll check something - the data is already available.",
                },
                {"role": "user", "content": response_generator_prompt},
            ],
            temperature=0.7,
        )

        return response.choices[0].message.content

    except Exception as e:
        logger.error(
            f"Error generating conversational response: {e}\n{traceback.format_exc()}"
        )
        # Fallback to simple summary
        return f"Operation completed with {len(tool_results)} actions."

