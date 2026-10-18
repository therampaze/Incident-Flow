export class ApiError extends Error {
  constructor(message, status, fieldErrors = []) {
    super(message);
    this.status = status;
    this.fieldErrors = fieldErrors;
  }
}

async function request(path, { method = 'GET', body, params } = {}) {
  let url = `/api${path}`;
  if (params) {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== ''),
    ).toString();
    if (qs) url += `?${qs}`;
  }
  let res;
  try {
    res = await fetch(url, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError('Unable to reach the server. Is the backend running?', 0);
  }
  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const message = typeof data?.detail === 'string' ? data.detail : `Request failed (${res.status})`;
    throw new ApiError(message, res.status, data?.errors || []);
  }
  return data;
}

export const api = {
  dashboard: () => request('/dashboard'),
  listIncidents: (params) => request('/incidents', { params }),
  getIncident: (id) => request(`/incidents/${id}`),
  createIncident: (body) => request('/incidents', { method: 'POST', body }),
  updateIncident: (id, body) => request(`/incidents/${id}`, { method: 'PATCH', body }),
  resolveIncident: (id, resolution_note) =>
    request(`/incidents/${id}/resolve`, { method: 'POST', body: { resolution_note } }),
  deleteIncident: (id) => request(`/incidents/${id}`, { method: 'DELETE' }),
  getActivity: (id) => request(`/incidents/${id}/activity`),
  listMembers: () => request('/team-members'),
  createMember: (body) => request('/team-members', { method: 'POST', body }),
};

export const SEVERITIES = ['Low', 'Medium', 'High', 'Critical'];
export const STATUSES = ['Open', 'In Progress', 'Resolved'];

export function formatDate(value) {
  return value ? new Date(value).toLocaleString() : '—';
}
