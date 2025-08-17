from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone, UTC
from pydantic import BaseModel, Field


class TaskBase(BaseModel):
    name: str = Field(..., description="Title of the task")
    description: Optional[str] = Field(None, description="Details about the task")
    status: str = Field("TODO", description="Task status: TODO, IN_PROGRESS, DONE")
    due_date: Optional[datetime] = Field(None, description="Deadline for the task")


class TaskCreate(TaskBase):
    project_id: UUID = Field(..., description="ID of the project this task belongs to")
    parent_id: Optional[UUID] = Field(
        None, description="Parent task if this is a subtask"
    )

class Task(TaskBase):
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    parent_id: Optional[UUID] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=timezone.utc))
    # recursive relationship
    subtasks: List["Task"] = Field(default_factory=list)

    class Config:
        orm_mode = True

class TaskUpdate(TaskBase):
    id: UUID = Field(..., description="ID of the task to update")
    project_id: Optional[UUID] = Field(
        None, description="ID of the project this task belongs to"
    )
    parent_id: Optional[UUID] = Field(
        None, description="Parent task if this is a subtask"
    )
    name: Optional[str] = Field(None, description="Name of the task")
    description: Optional[str] = Field(None, description="Details about the task")
    status: Optional[str] = Field(
        None, description="Task status: TODO, IN_PROGRESS, DONE"
    )
    due_date: Optional[datetime] = Field(None, description="Deadline for the task")
    subtasks: Optional[List["Task"]] = Field(None, description="Subtasks of the task")


# to resolve forward reference for subtasks
Task.model_rebuild()
