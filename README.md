# IncidentFlow

A small incident management app for engineering teams: report, assign, track and resolve incidents.

- **Backend:** Python, FastAPI, SQLAlchemy, SQLite, Pydantic, Pytest — `backend/`
- **Frontend:** React, Vite, React Router, Vitest + Testing Library — `frontend/`

## Prerequisites

- Python 3.10+
- Node.js 18+ and npm

## Setup and startup

### Backend (http://127.0.0.1:8000)

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload --port 8000
```

Data is stored in `backend/incidentflow.db` (created on first start, git-ignored) and persists
across restarts. Set `INCIDENTFLOW_DATABASE_URL` to use a different SQLAlchemy SQLite URL.
Interactive API docs: http://127.0.0.1:8000/docs

### Frontend (http://localhost:5173)

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` to the backend on port 8000, so start the backend first.

### Optional sample data

Sample data is never inserted automatically. To populate an **empty** database with two team
members and four incidents in different states:

```bash
cd backend
.venv/bin/python seed.py
```

The script does nothing if the database already has incidents or team members.
To start over, stop the backend and delete `backend/incidentflow.db`.

## Tests

```bash
# Backend (uses a temporary SQLite database; the dev database is never touched)
cd backend && .venv/bin/pytest

# Frontend (jsdom, API calls mocked)
cd frontend && npm test
```

## Business rules (enforced by the backend)

- New incidents always start as `Open`; `status` cannot be supplied on create.
- Allowed transitions: `Open → In Progress → Resolved`. Anything else returns **409**.
- Resolving requires `POST /api/incidents/{id}/resolve` with a non-empty `resolution_note`
  (missing/blank → **422**). `resolved_at` and `updated_at` are set automatically.
- Resolved incidents cannot be edited, reopened or deleted (**409**).
- `updated_at` changes whenever a field, assignee or status actually changes.
- Severity must be `Low | Medium | High | Critical`; status must be `Open | In Progress | Resolved` (**422** otherwise).
- Assignees must be existing team members (**422** otherwise). Team member emails are unique (**409**).
- Activity entries are recorded on create, assign, reassign, unassign, status change and resolve.
  Deleting an incident deletes its activity entries.

## API

All endpoints are under `/api`. Errors share one shape:

```json
{ "detail": "Invalid status transition from 'Open' to 'Resolved'" }
{ "detail": "Validation failed", "errors": [{ "field": "severity", "message": "..." }] }
```

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/dashboard` | Totals, open / in-progress / critical-unresolved / resolved counts, average resolution time (hours), severity breakdown, 5 most recent incidents |
| GET | `/api/incidents` | List incidents, newest first. Query params (combinable): `q` (title/description search), `status`, `severity`, `assignee_id` |
| POST | `/api/incidents` | Create: `{title, description, severity, assignee_id?}` → 201 |
| GET | `/api/incidents/{id}` | Retrieve one incident |
| PATCH | `/api/incidents/{id}` | Partial update of `title`, `description`, `severity`, `assignee_id` (null to unassign), `status` (`In Progress` only) |
| POST | `/api/incidents/{id}/resolve` | Resolve: `{resolution_note}` |
| DELETE | `/api/incidents/{id}` | Delete an unresolved incident → 204 |
| GET | `/api/incidents/{id}/activity` | Activity history, oldest first |
| GET | `/api/team-members` | List team members |
| POST | `/api/team-members` | Create: `{name, email}` → 201 |
| GET | `/api/health` | Health check |

## Known limitations

- No authentication, permissions, or team member edit/delete (out of scope for the MVP).
- Schema is created with `create_all` on startup; there are no migrations.
- Search uses SQL `LIKE`, which is case-insensitive for ASCII only in SQLite.
