import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Toaster } from 'react-hot-toast';
import './App.css';

// Layout Components
import Layout from './components/Layout/Layout';

// Pages
import Dashboard from './pages/Dashboard';
import MissionPlanning from './pages/MissionPlanning';
import LiveMission from './pages/LiveMission';

// Context Providers
import { WebSocketProvider } from './contexts/WebSocketContext';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <WebSocketProvider>
        <Router>
          <div className="App">
            <Layout>
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/mission-planning" element={<MissionPlanning />} />
                <Route path="/live-mission/:missionId" element={<LiveMission />} />
              </Routes>
            </Layout>
            <Toaster position="top-right" />
          </div>
        </Router>
      </WebSocketProvider>
    </QueryClientProvider>
  );
}

export default App;