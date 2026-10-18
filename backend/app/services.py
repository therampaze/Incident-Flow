from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from .models import Activity, ActivityAction, Incident, Status, TeamMember, utcnow
from .schemas import IncidentCreate, IncidentUpdate

ALLOWED_TRANSITIONS = {
    Status.OPEN: {Status.IN_PROGRESS},
    Status.IN_PROGRESS: {Status.RESOLVED},
    Status.RESOLVED: set(),
}


def get_incident_or_404(db: Session, incident_id: int) -> Incident:
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Incident {incident_id} not found")
    return incident


def _get_member_or_422(db: Session, member_id: int) -> TeamMember:
    member = db.get(TeamMember, member_id)
    if member is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, f"Team member {member_id} does not exist"
        )
    return member


def _ensure_editable(incident: Incident) -> None:
    if incident.status == Status.RESOLVED:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Resolved incidents cannot be modified"
        )


def _ensure_transition(incident: Incident, new_status: Status) -> None:
    if new_status not in ALLOWED_TRANSITIONS[incident.status]:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Invalid status transition from '{incident.status.value}' to '{new_status.value}'",
        )


def _log(incident: Incident, action: ActivityAction, description: str) -> None:
    incident.activities.append(Activity(action=action, description=description, created_at=utcnow()))


def _apply_assignee(db: Session, incident: Incident, assignee_id: int | None) -> bool:
    if assignee_id == incident.assignee_id:
        return False
    previous = incident.assignee
    if assignee_id is None:
        incident.assignee = None
        _log(incident, ActivityAction.UNASSIGNED, f"Unassigned from {previous.name}")
        return True
    member = _get_member_or_422(db, assignee_id)
    incident.assignee = member
    if previous is None:
        _log(incident, ActivityAction.ASSIGNED, f"Assigned to {member.name}")
    else:
        _log(incident, ActivityAction.REASSIGNED, f"Reassigned from {previous.name} to {member.name}")
    return True


def create_incident(db: Session, data: IncidentCreate) -> Incident:
    now = utcnow()
    incident = Incident(
        title=data.title, description=data.description, severity=data.severity,
        status=Status.OPEN, created_at=now, updated_at=now,
    )
    _log(incident, ActivityAction.CREATED, f"Incident created with {data.severity.value} severity")
    if data.assignee_id is not None:
        _apply_assignee(db, incident, data.assignee_id)
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


def update_incident(db: Session, incident: Incident, data: IncidentUpdate) -> Incident:
    _ensure_editable(incident)
    fields = data.model_fields_set
    for name in ("title", "description", "severity"):
        if name in fields and getattr(data, name) is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"'{name}' cannot be null")

    if "status" in fields and data.status is not None and data.status != incident.status:
        if data.status == Status.RESOLVED:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "Use POST /api/incidents/{id}/resolve with a resolution note to resolve an incident",
            )
        _ensure_transition(incident, data.status)

    changed = False
    for name in ("title", "description", "severity"):
        value = getattr(data, name)
        if name in fields and value != getattr(incident, name):
            setattr(incident, name, value)
            changed = True

    if "assignee_id" in fields:
        changed = _apply_assignee(db, incident, data.assignee_id) or changed

    if "status" in fields and data.status is not None and data.status != incident.status:
        _log(incident, ActivityAction.STATUS_CHANGED,
             f"Status changed from {incident.status.value} to {data.status.value}")
        incident.status = data.status
        changed = True

    if changed:
        incident.updated_at = utcnow()
        db.commit()
        db.refresh(incident)
    return incident


def resolve_incident(db: Session, incident: Incident, note: str) -> Incident:
    _ensure_transition(incident, Status.RESOLVED)
    now = utcnow()
    incident.status = Status.RESOLVED
    incident.resolution_note = note
    incident.resolved_at = now
    incident.updated_at = now
    _log(incident, ActivityAction.RESOLVED, f"Resolved: {note[:200]}")
    db.commit()
    db.refresh(incident)
    return incident


def delete_incident(db: Session, incident: Incident) -> None:
    if incident.status == Status.RESOLVED:
        raise HTTPException(status.HTTP_409_CONFLICT, "Resolved incidents cannot be deleted")
    db.delete(incident)
    db.commit()
