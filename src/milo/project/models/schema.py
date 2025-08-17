from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Literal
from datetime import date, datetime, timezone
from typing import Annotated
from pydantic import StringConstraints
import uuid
from milo.user.models.schema import User


class Project(BaseModel):
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4, description="Unique project identifier"
    )
    name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=3, max_length=100)
    ] = Field(..., description="Project name (3–100 characters)")
    description: Optional[str] = Field(
        None, description="Optional project description (max 500 characters)"
    )
    start_date: date = Field(
        default_factory=date.today, description="Date when project starts"
    )
    target_end_date: Optional[date] = Field(
        None, description="Planned project end date"
    )
    status: Literal["Active", "Completed", "On Hold"] = Field(
        default="Active", description="Project status"
    )
    owner: User = Field(..., description="User of the project owner")
    members: List[User] = Field(
        default_factory=list,
        description="List of users who are members of the project",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(datetime.UTC).replace(tzinfo=timezone.utc),
        description="Timestamp of project creation",
    )

    @field_validator("description")
    def validate_description_length(cls, v):
        if v and len(v) > 500:
            raise ValueError("Description cannot exceed 500 characters.")
        return v

    @field_validator("target_end_date")
    def validate_end_date(cls, v, values):
        if v and "start_date" in values and v < values["start_date"]:
            raise ValueError("Target end date cannot be before start date.")
        return v

    @field_validator("members")
    def validate_members(cls, members, values):
        if "owner_id" in values and values["owner_id"] in members:
            raise ValueError("Owner cannot also be listed as a member.")
        return members

    @field_validator("members", mode="before")
    def ensure_unique_members(cls, members):
        return list(dict.fromkeys(members))
