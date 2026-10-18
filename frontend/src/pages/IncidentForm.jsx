import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { api, SEVERITIES } from '../api.js';
import { ErrorMessage, Loading } from '../components.jsx';
import { useAsync } from '../useAsync.js';

const EMPTY = { title: '', description: '', severity: '', assignee_id: '' };

export function validateIncident(values) {
  const errors = {};
  if (!values.title.trim()) errors.title = 'Title is required.';
  else if (values.title.trim().length > 200) errors.title = 'Title must be at most 200 characters.';
  if (!values.description.trim()) errors.description = 'Description is required.';
  if (!SEVERITIES.includes(values.severity)) errors.severity = 'Select a severity.';
  return errors;
}

export default function IncidentForm() {
  const { id } = useParams();
  const isEdit = Boolean(id);
  const navigate = useNavigate();
  const members = useAsync(() => api.listMembers(), []);
  const existing = useAsync(() => (isEdit ? api.getIncident(id) : Promise.resolve(null)), [id]);
  const [values, setValues] = useState(EMPTY);
  const [errors, setErrors] = useState({});
  const [submitError, setSubmitError] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (existing.data) {
      const { title, description, severity, assignee_id } = existing.data;
      setValues({ title, description, severity, assignee_id: assignee_id ? String(assignee_id) : '' });
    }
  }, [existing.data]);

  const onChange = (e) => setValues((v) => ({ ...v, [e.target.name]: e.target.value }));

  const onSubmit = async (e) => {
    e.preventDefault();
    const clientErrors = validateIncident(values);
    setErrors(clientErrors);
    setSubmitError(null);
    if (Object.keys(clientErrors).length) return;

    const payload = {
      title: values.title.trim(),
      description: values.description.trim(),
      severity: values.severity,
      assignee_id: values.assignee_id ? Number(values.assignee_id) : null,
    };
    setSaving(true);
    try {
      const saved = isEdit ? await api.updateIncident(id, payload) : await api.createIncident(payload);
      navigate(`/incidents/${saved.id}`);
    } catch (err) {
      setErrors(Object.fromEntries(err.fieldErrors.map((f) => [f.field, f.message])));
      setSubmitError(err);
      setSaving(false);
    }
  };

  if (existing.loading) return <Loading />;
  if (existing.error) return <ErrorMessage error={existing.error} onRetry={existing.reload} />;
  if (existing.data?.status === 'Resolved') {
    return <ErrorMessage error={new Error('Resolved incidents cannot be edited.')} />;
  }

  return (
    <>
      <div className="page-header">
        <h1>{isEdit ? `Edit incident #${id}` : 'Report incident'}</h1>
      </div>
      <form className="card form" onSubmit={onSubmit} noValidate>
        <ErrorMessage error={submitError} />
        <label htmlFor="title">Title</label>
        <input id="title" name="title" value={values.title} onChange={onChange} maxLength={200}
          aria-invalid={Boolean(errors.title)} />
        {errors.title && <div className="field-error">{errors.title}</div>}

        <label htmlFor="description">Description</label>
        <textarea id="description" name="description" rows={5} value={values.description} onChange={onChange}
          aria-invalid={Boolean(errors.description)} />
        {errors.description && <div className="field-error">{errors.description}</div>}

        <label htmlFor="severity">Severity</label>
        <select id="severity" name="severity" value={values.severity} onChange={onChange}
          aria-invalid={Boolean(errors.severity)}>
          <option value="">Select severity…</option>
          {SEVERITIES.map((s) => <option key={s}>{s}</option>)}
        </select>
        {errors.severity && <div className="field-error">{errors.severity}</div>}

        <label htmlFor="assignee_id">Assignee</label>
        <select id="assignee_id" name="assignee_id" value={values.assignee_id} onChange={onChange}
          disabled={members.loading}>
          <option value="">Unassigned</option>
          {(members.data || []).map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
        </select>
        {members.error && <div className="field-error">Could not load team members.</div>}
        {errors.assignee_id && <div className="field-error">{errors.assignee_id}</div>}

        <div className="actions">
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? 'Saving…' : isEdit ? 'Save changes' : 'Create incident'}
          </button>
          <Link className="btn" to={isEdit ? `/incidents/${id}` : '/incidents'}>Cancel</Link>
        </div>
      </form>
    </>
  );
}
