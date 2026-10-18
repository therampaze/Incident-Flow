import { useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api.js';
import { EmptyState, ErrorMessage, Loading } from '../components.jsx';
import { useAsync } from '../useAsync.js';

const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

export default function Team() {
  const members = useAsync(() => api.listMembers(), []);
  const [values, setValues] = useState({ name: '', email: '' });
  const [errors, setErrors] = useState({});
  const [submitError, setSubmitError] = useState(null);
  const [saving, setSaving] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault();
    const next = {};
    if (!values.name.trim()) next.name = 'Name is required.';
    if (!EMAIL_RE.test(values.email.trim())) next.email = 'Enter a valid email address.';
    setErrors(next);
    setSubmitError(null);
    if (Object.keys(next).length) return;
    setSaving(true);
    try {
      await api.createMember({ name: values.name.trim(), email: values.email.trim() });
      setValues({ name: '', email: '' });
      members.reload();
    } catch (err) {
      setErrors(Object.fromEntries(err.fieldErrors.map((f) => [f.field, f.message])));
      setSubmitError(err);
    } finally {
      setSaving(false);
    }
  };

  const onChange = (e) => setValues((v) => ({ ...v, [e.target.name]: e.target.value }));

  return (
    <>
      <div className="page-header"><h1>Team members</h1></div>
      <div className="grid-2">
        <section className="card">
          {members.loading ? (
            <Loading />
          ) : members.error ? (
            <ErrorMessage error={members.error} onRetry={members.reload} />
          ) : members.data.length === 0 ? (
            <EmptyState>No team members yet. Add one to start assigning incidents.</EmptyState>
          ) : (
            <table>
              <thead><tr><th>Name</th><th>Email</th><th /></tr></thead>
              <tbody>
                {members.data.map((m) => (
                  <tr key={m.id}>
                    <td>{m.name}</td>
                    <td>{m.email}</td>
                    <td><Link to={`/incidents?assignee_id=${m.id}`}>Incidents</Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
        <form className="card form" onSubmit={onSubmit} noValidate>
          <h2>Add member</h2>
          <ErrorMessage error={submitError} />
          <label htmlFor="name">Name</label>
          <input id="name" name="name" value={values.name} onChange={onChange} aria-invalid={Boolean(errors.name)} />
          {errors.name && <div className="field-error">{errors.name}</div>}
          <label htmlFor="email">Email</label>
          <input id="email" name="email" type="email" value={values.email} onChange={onChange}
            aria-invalid={Boolean(errors.email)} />
          {errors.email && <div className="field-error">{errors.email}</div>}
          <div className="actions">
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? 'Adding…' : 'Add member'}
            </button>
          </div>
        </form>
      </div>
    </>
  );
}
