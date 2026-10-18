import { act, fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import App from './App.jsx';

function mockFetch(routes) {
  const fn = vi.fn(async (url) => {
    const path = Object.keys(routes).find((p) => url.startsWith(p));
    return { ok: true, status: 200, json: async () => routes[path] };
  });
  vi.stubGlobal('fetch', fn);
  return fn;
}

function renderAt(path) {
  return render(
    <MemoryRouter initialEntries={[path]} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <App />
    </MemoryRouter>,
  );
}

afterEach(() => vi.unstubAllGlobals());

describe('IncidentFlow UI', () => {
  it('renders dashboard values from the API', async () => {
    mockFetch({
      '/api/dashboard': {
        total: 3, open: 1, in_progress: 1, critical_unresolved: 2, resolved: 1, avg_resolution_hours: 2.5,
        severity_breakdown: { Low: 0, Medium: 1, High: 0, Critical: 2 }, recent_incidents: [],
      },
    });
    renderAt('/');
    expect(await screen.findByText('Critical (unresolved)')).toBeInTheDocument();
    expect(screen.getByText('2.5 h')).toBeInTheDocument();
    expect(screen.getByText('No incidents reported yet.')).toBeInTheDocument();
  });

  it('sends filters to the backend and shows an empty state', async () => {
    const fetchMock = mockFetch({ '/api/team-members': [], '/api/incidents': [] });
    renderAt('/incidents?status=Open&severity=Critical');
    expect(await screen.findByText('No incidents match the current filters.')).toBeInTheDocument();
    const urls = fetchMock.mock.calls.map(([u]) => u);
    expect(urls).toContain('/api/incidents?status=Open&severity=Critical');
  });

  it('shows validation messages without calling the create API', async () => {
    const fetchMock = mockFetch({ '/api/team-members': [] });
    renderAt('/incidents/new');
    fireEvent.click(await screen.findByRole('button', { name: 'Create incident' }));
    expect(screen.getByText('Title is required.')).toBeInTheDocument();
    expect(screen.getByText('Description is required.')).toBeInTheDocument();
    expect(screen.getByText('Select a severity.')).toBeInTheDocument();
    expect(fetchMock.mock.calls.some(([, opts]) => opts?.method === 'POST')).toBe(false);
  });

  it('Clear resets search and all other filters', async () => {
    const fetchMock = mockFetch({ '/api/team-members': [], '/api/incidents': [] });
    renderAt('/incidents?q=disk&status=Open&severity=High');
    fireEvent.click(await screen.findByRole('button', { name: 'Clear' }));
    await act(() => new Promise((r) => setTimeout(r, 400)));
    expect(screen.getByLabelText('Status')).toHaveValue('');
    expect(screen.getByLabelText('Severity')).toHaveValue('');
    expect(screen.getByLabelText('Search')).toHaveValue('');
    const incidentCalls = fetchMock.mock.calls.map(([u]) => u).filter((u) => u.startsWith('/api/incidents'));
    expect(incidentCalls.at(-1)).toBe('/api/incidents');
  });
});
