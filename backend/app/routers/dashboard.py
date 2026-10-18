from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Incident, Severity, Status
from ..schemas import DashboardOut

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

RECENT_LIMIT = 5


@router.get("", response_model=DashboardOut)
def get_dashboard(db: Session = Depends(get_db)):
    by_status = dict(db.execute(select(Incident.status, func.count()).group_by(Incident.status)).all())
    by_severity = dict(db.execute(select(Incident.severity, func.count()).group_by(Incident.severity)).all())
    critical_unresolved = db.scalar(
        select(func.count()).where(Incident.severity == Severity.CRITICAL, Incident.status != Status.RESOLVED)
    )
    resolved_rows = db.execute(
        select(Incident.created_at, Incident.resolved_at).where(
            Incident.status == Status.RESOLVED, Incident.resolved_at.is_not(None)
        )
    ).all()
    avg_hours = None
    if resolved_rows:
        total_seconds = sum((r.resolved_at - r.created_at).total_seconds() for r in resolved_rows)
        avg_hours = round(total_seconds / len(resolved_rows) / 3600, 2)
    recent = db.scalars(
        select(Incident).order_by(Incident.created_at.desc(), Incident.id.desc()).limit(RECENT_LIMIT)
    ).unique().all()

    return DashboardOut(
        total=sum(by_status.values()),
        open=by_status.get(Status.OPEN, 0),
        in_progress=by_status.get(Status.IN_PROGRESS, 0),
        critical_unresolved=critical_unresolved,
        resolved=by_status.get(Status.RESOLVED, 0),
        avg_resolution_hours=avg_hours,
        severity_breakdown={s: by_severity.get(s, 0) for s in Severity},
        recent_incidents=recent,
    )
