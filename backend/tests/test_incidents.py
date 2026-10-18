from app.models import Activity


def start(client, incident_id):
    return client.patch(f"/api/incidents/{incident_id}", json={"status": "In Progress"})


def resolve(client, incident_id, note="Fixed it"):
    return client.post(f"/api/incidents/{incident_id}/resolve", json={"resolution_note": note})


# --- CRUD -------------------------------------------------------------------

def test_create_incident_defaults_to_open(client, make_incident):
    inc = make_incident()
    assert inc["status"] == "Open"
    assert inc["assignee"] is None
    assert inc["resolved_at"] is None and inc["resolution_note"] is None
    assert inc["created_at"].endswith("Z") and inc["created_at"] == inc["updated_at"]


def test_create_rejects_status_field_and_invalid_values(client):
    base = {"title": "x", "description": "y", "severity": "High"}
    res = client.post("/api/incidents", json={**base, "status": "Resolved"})
    assert res.status_code == 422
    res = client.post("/api/incidents", json={**base, "severity": "Urgent"})
    assert res.status_code == 422
    assert res.json()["errors"][0]["field"] == "severity"
    res = client.post("/api/incidents", json={**base, "title": "   "})
    assert res.status_code == 422


def test_get_update_list_and_delete(client, make_incident):
    inc = make_incident()
    assert client.get(f"/api/incidents/{inc['id']}").json()["title"] == "DB outage"

    res = client.patch(f"/api/incidents/{inc['id']}", json={"title": "DB outage (EU)", "severity": "Critical"})
    assert res.status_code == 200
    body = res.json()
    assert body["title"] == "DB outage (EU)" and body["severity"] == "Critical"
    assert body["updated_at"] >= inc["updated_at"]

    assert len(client.get("/api/incidents").json()) == 1

    assert client.delete(f"/api/incidents/{inc['id']}").status_code == 204
    assert client.get(f"/api/incidents/{inc['id']}").status_code == 404


def test_update_rejects_invalid_status_value_and_null_title(client, make_incident):
    inc = make_incident()
    assert client.patch(f"/api/incidents/{inc['id']}", json={"status": "Closed"}).status_code == 422
    assert client.patch(f"/api/incidents/{inc['id']}", json={"title": None}).status_code == 422


def test_missing_incident_returns_404(client):
    assert client.get("/api/incidents/999").status_code == 404
    assert client.patch("/api/incidents/999", json={"title": "x"}).status_code == 404
    assert client.delete("/api/incidents/999").status_code == 404
    assert resolve(client, 999).status_code == 404
    assert client.get("/api/incidents/999/activity").status_code == 404


# --- Workflow ---------------------------------------------------------------

def test_valid_workflow(client, make_incident):
    inc = make_incident()
    assert start(client, inc["id"]).json()["status"] == "In Progress"
    res = resolve(client, inc["id"], "Restarted the primary")
    assert res.status_code == 200
    assert res.json()["status"] == "Resolved"
    assert res.json()["resolution_note"] == "Restarted the primary"


def test_invalid_transitions(client, make_incident):
    inc = make_incident()
    # Open -> Resolved directly is not allowed
    res = resolve(client, inc["id"])
    assert res.status_code == 409
    assert "Open" in res.json()["detail"]
    res = client.patch(f"/api/incidents/{inc['id']}", json={"status": "Resolved"})
    assert res.status_code == 409

    start(client, inc["id"])
    # In Progress -> Open is not allowed
    res = client.patch(f"/api/incidents/{inc['id']}", json={"status": "Open"})
    assert res.status_code == 409

    resolve(client, inc["id"])
    # Resolved incidents cannot be reopened, edited or resolved again
    assert client.patch(f"/api/incidents/{inc['id']}", json={"status": "Open"}).status_code == 409
    assert client.patch(f"/api/incidents/{inc['id']}", json={"title": "new"}).status_code == 409
    assert resolve(client, inc["id"]).status_code == 409


def test_resolution_note_is_mandatory(client, make_incident):
    inc = make_incident()
    start(client, inc["id"])
    assert client.post(f"/api/incidents/{inc['id']}/resolve", json={}).status_code == 422
    assert resolve(client, inc["id"], "   ").status_code == 422
    assert client.get(f"/api/incidents/{inc['id']}").json()["status"] == "In Progress"


def test_resolution_timestamp_set_automatically(client, make_incident):
    inc = make_incident()
    started = start(client, inc["id"]).json()
    resolved = resolve(client, inc["id"]).json()
    assert resolved["resolved_at"] is not None
    assert resolved["resolved_at"] == resolved["updated_at"]
    assert resolved["resolved_at"] >= started["updated_at"] >= inc["created_at"]


# --- Assignment -------------------------------------------------------------

def test_assign_and_reassign_valid_members(client, make_member, make_incident):
    alice, bob = make_member("Alice"), make_member("Bob")
    inc = make_incident(assignee_id=alice["id"])
    assert inc["assignee"]["name"] == "Alice"

    res = client.patch(f"/api/incidents/{inc['id']}", json={"assignee_id": bob["id"]})
    assert res.status_code == 200 and res.json()["assignee_id"] == bob["id"]

    res = client.patch(f"/api/incidents/{inc['id']}", json={"assignee_id": None})
    assert res.status_code == 200 and res.json()["assignee"] is None


