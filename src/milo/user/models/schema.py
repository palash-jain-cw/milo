from pydantic import BaseModel, Field
from typing import Annotated, Optional
from pydantic import StringConstraints, EmailStr
from datetime import datetime, timezone
import uuid


class User(BaseModel):
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4, description="Unique user identifier"
    )
    name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=2, max_length=50)
    ] = Field(..., description="Full name of the user (2–50 characters)")
    email: EmailStr = Field(..., description="Valid email address for the user")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(datetime.UTC).replace(tzinfo=timezone.utc),
        description="Timestamp when the user account was created",
    )
    is_active: bool = Field(
        default=True, description="Whether the user account is active"
    )

    class Config:
        from_attributes = True  # allows .from_orm() usage


class UserUpdate(BaseModel):
    """Schema for user updates - all fields optional except id"""

    id: uuid.UUID = Field(..., description="User ID to update")
    name: Optional[
        Annotated[
            str, StringConstraints(strip_whitespace=True, min_length=2, max_length=50)
        ]
    ] = Field(None, description="Full name of the user (2–50 characters)")
    email: Optional[EmailStr] = Field(
        None, description="Valid email address for the user"
    )
    is_active: Optional[bool] = Field(
        None, description="Whether the user account is active"
    )

    class Config:
        from_attributes = True
