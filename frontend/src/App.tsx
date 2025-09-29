import { Routes, Route } from 'react-router-dom'
import Layout from '@/components/Layout/Layout'
import Dashboard from '@/pages/Dashboard'
import MissionPlanning from '@/pages/MissionPlanning'
import LiveMission from '@/pages/LiveMission'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/mission-planning" element={<MissionPlanning />} />
        <Route path="/live-mission" element={<LiveMission missionId="default" />} />
      </Routes>
    </Layout>
  )
}

export default App