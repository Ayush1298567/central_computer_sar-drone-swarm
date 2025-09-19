import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout } from 'antd';
import 'antd/dist/antd.css';
import './App.css';

import Sidebar from './components/Layout/Sidebar';
import Header from './components/Layout/Header';
import Dashboard from './pages/Dashboard';
import MissionPlanning from './pages/MissionPlanning';
import ActiveMissions from './pages/ActiveMissions';
import DroneFleet from './pages/DroneFleet';
import RealTimeMonitoring from './pages/RealTimeMonitoring';
import AIInsights from './pages/AIInsights';
import { WebSocketProvider } from './contexts/WebSocketContext';

const { Content } = Layout;

function App() {
  return (
    <WebSocketProvider>
      <Router>
        <Layout style={{ minHeight: '100vh' }}>
          <Sidebar />
          <Layout className="site-layout">
            <Header />
            <Content style={{ margin: '24px 16px', padding: 24, background: '#fff' }}>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/mission-planning" element={<MissionPlanning />} />
                <Route path="/active-missions" element={<ActiveMissions />} />
                <Route path="/drone-fleet" element={<DroneFleet />} />
                <Route path="/monitoring" element={<RealTimeMonitoring />} />
                <Route path="/ai-insights" element={<AIInsights />} />
              </Routes>
            </Content>
          </Layout>
        </Layout>
      </Router>
    </WebSocketProvider>
  );
}

export default App;