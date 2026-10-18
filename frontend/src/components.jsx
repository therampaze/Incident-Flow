export function Loading({ label = 'Loading…' }) {
  return (
    <div className="loading" role="status">
      <span className="spinner" aria-hidden="true" /> {label}
    </div>
  );
}

export function ErrorMessage({ error, onRetry }) {
  if (!error) return null;
  return (
    <div className="alert" role="alert">
      {error.message || String(error)}
      {onRetry && (
        <button type="button" className="btn btn-small" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}

export function EmptyState({ children }) {
  return <div className="empty">{children}</div>;
}

const slug = (value) => value.toLowerCase().replace(/\s+/g, '-');

export function SeverityBadge({ value }) {
  return <span className={`badge sev-${slug(value)}`}>{value}</span>;
}

export function StatusBadge({ value }) {
  return <span className={`badge status-${slug(value)}`}>{value}</span>;
}
