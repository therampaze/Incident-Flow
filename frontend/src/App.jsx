import { NavLink, Route, Routes } from 'react-router-dom';
import Dashboard from './pages/Dashboard.jsx';
import IncidentList from './pages/IncidentList.jsx';
import IncidentDetail from './pages/IncidentDetail.jsx';
import IncidentForm from './pages/IncidentForm.jsx';
import Team from './pages/Team.jsx';
import { EmptyState } from './components.jsx';

export default function App() {
  return (
    <div className="app">
      <header className="topbar">
        <span className="brand">IncidentFlow</span>
        <nav>
          <NavLink to="/" end>Dashboard</NavLink>
          <NavLink to="/incidents">Incidents</NavLink>
          <NavLink to="/team">Team</NavLink>
        </nav>
      </header>
      <main className="content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/incidents" element={<IncidentList />} />
          <Route path="/incidents/new" element={<IncidentForm />} />
          <Route path="/incidents/:id" element={<IncidentDetail />} />
          <Route path="/incidents/:id/edit" element={<IncidentForm />} />
          <Route path="/team" element={<Team />} />
          <Route path="*" element={<EmptyState>Page not found.</EmptyState>} />
        </Routes>
      </main>
    </div>
  );
}
