import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Severity(str, enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class Status(str, enum.Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"


class ActivityAction(str, enum.Enum):
    CREATED = "created"
    ASSIGNED = "assigned"
    REASSIGNED = "reassigned"
    UNASSIGNED = "unassigned"
    STATUS_CHANGED = "status_changed"
    RESOLVED = "resolved"


def _enum_column(enum_cls):
    return Enum(enum_cls, values_callable=lambda e: [m.value for m in e], native_enum=False,
                validate_strings=True, length=20)


class TeamMember(Base):
    __tablename__ = "team_members"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(254), unique=True)


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    severity: Mapped[Severity] = mapped_column(_enum_column(Severity))
    status: Mapped[Status] = mapped_column(_enum_column(Status), default=Status.OPEN)
    assignee_id: Mapped[int | None] = mapped_column(
        ForeignKey("team_members.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    assignee: Mapped[TeamMember | None] = relationship(lazy="joined")
    activities: Mapped[list["Activity"]] = relationship(
        back_populates="incident",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Activity.id",
    )


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    incident_id: Mapped[int] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"), index=True
    )
    action: Mapped[ActivityAction] = mapped_column(_enum_column(ActivityAction))
    description: Mapped[str] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    incident: Mapped[Incident] = relationship(back_populates="activities")
