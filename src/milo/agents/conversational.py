"""Conversational handler for social/emotional messages."""

import traceback
from openai import OpenAI

from milo.core.config import settings
from milo.core.logger.logger_setup import loguru_setup

logger = loguru_setup()


conversational_instructions = """
You are a friendly AI assistant for a task management system.

The user has sent you a conversational message (not a task-related request).
Respond naturally and warmly. Keep it brief and friendly.

If they're greeting you, greet them back.
If they're thanking you, acknowledge it gracefully.
If they're sharing how they feel, respond empathetically.

Keep your response to 1-2 sentences maximum.
"""


def handle_conversational(user_message: str, client: OpenAI) -> str:
    """
    Handle conversational/social messages with a friendly response.

    Args:
        user_message: The user's conversational message
        client: OpenAI client instance

    Returns:
        Friendly response text
    """
    try:
        logger.info("💬 Handling conversational message...")

        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": conversational_instructions},
                {"role": "user", "content": user_message},
            ],
        )

        response_text = response.choices[0].message.content
        logger.info(f"💬 Response: {response_text}")

        return response_text

    except Exception as e:
        logger.error(
            f"Error handling conversational message: {e}\n{traceback.format_exc()}"
        )
        raise

