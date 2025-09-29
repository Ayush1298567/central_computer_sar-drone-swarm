import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';

// Layout components
import Layout from './components/ui/Layout';

// Page components
import Dashboard from './pages/Dashboard';
import MissionPlanning from './pages/MissionPlanning';
import LiveMission from './pages/LiveMission';

// Context providers
import { NotificationProvider } from './components/notifications/NotificationProvider';
import { WebSocketProvider } from './components/websocket/WebSocketProvider';

// Create a client
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
      <Router>
        <WebSocketProvider>
          <NotificationProvider>
            <Layout>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/mission-planning" element={<MissionPlanning />} />
                <Route path="/live-mission/:missionId" element={<LiveMission />} />
                <Route path="/drones" element={<div>Drones Page (Coming Soon)</div>} />
                <Route path="/discoveries" element={<div>Discoveries Page (Coming Soon)</div>} />
                <Route path="/analytics" element={<div>Analytics Page (Coming Soon)</div>} />
                <Route path="/settings" element={<div>Settings Page (Coming Soon)</div>} />
              </Routes>
            </Layout>
          </NotificationProvider>
        </WebSocketProvider>
      </Router>
    </QueryClientProvider>
  );
}

export default App;