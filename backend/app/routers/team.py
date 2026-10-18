from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import TeamMember
from ..schemas import TeamMemberCreate, TeamMemberOut

router = APIRouter(prefix="/api/team-members", tags=["team"])


@router.get("", response_model=list[TeamMemberOut])
def list_members(db: Session = Depends(get_db)):
    return db.scalars(select(TeamMember).order_by(TeamMember.name, TeamMember.id)).all()


@router.post("", response_model=TeamMemberOut, status_code=status.HTTP_201_CREATED)
def create_member(data: TeamMemberCreate, db: Session = Depends(get_db)):
    if db.scalar(select(TeamMember).where(TeamMember.email == data.email)):
        raise HTTPException(status.HTTP_409_CONFLICT, f"A team member with email {data.email} already exists")
    member = TeamMember(name=data.name, email=data.email)
    db.add(member)
    db.commit()
    db.refresh(member)
    return member
