import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Dashboard from './pages/Dashboard';
import React, { useMemo } from 'react';
import Login from './pages/Login';

function PrivateRoute({ children }: { children: JSX.Element }) {
  const token = localStorage.getItem('auth_token');
  return token ? children : <Navigate to="/login" replace />;
}
import MissionPlanning from './pages/MissionPlanning';
import EmergencyControl from './pages/EmergencyControl';
import { WebSocketProvider } from './contexts/WebSocketContext';

function App() {
  return (
    <Router>
<<<<<<< Current (Your changes)
      <div className="min-h-screen bg-gray-50">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/login" element={<Login />} />
          <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
          <Route path="/mission-planning" element={<PrivateRoute><MissionPlanning /></PrivateRoute>} />
          <Route path="/emergency-control" element={<PrivateRoute><EmergencyControl /></PrivateRoute>} />
        </Routes>
        
        {/* Global toast notifications */}
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#363636',
              color: '#fff',
            },
            success: {
              duration: 3000,
              iconTheme: {
                primary: '#22c55e',
                secondary: '#fff',
=======
      <WebSocketProvider>
        <div className="min-h-screen bg-gray-50">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/mission-planning" element={<MissionPlanning />} />
            <Route path="/emergency-control" element={<EmergencyControl />} />
          </Routes>
          
          {/* Global toast notifications */}
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#363636',
                color: '#fff',
>>>>>>> Incoming (Background Agent changes)
              },
              success: {
                duration: 3000,
                iconTheme: {
                  primary: '#22c55e',
                  secondary: '#fff',
                },
              },
              error: {
                duration: 5000,
                iconTheme: {
                  primary: '#ef4444',
                  secondary: '#fff',
                },
              },
            }}
          />
        </div>
      </WebSocketProvider>
    </Router>
  );
}

export default App;