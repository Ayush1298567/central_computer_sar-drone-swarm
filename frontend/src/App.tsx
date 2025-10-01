import React, { useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import MissionPlanning from './pages/MissionPlanning';
import LiveMission from './pages/LiveMission';
import { websocketService } from './services/websocket';

function App() {
  useEffect(() => {
    // Connect WebSocket on app start
    websocketService.connect();

    return () => {
      // Disconnect WebSocket on app unmount
      websocketService.disconnect();
    };
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/planning" element={<MissionPlanning />} />
        <Route path="/mission/:missionId" element={<LiveMission />} />
      </Routes>
    </div>
  );
}

export default App;
