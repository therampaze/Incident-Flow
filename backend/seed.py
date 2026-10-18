"""Populate the development database with sample data.

Usage (from the backend directory):  .venv/bin/python seed.py
Runs only when the database is empty, so it never touches real data.
Sample data is never inserted automatically.
"""
from sqlalchemy import func, select

from app import services
from app.database import Base, SessionLocal, engine
from app.models import Incident, Severity, Status, TeamMember
from app.schemas import IncidentCreate, IncidentUpdate


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.scalar(select(func.count()).select_from(Incident)) or db.scalar(
            select(func.count()).select_from(TeamMember)
        ):
            print("Database already contains data; skipping seed.")
            return

        alice = TeamMember(name="Alice Johnson", email="alice@example.com")
        bob = TeamMember(name="Bob Smith", email="bob@example.com")
        db.add_all([alice, bob])
        db.commit()

        samples = [
            ("Checkout API returning 500s", "Spike of errors on /checkout since 09:00.", Severity.CRITICAL, alice.id),
            ("Login page slow", "p95 latency above 3s for the login page.", Severity.MEDIUM, bob.id),
            ("Typo on pricing page", "'Anual' should read 'Annual'.", Severity.LOW, None),
            ("Nightly backup failed", "Backup job exited with code 1.", Severity.HIGH, alice.id),
        ]
        incidents = [
            services.create_incident(db, IncidentCreate(title=t, description=d, severity=s, assignee_id=a))
            for t, d, s, a in samples
        ]
        services.update_incident(db, incidents[1], IncidentUpdate(status=Status.IN_PROGRESS))
        services.update_incident(db, incidents[3], IncidentUpdate(status=Status.IN_PROGRESS))
        services.resolve_incident(db, incidents[3], "Freed disk space on the backup volume and re-ran the job.")
        print(f"Seeded 2 team members and {len(incidents)} incidents.")


if __name__ == "__main__":
    seed()
