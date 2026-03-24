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

const Home: React.FC = () => (
  <div>
    <h2>Welcome to OW_BC</h2>
    <p>Select an option from the sidebar to begin.</p>
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px', marginTop: '20px' }}>
      <Link to="/" style={cardStyle}>Workspace</Link>
      <Link to="/uploads" style={cardStyle}>Uploads</Link>
      <Link to="/audit" style={cardStyle}>Audit Log</Link>
    </div>
  </div>
);

const cardStyle = {
  padding: '20px',
  border: '1px solid #ddd',
  borderRadius: '8px',
  textAlign: 'center' as const,
  textDecoration: 'none',
  color: '#333',
  backgroundColor: '#f9f9f9'
};

const Dashboard: React.FC = () => {
  const { user, logout } = useAuth();
  return (
    <div style={{ padding: '20px' }}>
      <nav style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', borderBottom: '1px solid #eee', paddingBottom: '10px' }}>
        <h1 style={{ margin: 0 }}>OW_BC Reconciliation</h1>
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <span>{user?.email}</span>
          <button onClick={logout} style={{ padding: '5px 10px', cursor: 'pointer', borderRadius: '4px', border: '1px solid #ccc' }}>Logout</button>
        </div>
      </nav>
      <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '30px' }}>
        <aside style={{ borderRight: '1px solid #eee', paddingRight: '20px' }}>
          <ul style={{ listStyle: 'none', padding: 0 }}>
            <li style={{ marginBottom: '15px' }}><Link to="/" style={{ textDecoration: 'none', color: '#007bff', fontWeight: 'bold' }}>Workspace</Link></li>
            <li style={{ marginBottom: '15px' }}><Link to="/uploads" style={{ textDecoration: 'none', color: '#007bff', fontWeight: 'bold' }}>Uploads</Link></li>
            <li style={{ marginBottom: '15px' }}><Link to="/audit" style={{ textDecoration: 'none', color: '#007bff', fontWeight: 'bold' }}>Audit Log</Link></li>
          </ul>
        </aside>
        <main>
          <Routes>
            <Route path="/" element={<Workspace />} />
            <Route path="/home" element={<Home />} />
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
