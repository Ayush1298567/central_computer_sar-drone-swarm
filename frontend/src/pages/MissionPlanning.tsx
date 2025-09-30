import React, { useState } from 'react'
import ConversationalChat from '../components/mission/ConversationalChat'
import InteractiveMap from '../components/map/InteractiveMap'
import MissionPreview from '../components/mission/MissionPreview'

const MissionPlanning: React.FC = () => {
  const [selectedArea, setSelectedArea] = useState<any>(null)
  const [currentMission, setCurrentMission] = useState<any>(null)

  return (
    <div className="h-screen flex">
      {/* Left Panel - Chat and Preview */}
      <div className="w-1/2 flex flex-col border-r border-gray-200">
        <div className="flex-1 p-6 overflow-y-auto">
          <ConversationalChat
            onMissionUpdate={setCurrentMission}
            selectedArea={selectedArea}
          />
        </div>
        <div className="border-t border-gray-200 p-6">
          <MissionPreview mission={currentMission} />
        </div>
      </div>

      {/* Right Panel - Interactive Map */}
      <div className="w-1/2">
        <InteractiveMap
          onAreaSelect={setSelectedArea}
          mission={currentMission}
        />
      </div>
    </div>
  )
}

export default MissionPlanning