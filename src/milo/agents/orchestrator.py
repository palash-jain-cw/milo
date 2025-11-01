"""Main orchestrator that routes user messages through appropriate agents."""

import logging
import traceback
from typing import List, Dict, Optional
from openai import OpenAI

from milo.agents.router import route_message
from milo.agents.clarifier import handle_clarification, resolve_clarification
from milo.agents.conversational import handle_conversational
from milo.agents.task_agent import handle_task_agent
from milo.tasks.service import TaskService
from milo.core.config import settings

logger = logging.getLogger(__name__)


def run_task_manager(
    user_message: str,
    task_service: TaskService,
    client: OpenAI,
    conversation_history: Optional[List[dict]] = None,
    max_clarifications: int = 3,
) -> Dict:
    """
    Main orchestrator that routes user messages through the appropriate agents.

    Args:
        user_message: The user's input message
        task_service: TaskService instance
        client: OpenAI client instance
        conversation_history: List of previous messages (optional)
        max_clarifications: Maximum number of clarification rounds (default: 3)

    Returns:
        dict with response, route taken, and updated conversation history
    """
    try:
        if conversation_history is None:
            conversation_history = []

        # Add user message to history
        conversation_history.append({"role": "user", "content": user_message})

        logger.info(f"📨 User: {user_message}")

        # STEP 1: ROUTE THE MESSAGE
        route_output = route_message(
            user_message,
            conversation_history,
            task_service.list_all_tasks(),
            client,
        )

        # STEP 2: HANDLE BASED ON ROUTE

        if route_output.route == "conversational":
            # Handle conversational messages
            response_text = handle_conversational(user_message, client)
            conversation_history.append({"role": "assistant", "content": response_text})

            return {
                "response": response_text,
                "route": "conversational",
                "conversation_history": conversation_history,
            }

        elif route_output.route == "clarify":
            # Handle clarification
            clarification_result = handle_clarification(
                conversation_history,
                task_service.list_all_tasks(),
                client,
            )

            return {
                "response": clarification_result["response"],
                "route": "clarify",
                "conversation_history": clarification_result["conversation_history"],
                "needs_user_input": clarification_result.get("needs_user_input", False),
                "resolved_message": clarification_result.get("resolved_message"),
            }

        elif route_output.route == "agent":
            # Handle task operations
            agent_result = handle_task_agent(
                user_message,
                conversation_history,
                task_service,
                client,
            )

            return {
                "response": agent_result["response"],
                "route": "agent",
                "conversation_history": agent_result["conversation_history"],
                "tool_results": agent_result["tool_results"],
            }

        else:
            error_msg = f"Unknown route: {route_output.route}"
            logger.error(error_msg)
            conversation_history.append({"role": "assistant", "content": error_msg})

            return {
                "response": error_msg,
                "route": "error",
                "conversation_history": conversation_history,
            }

    except Exception as e:
        error_msg = f"Error in task manager: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        conversation_history.append({"role": "assistant", "content": error_msg})

        return {
            "response": error_msg,
            "route": "error",
            "conversation_history": conversation_history,
        }


def interactive_chat():
    """
    Run an interactive chat session with the task manager.
    """
    print("=" * 60)
    print("🤖 TASK MANAGER CHAT")
    print("=" * 60)
    print("Type 'quit' or 'exit' to end the conversation")
    print("=" * 60 + "\n")

    # Initialize services
    task_service = TaskService()
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    conversation_history = []

    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()

            if user_input.lower() in ["quit", "exit", "bye"]:
                print("\n👋 Goodbye!\n")
                break

            if not user_input:
                continue

            # Process the message
            result = run_task_manager(
                user_input,
                task_service,
                client,
                conversation_history,
            )

            # Update conversation history
            conversation_history = result["conversation_history"]

            # Display response
            print(f"\nAssistant: {result['response']}\n")

            # If we need clarification, continue the loop to get user's response
            if result.get("needs_user_input"):
                clarification_input = input("You: ").strip()

                if clarification_input.lower() in ["quit", "exit", "bye"]:
                    print("\n👋 Goodbye!\n")
                    break

                # Resolve clarification
                resolved_message, conversation_history = resolve_clarification(
                    clarification_input,
                    conversation_history,
                    task_service.list_all_tasks(),
                    client,
                )

                # Now route the resolved message
                result = run_task_manager(
                    resolved_message,
                    task_service,
                    client,
                    conversation_history,
                )
                conversation_history = result["conversation_history"]

                print(f"\nAssistant: {result['response']}\n")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
        except Exception as e:
            logger.error(f"Error in interactive chat: {e}\n{traceback.format_exc()}")
            print(f"\n❌ Error: {str(e)}\n")

