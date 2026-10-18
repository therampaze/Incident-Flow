from datetime import datetime, timezone
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, StringConstraints

from .models import ActivityAction, Severity, Status

UTCDateTime = Annotated[
    datetime,
    PlainSerializer(
        lambda d: d.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
        return_type=str,
    ),
]

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Description = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)]


class StrictInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TeamMemberCreate(StrictInput):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    email: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True, to_lower=True, max_length=254,
            pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
        ),
    ]


class TeamMemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str


class IncidentCreate(StrictInput):
    title: Title
    description: Description
    severity: Severity
    assignee_id: int | None = None


class IncidentUpdate(StrictInput):
    title: Title | None = None
    description: Description | None = None
    severity: Severity | None = None
    status: Status | None = None
    assignee_id: int | None = None


class ResolveRequest(StrictInput):
    resolution_note: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]


class IncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    severity: Severity
    status: Status
    assignee_id: int | None
    assignee: TeamMemberOut | None
    created_at: UTCDateTime
    updated_at: UTCDateTime
    resolved_at: UTCDateTime | None
    resolution_note: str | None


class ActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_id: int
    action: ActivityAction
    description: str
    created_at: UTCDateTime


class DashboardOut(BaseModel):
    total: int
    open: int
    in_progress: int
    critical_unresolved: int
    resolved: int
    avg_resolution_hours: float | None
    severity_breakdown: dict[Severity, int] = Field(
        description="Incident count per severity, including resolved incidents"
    )
    recent_incidents: list[IncidentOut]
