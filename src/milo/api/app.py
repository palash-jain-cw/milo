"""FastAPI application for Milo task manager."""

import logging
import traceback
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

from milo.api.models import (
    ChatRequest,
    ChatResponse,
    ChatMessage,
    TaskResponse,
    HealthResponse,
)
from milo.agents import run_task_manager
from milo.agents.clarifier import resolve_clarification
from milo.tasks.service import TaskService
from milo.shared.database import init_db
from milo.shared.json_generator import jsonify
from milo.core.config import settings

logger = logging.getLogger(__name__)

# Global instances
task_service: TaskService = None
openai_client: OpenAI = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    global task_service, openai_client

    # Startup
    logger.info("🚀 Starting Milo API...")
    init_db()
    task_service = TaskService()
    openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    logger.info("✅ Milo API started successfully")

    yield

    # Shutdown
    logger.info("👋 Shutting down Milo API...")


# Create FastAPI app
app = FastAPI(
    title="Milo Task Manager API",
    description="AI-powered task management system with conversational interface",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check."""
    return HealthResponse(status="healthy", version="0.1.0")


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(status="healthy", version="0.1.0")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint for conversational task management.

    Args:
        request: ChatRequest with message and optional conversation history

    Returns:
        ChatResponse with assistant response and updated conversation history
    """
    try:
        logger.info(f"📨 Chat request: {request.message}")

        # Convert ChatMessage to dict
        conversation_history = (
            [msg.model_dump() for msg in request.conversation_history]
            if request.conversation_history
            else []
        )

        # Process the message through the agent system
        result = run_task_manager(
            request.message,
            task_service,
            openai_client,
            conversation_history,
        )

        # Convert conversation history back to ChatMessage objects
        chat_history = [
            ChatMessage(role=msg["role"], content=msg["content"])
            for msg in result["conversation_history"]
        ]

        return ChatResponse(
            response=result["response"],
            route=result["route"],
            conversation_history=chat_history,
            needs_user_input=result.get("needs_user_input", False),
            tool_results=result.get("tool_results"),
        )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/clarify", response_model=ChatResponse)
async def clarify(request: ChatRequest):
    """
    Endpoint for resolving clarifications.

    Args:
        request: ChatRequest with clarification response and conversation history

    Returns:
        ChatResponse with resolved message routed through the system
    """
    try:
        logger.info(f"🔍 Clarification request: {request.message}")

        # Convert ChatMessage to dict
        conversation_history = (
            [msg.model_dump() for msg in request.conversation_history]
            if request.conversation_history
            else []
        )

        # Resolve the clarification
        resolved_message, updated_history = resolve_clarification(
            request.message,
            conversation_history,
            task_service.list_all_tasks(),
            openai_client,
        )

        # Now route the resolved message
        result = run_task_manager(
            resolved_message,
            task_service,
            openai_client,
            updated_history,
        )

        # Convert conversation history back to ChatMessage objects
        chat_history = [
            ChatMessage(role=msg["role"], content=msg["content"])
            for msg in result["conversation_history"]
        ]

        return ChatResponse(
            response=result["response"],
            route=result["route"],
            conversation_history=chat_history,
            needs_user_input=result.get("needs_user_input", False),
            tool_results=result.get("tool_results"),
        )

    except Exception as e:
        logger.error(f"Error in clarify endpoint: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(
    status: str = None,
    priority: str = None,
    limit: int = 50,
):
    """
    List tasks with optional filters.

    Args:
        status: Filter by status (pending/in_progress/completed/cancelled)
        priority: Filter by priority (low/medium/high)
        limit: Maximum number of tasks to return

    Returns:
        List of tasks
    """
    try:
        if status or priority:
            tasks = task_service.list_tasks(status=status, priority=priority, limit=limit)
        else:
            tasks = task_service.list_all_tasks()

        # Convert to JSON-serializable format
        tasks_json = jsonify(tasks)

        return [TaskResponse(**task) for task in tasks_json]

    except Exception as e:
        logger.error(f"Error listing tasks: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int):
    """
    Get a specific task by ID.

    Args:
        task_id: Task ID

    Returns:
        Task details
    """
    try:
        task = task_service.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        task_json = jsonify(task)
        return TaskResponse(**task_json)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int):
    """
    Delete a task by ID.

    Args:
        task_id: Task ID

    Returns:
        Success message
    """
    try:
        success = task_service.delete_task(task_id)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")

        return {"message": f"Task {task_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting task: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

