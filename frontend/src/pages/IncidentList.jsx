import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { api, formatDate, SEVERITIES, STATUSES } from '../api.js';
import { EmptyState, ErrorMessage, Loading, SeverityBadge, StatusBadge } from '../components.jsx';
import { useAsync } from '../useAsync.js';

const FILTER_KEYS = ['q', 'status', 'severity', 'assignee_id'];

export default function IncidentList() {
  const [searchParams, setSearchParams] = useSearchParams();
  const filters = Object.fromEntries(FILTER_KEYS.map((k) => [k, searchParams.get(k) || '']));
  const [search, setSearch] = useState(filters.q);
  const members = useAsync(() => api.listMembers(), []);
  const incidents = useAsync(
    () => api.listIncidents(filters),
    [filters.q, filters.status, filters.severity, filters.assignee_id],
  );

  const setFilter = (key, value) => {
    const next = new URLSearchParams(searchParams);
    if (value) next.set(key, value);
    else next.delete(key);
    setSearchParams(next, { replace: true });
  };

  useEffect(() => {
    if (search === filters.q) return undefined;
    const timer = setTimeout(() => setFilter('q', search.trim()), 300);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search]);

  const hasFilters = FILTER_KEYS.some((k) => filters[k]);

  return (
    <>
      <div className="page-header">
        <h1>Incidents</h1>
        <Link className="btn btn-primary" to="/incidents/new">Report incident</Link>
      </div>
      <div className="filters card">
        <input
          type="search"
          placeholder="Search title or description…"
          aria-label="Search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select aria-label="Status" value={filters.status} onChange={(e) => setFilter('status', e.target.value)}>
          <option value="">All statuses</option>
          {STATUSES.map((s) => <option key={s}>{s}</option>)}
        </select>
        <select aria-label="Severity" value={filters.severity} onChange={(e) => setFilter('severity', e.target.value)}>
          <option value="">All severities</option>
          {SEVERITIES.map((s) => <option key={s}>{s}</option>)}
        </select>
        <select
          aria-label="Assignee"
          value={filters.assignee_id}
          onChange={(e) => setFilter('assignee_id', e.target.value)}
        >
          <option value="">All assignees</option>
          {(members.data || []).map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
        </select>
        {hasFilters && (
          <button
            type="button"
            className="btn"
            onClick={() => {
              setSearch('');
              setSearchParams({}, { replace: true });
            }}
          >
            Clear
          </button>
        )}
      </div>

      {incidents.loading ? (
        <Loading />
      ) : incidents.error ? (
        <ErrorMessage error={incidents.error} onRetry={incidents.reload} />
      ) : incidents.data.length === 0 ? (
        <EmptyState>
          {hasFilters ? 'No incidents match the current filters.' : 'No incidents yet. Report the first one.'}
        </EmptyState>
      ) : (
        <div className="card table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Title</th>
                <th>Severity</th>
                <th>Status</th>
                <th>Assignee</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {incidents.data.map((i) => (
                <tr key={i.id}>
                  <td>#{i.id}</td>
                  <td><Link to={`/incidents/${i.id}`}>{i.title}</Link></td>
                  <td><SeverityBadge value={i.severity} /></td>
                  <td><StatusBadge value={i.status} /></td>
                  <td>{i.assignee?.name || <span className="muted">Unassigned</span>}</td>
                  <td>{formatDate(i.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
