import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { api, formatDate } from '../api.js';
import { EmptyState, ErrorMessage, Loading, SeverityBadge, StatusBadge } from '../components.jsx';
import { useAsync } from '../useAsync.js';

export default function IncidentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const incident = useAsync(() => api.getIncident(id), [id]);
  const activity = useAsync(() => api.getActivity(id), [id]);
  const [note, setNote] = useState('');
  const [noteError, setNoteError] = useState('');
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState(null);

  const runAction = async (fn) => {
    setBusy(true);
    setActionError(null);
    try {
      const updated = await fn();
      if (updated) incident.setData(updated);
      activity.reload();
      return true;
    } catch (err) {
      setActionError(err);
      return false;
    } finally {
      setBusy(false);
    }
  };

  const handleResolve = async (e) => {
    e.preventDefault();
    if (!note.trim()) {
      setNoteError('A resolution note is required.');
      return;
    }
    setNoteError('');
    if (await runAction(() => api.resolveIncident(id, note.trim()))) setNote('');
  };

  const handleDelete = async () => {
    if (!window.confirm(`Delete incident #${id}? This cannot be undone.`)) return;
    setBusy(true);
    setActionError(null);
    try {
      await api.deleteIncident(id);
      navigate('/incidents');
    } catch (err) {
      setActionError(err);
      setBusy(false);
    }
  };

  if (incident.loading && !incident.data) return <Loading />;
  if (incident.error) return <ErrorMessage error={incident.error} onRetry={incident.reload} />;

  const inc = incident.data;
  const resolved = inc.status === 'Resolved';

  return (
    <>
      <div className="page-header">
        <h1>#{inc.id} {inc.title}</h1>
        {!resolved && (
          <div className="actions">
            <Link className="btn" to={`/incidents/${inc.id}/edit`}>Edit</Link>
            <button type="button" className="btn btn-danger" disabled={busy} onClick={handleDelete}>
              Delete
            </button>
          </div>
        )}
      </div>
      <ErrorMessage error={actionError} />

      <div className="grid-2">
        <section className="card">
          <dl className="details">
            <dt>Status</dt><dd><StatusBadge value={inc.status} /></dd>
            <dt>Severity</dt><dd><SeverityBadge value={inc.severity} /></dd>
            <dt>Assignee</dt>
            <dd>{inc.assignee ? `${inc.assignee.name} (${inc.assignee.email})` : <span className="muted">Unassigned</span>}</dd>
            <dt>Created</dt><dd>{formatDate(inc.created_at)}</dd>
            <dt>Last updated</dt><dd>{formatDate(inc.updated_at)}</dd>
            {resolved && (
              <>
                <dt>Resolved</dt><dd>{formatDate(inc.resolved_at)}</dd>
                <dt>Resolution note</dt><dd className="prewrap">{inc.resolution_note}</dd>
              </>
            )}
          </dl>
          <h2>Description</h2>
          <p className="prewrap">{inc.description}</p>

          {inc.status === 'Open' && (
            <button
              type="button"
              className="btn btn-primary"
              disabled={busy}
              onClick={() => runAction(() => api.updateIncident(id, { status: 'In Progress' }))}
            >
              Start progress
            </button>
          )}
          {inc.status === 'In Progress' && (
            <form className="resolve-form" onSubmit={handleResolve} noValidate>
              <label htmlFor="resolution-note">Resolution note</label>
              <textarea
                id="resolution-note"
                rows={3}
                value={note}
                onChange={(e) => setNote(e.target.value)}
                aria-invalid={Boolean(noteError)}
              />
              {noteError && <div className="field-error">{noteError}</div>}
              <button type="submit" className="btn btn-primary" disabled={busy}>Resolve incident</button>
            </form>
          )}
        </section>

        <section className="card">
          <h2>Activity</h2>
          {activity.loading && !activity.data ? (
            <Loading />
          ) : activity.error ? (
            <ErrorMessage error={activity.error} onRetry={activity.reload} />
          ) : activity.data.length === 0 ? (
            <EmptyState>No activity recorded.</EmptyState>
          ) : (
            <ol className="timeline">
              {activity.data.map((a) => (
                <li key={a.id}>
                  <div>{a.description}</div>
                  <small className="muted">{formatDate(a.created_at)} · {a.action.replace('_', ' ')}</small>
                </li>
              ))}
            </ol>
          )}
        </section>
      </div>
    </>
  );
}
