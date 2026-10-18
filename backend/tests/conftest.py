import os
import tempfile
from pathlib import Path

_TMP_DIR = tempfile.mkdtemp(prefix="incidentflow-tests-")
os.environ["INCIDENTFLOW_DATABASE_URL"] = f"sqlite:///{Path(_TMP_DIR) / 'test.db'}"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def make_member(client):
    def _make(name="Alice", email=None):
        email = email or f"{name.lower()}@example.com"
        res = client.post("/api/team-members", json={"name": name, "email": email})
        assert res.status_code == 201, res.text
        return res.json()

    return _make


@pytest.fixture
def make_incident(client):
    def _make(**overrides):
        payload = {"title": "DB outage", "description": "Primary DB unreachable", "severity": "High"}
        payload.update(overrides)
        res = client.post("/api/incidents", json=payload)
        assert res.status_code == 201, res.text
        return res.json()

    return _make
