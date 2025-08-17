from pydantic import BaseModel, EmailStr
from uuid import UUID


class UserUpdate(BaseModel):
    """Schema for user update requests"""

    id: UUID
    name: str | None = None
    email: EmailStr | None = None
    is_active: bool | None = None
