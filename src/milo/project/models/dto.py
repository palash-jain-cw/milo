from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Annotated, Literal
from datetime import date
import uuid
from pydantic import StringConstraints


class ProjectUpdate(BaseModel):
    """Schema for updating project information"""

    id: uuid.UUID = Field(..., description="Unique identifier of the project to update")
    name: Optional[
        Annotated[
            str, StringConstraints(strip_whitespace=True, min_length=3, max_length=100)
        ]
    ] = Field(None, description="Project name (3–100 characters)")
    description: Optional[str] = Field(
        None, description="Optional project description (max 500 characters)"
    )
    start_date: Optional[date] = Field(None, description="Date when project starts")
    target_end_date: Optional[date] = Field(
        None, description="Planned project end date"
    )
    status: Optional[Literal["Active", "Completed", "On Hold"]] = Field(
        None, description="Project status"
    )
    owner_id: Optional[uuid.UUID] = Field(
        None, description="UUID of the new project owner"
    )
    member_ids: Optional[List[uuid.UUID]] = Field(
        None, description="List of member UUIDs to set for the project"
    )

    @field_validator("description")
    def validate_description_length(cls, v):
        if v and len(v) > 500:
            raise ValueError("Description cannot exceed 500 characters.")
        return v

    @field_validator("target_end_date")
    def validate_end_date(cls, v, values):
        if (
            v
            and "start_date" in values
            and values["start_date"]
            and v < values["start_date"]
        ):
            raise ValueError("Target end date cannot be before start date.")
        return v

    @field_validator("member_ids")
    def ensure_unique_members(cls, v):
        if v:
            return list(dict.fromkeys(v))
        return v

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Updated Project Name",
                "description": "Updated project description",
                "start_date": "2024-01-01",
                "target_end_date": "2024-12-31",
                "status": "Active",
                "owner_id": "123e4567-e89b-12d3-a456-426614174001",
                "member_ids": [
                    "123e4567-e89b-12d3-a456-426614174002",
                    "123e4567-e89b-12d3-a456-426614174003",
                ],
            }
        }
