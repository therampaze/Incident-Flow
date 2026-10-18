from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from .. import services
from ..database import get_db
from ..models import Activity, Incident, Severity, Status
from ..schemas import ActivityOut, IncidentCreate, IncidentOut, IncidentUpdate, ResolveRequest

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


@router.get("", response_model=list[IncidentOut])
def list_incidents(
    q: str | None = Query(None, description="Search in title or description"),
    status_: Status | None = Query(None, alias="status"),
    severity: Severity | None = None,
    assignee_id: int | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(Incident)
    if q and q.strip():
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(or_(Incident.title.ilike(pattern), Incident.description.ilike(pattern)))
    if status_ is not None:
        stmt = stmt.where(Incident.status == status_)
    if severity is not None:
        stmt = stmt.where(Incident.severity == severity)
    if assignee_id is not None:
        stmt = stmt.where(Incident.assignee_id == assignee_id)
    stmt = stmt.order_by(Incident.created_at.desc(), Incident.id.desc())
    return db.scalars(stmt).unique().all()


@router.post("", response_model=IncidentOut, status_code=status.HTTP_201_CREATED)
def create_incident(data: IncidentCreate, db: Session = Depends(get_db)):
    return services.create_incident(db, data)


@router.get("/{incident_id}", response_model=IncidentOut)
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    return services.get_incident_or_404(db, incident_id)


@router.patch("/{incident_id}", response_model=IncidentOut)
def update_incident(incident_id: int, data: IncidentUpdate, db: Session = Depends(get_db)):
    incident = services.get_incident_or_404(db, incident_id)
    return services.update_incident(db, incident, data)


@router.post("/{incident_id}/resolve", response_model=IncidentOut)
def resolve_incident(incident_id: int, data: ResolveRequest, db: Session = Depends(get_db)):
    incident = services.get_incident_or_404(db, incident_id)
    return services.resolve_incident(db, incident, data.resolution_note)


@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_incident(incident_id: int, db: Session = Depends(get_db)):
    incident = services.get_incident_or_404(db, incident_id)
    services.delete_incident(db, incident)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{incident_id}/activity", response_model=list[ActivityOut])
def get_activity(incident_id: int, db: Session = Depends(get_db)):
    services.get_incident_or_404(db, incident_id)
    stmt = (
        select(Activity)
        .where(Activity.incident_id == incident_id)
        .order_by(Activity.created_at, Activity.id)
    )
    return db.scalars(stmt).all()
