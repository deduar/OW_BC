import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link } from 'react-router-dom';
import { AuthProvider, useAuth } from './AuthContext';
import Login from './Login';
import Register from './Register';
import Uploads from './Uploads';
import Workspace from './Workspace';
import RunDetails from './RunDetails';

const PrivateRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isLoading } = useAuth();

  if (isLoading) return <div>Loading...</div>;
  if (!user) return <Navigate to="/login" />;

  return <>{children}</>;
};

const Dashboard: React.FC = () => {
  const { user, logout } = useAuth();
  return (
    <div style={{ padding: '20px' }}>
      <nav style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', borderBottom: '1px solid #eee', paddingBottom: '10px' }}>
        <h1>OW_BC Reconciliation</h1>
        <div>
          <span style={{ marginRight: '15px' }}>{user?.email}</span>
          <button onClick={logout} style={{ padding: '5px 10px', cursor: 'pointer' }}>Logout</button>
        </div>
      </nav>
      <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '20px' }}>
        <aside style={{ borderRight: '1px solid #eee', paddingRight: '20px' }}>
          <ul style={{ listStyle: 'none', padding: 0 }}>
            <li style={{ marginBottom: '10px' }}><Link to="/">Workspace</Link></li>
            <li style={{ marginBottom: '10px' }}><Link to="/uploads">Uploads</Link></li>
            <li style={{ marginBottom: '10px' }}><Link to="/audit">Audit Log</Link></li>
          </ul>
        </aside>
        <main>
          <Routes>
            <Route path="/" element={<Workspace />} />
            <Route path="/workspace/:runId" element={<RunDetails />} />
            <Route path="/uploads" element={<Uploads />} />
            <Route path="/audit" element={<h2>Audit Log (Coming Soon)</h2>} />
          </Routes>
        </main>
      </div>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/*"
            element={
              <PrivateRoute>
                <Dashboard />
              </PrivateRoute>
            }
          />
        </Routes>
      </Router>
    </AuthProvider>
  );
};

export default App;
