import { Link } from 'react-router-dom';
import { api, formatDate, SEVERITIES } from '../api.js';
import { EmptyState, ErrorMessage, Loading, SeverityBadge, StatusBadge } from '../components.jsx';
import { useAsync } from '../useAsync.js';

function formatHours(hours) {
  if (hours === null || hours === undefined) return '—';
  if (hours < 1) return `${Math.round(hours * 60)} min`;
  if (hours < 48) return `${hours.toFixed(1)} h`;
  return `${(hours / 24).toFixed(1)} d`;
}

export default function Dashboard() {
  const { data, error, loading, reload } = useAsync(() => api.dashboard(), []);

  if (loading) return <Loading />;
  if (error) return <ErrorMessage error={error} onRetry={reload} />;

  const stats = [
    ['Total incidents', data.total],
    ['Open', data.open],
    ['In progress', data.in_progress],
    ['Critical (unresolved)', data.critical_unresolved],
    ['Resolved', data.resolved],
    ['Avg. resolution time', formatHours(data.avg_resolution_hours)],
  ];
  const maxSeverity = Math.max(1, ...Object.values(data.severity_breakdown));

  return (
    <>
      <div className="page-header">
        <h1>Dashboard</h1>
        <Link className="btn btn-primary" to="/incidents/new">Report incident</Link>
      </div>
      <section className="stats">
        {stats.map(([label, value]) => (
          <div className="card stat" key={label}>
            <div className="stat-value">{value}</div>
            <div className="stat-label">{label}</div>
          </div>
        ))}
      </section>
      <div className="grid-2">
        <section className="card">
          <h2>By severity</h2>
          {SEVERITIES.map((sev) => {
            const count = data.severity_breakdown[sev] ?? 0;
            return (
              <div className="bar-row" key={sev}>
                <span className="bar-label">{sev}</span>
                <div className="bar-track">
                  <div className={`bar sev-${sev.toLowerCase()}`} style={{ width: `${(count / maxSeverity) * 100}%` }} />
                </div>
                <span className="bar-count">{count}</span>
              </div>
            );
          })}
        </section>
        <section className="card">
          <h2>Recent incidents</h2>
          {data.recent_incidents.length === 0 ? (
            <EmptyState>No incidents reported yet.</EmptyState>
          ) : (
            <ul className="recent">
              {data.recent_incidents.map((i) => (
                <li key={i.id}>
                  <Link to={`/incidents/${i.id}`}>#{i.id} {i.title}</Link>
                  <span className="recent-meta">
                    <SeverityBadge value={i.severity} /> <StatusBadge value={i.status} />
                    <small>{formatDate(i.created_at)}</small>
                  </span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </>
  );
}
