import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';

// Import pages (will be created in later phases)
import Dashboard from './pages/Dashboard';
import MissionPlanning from './pages/MissionPlanning';
import LiveMission from './pages/LiveMission';

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/planning" element={<MissionPlanning />} />
            <Route path="/mission/:missionId" element={<LiveMission />} />
          </Routes>
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;