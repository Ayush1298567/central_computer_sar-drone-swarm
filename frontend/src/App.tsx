import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import MissionPlanning from './pages/MissionPlanning';
import LiveMission from './pages/LiveMission';

function App() {
  return (
    <Router>
      <div className="App">
        <Layout>
          <Routes>
            {/* Default route redirects to dashboard */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            
            {/* Main application routes */}
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/mission-planning" element={<MissionPlanning />} />
            <Route path="/mission/:missionId" element={<LiveMission />} />
            
            {/* Catch-all route for 404s */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Layout>
      </div>
    </Router>
  );
}

export default App;