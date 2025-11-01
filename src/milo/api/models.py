"""API request/response models."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ChatMessage(BaseModel):
    """Chat message model."""

    role: str = Field(..., description="Message role (user/assistant)")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    message: str = Field(..., description="User message")
    conversation_history: Optional[List[ChatMessage]] = Field(
        default=None, description="Conversation history"
    )


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    response: str = Field(..., description="Assistant response")
    route: str = Field(..., description="Route taken (agent/conversational/clarify)")
    conversation_history: List[ChatMessage] = Field(
        ..., description="Updated conversation history"
    )
    needs_user_input: Optional[bool] = Field(
        default=False, description="Whether clarification is needed"
    )
    tool_results: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Tool execution results"
    )


class TaskCreate(BaseModel):
    """Request model for creating a task."""

    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(default=None, description="Task description")
    priority: Optional[str] = Field(default="medium", description="Task priority")
    due_date: Optional[str] = Field(default=None, description="Due date (YYYY-MM-DD)")


class TaskUpdate(BaseModel):
    """Request model for updating a task."""

    title: Optional[str] = Field(default=None, description="Task title")
    description: Optional[str] = Field(default=None, description="Task description")
    status: Optional[str] = Field(default=None, description="Task status")
    priority: Optional[str] = Field(default=None, description="Task priority")
    due_date: Optional[str] = Field(default=None, description="Due date (YYYY-MM-DD)")


class TaskResponse(BaseModel):
    """Response model for task operations."""

    id: int
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    due_date: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
