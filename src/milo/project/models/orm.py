import uuid
from datetime import date, datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Text,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Table,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from milo.core.database.base import Base


# Enum for project status
class ProjectStatus(str, enum.Enum):
    Active = "Active"
    Completed = "Completed"
    OnHold = "On Hold"


# Association table for many-to-many Project <-> User relationship
project_members = Table(
    "project_members",
    Base.metadata,
    Column(
        "project_id", UUID(as_uuid=True), ForeignKey("projects.id"), primary_key=True
    ),
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True),
)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[date] = mapped_column(Date, default=date.today)
    target_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus), default=ProjectStatus.Active, nullable=False
    )

    # Owner relationship (many projects → one user)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    owner = relationship("User", back_populates="owned_projects")

    # Members relationship (many-to-many)
    members = relationship(
        "User", secondary=project_members, back_populates="projects", lazy="joined"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(datetime.UTC).replace(tzinfo=timezone.utc),
    )