def test_assign_to_nonexistent_member_rejected(client, make_incident):
    res = client.post(
        "/api/incidents",
        json={"title": "x", "description": "y", "severity": "Low", "assignee_id": 42},
    )
    assert res.status_code == 422
    assert "does not exist" in res.json()["detail"]

    inc = make_incident()
    res = client.patch(f"/api/incidents/{inc['id']}", json={"assignee_id": 42})
    assert res.status_code == 422
    assert client.get(f"/api/incidents/{inc['id']}").json()["assignee_id"] is None


def test_team_members_create_list_and_validation(client, make_member):
    make_member("Bob")
    make_member("Alice")
    names = [m["name"] for m in client.get("/api/team-members").json()]
    assert names == ["Alice", "Bob"]
    dup = client.post("/api/team-members", json={"name": "Al", "email": "ALICE@example.com"})
    assert dup.status_code == 409
    bad = client.post("/api/team-members", json={"name": "X", "email": "not-an-email"})
    assert bad.status_code == 422


# --- Search & filtering -----------------------------------------------------

def test_combined_search_and_filters(client, make_member, make_incident):
    alice, bob = make_member("Alice"), make_member("Bob")
    target = make_incident(title="Login page down", description="500s", severity="Critical",
                           assignee_id=alice["id"])
    make_incident(title="Login slow", description="latency", severity="Low", assignee_id=alice["id"])
    make_incident(title="Payments failing", description="login token expired", severity="Critical",
                  assignee_id=bob["id"])
    other = make_incident(title="Disk full", description="logs", severity="Critical", assignee_id=alice["id"])
    start(client, target["id"])

    def ids(**params):
        res = client.get("/api/incidents", params=params)
        assert res.status_code == 200
        return {i["id"] for i in res.json()}

    assert len(ids(q="login")) == 3  # title or description, case-insensitive
    assert ids(q="login", severity="Critical", assignee_id=alice["id"]) == {target["id"]}
    assert ids(q="login", status="In Progress") == {target["id"]}
    assert ids(severity="Critical", status="Open", assignee_id=alice["id"]) == {other["id"]}
    assert ids(q="nomatch") == set()
    assert client.get("/api/incidents", params={"status": "Closed"}).status_code == 422
    assert client.get("/api/incidents", params={"severity": "Urgent"}).status_code == 422


# --- Dashboard --------------------------------------------------------------

def test_dashboard_empty(client):
    data = client.get("/api/dashboard").json()
    assert data["total"] == 0 and data["avg_resolution_hours"] is None
    assert data["severity_breakdown"] == {"Low": 0, "Medium": 0, "High": 0, "Critical": 0}
    assert data["recent_incidents"] == []


def test_dashboard_calculations(client, db, make_incident):
    from datetime import timedelta

    from app.models import Incident

    a = make_incident(severity="Critical")
    b = make_incident(severity="Critical")
    c = make_incident(severity="Low")
    make_incident(severity="High")
    for inc, hours in ((a, 2), (c, 4)):
        start(client, inc["id"])
        resolve(client, inc["id"])
        row = db.get(Incident, inc["id"])
        row.resolved_at = row.created_at + timedelta(hours=hours)
        db.commit()
    start(client, b["id"])

    data = client.get("/api/dashboard").json()
    assert data["total"] == 4
    assert data["open"] == 1
    assert data["in_progress"] == 1
    assert data["resolved"] == 2
    assert data["critical_unresolved"] == 1
    assert data["avg_resolution_hours"] == 3.0
    assert data["severity_breakdown"] == {"Low": 1, "Medium": 0, "High": 1, "Critical": 2}
    assert len(data["recent_incidents"]) == 4


# --- Activity history -------------------------------------------------------

def test_activity_history_generated_in_order(client, make_member, make_incident):
    alice, bob = make_member("Alice"), make_member("Bob")
    inc = make_incident(assignee_id=alice["id"])
    client.patch(f"/api/incidents/{inc['id']}", json={"assignee_id": bob["id"]})
    client.patch(f"/api/incidents/{inc['id']}", json={"title": "Renamed"})  # no activity entry
    start(client, inc["id"])
    resolve(client, inc["id"], "Rolled back")

    entries = client.get(f"/api/incidents/{inc['id']}/activity").json()
    assert [e["action"] for e in entries] == ["created", "assigned", "reassigned", "status_changed", "resolved"]
    assert entries[2]["description"] == "Reassigned from Alice to Bob"
    assert entries[3]["description"] == "Status changed from Open to In Progress"
    assert all(e["incident_id"] == inc["id"] and e["created_at"] for e in entries)
    timestamps = [e["created_at"] for e in entries]
    assert timestamps == sorted(timestamps)


def test_failed_operations_do_not_log_activity(client, make_incident):
    inc = make_incident()
    resolve(client, inc["id"])  # invalid: Open -> Resolved
    client.patch(f"/api/incidents/{inc['id']}", json={"assignee_id": 99})
    assert len(client.get(f"/api/incidents/{inc['id']}/activity").json()) == 1


# --- Deletion constraints ---------------------------------------------------

def test_cannot_delete_resolved_incident(client, make_incident):
    inc = make_incident()
    start(client, inc["id"])
    resolve(client, inc["id"])
    res = client.delete(f"/api/incidents/{inc['id']}")
    assert res.status_code == 409
    assert client.get(f"/api/incidents/{inc['id']}").status_code == 200


def test_delete_removes_activity_records(client, db, make_member, make_incident):
    member = make_member()
    inc = make_incident(assignee_id=member["id"])
    start(client, inc["id"])
    assert db.query(Activity).filter_by(incident_id=inc["id"]).count() == 3
    assert client.delete(f"/api/incidents/{inc['id']}").status_code == 204
    assert db.query(Activity).count() == 0
