import React from 'react';
import { Mission } from '../../types/api';

interface MissionPreviewProps {
  mission: Mission;
  onMissionSelect?: (mission: Mission) => void;
  compactView?: boolean;
}

const MissionPreview: React.FC<MissionPreviewProps> = ({
  mission,
  onMissionSelect,
  compactView = false,
}) => {
  const getStatusColor = (status: Mission['status']) => {
    switch (status) {
      case 'planning': return 'bg-blue-600';
      case 'active': return 'bg-green-600';
      case 'paused': return 'bg-yellow-600';
      case 'completed': return 'bg-gray-600';
      case 'cancelled': return 'bg-red-600';
      default: return 'bg-gray-600';
    }
  };

  const getPriorityColor = (priority: Mission['priority']) => {
    switch (priority) {
      case 'critical': return 'text-red-400';
      case 'high': return 'text-orange-400';
      case 'medium': return 'text-yellow-400';
      case 'low': return 'text-green-400';
      default: return 'text-gray-400';
    }
  };

  const formatProgress = (progress: number) => {
    return `${Math.round(progress * 100)}%`;
  };

  const formatTime = (timestamp?: number) => {
    if (!timestamp) return 'Not set';
    return new Date(timestamp).toLocaleString();
  };

  return (
    <div
      className="bg-gray-700 rounded p-3 cursor-pointer hover:bg-gray-600 transition-colors"
      onClick={() => onMissionSelect?.(mission)}
    >
      <div className="flex justify-between items-start mb-2">
        <div>
          <div className="font-medium">{mission.name}</div>
          <div className="text-xs text-gray-400">{mission.id}</div>
        </div>
        <div className="flex items-center gap-2">
          <span className={`px-2 py-1 rounded text-xs ${getPriorityColor(mission.priority)}`}>
            {mission.priority}
          </span>
          <div className={`w-2 h-2 rounded-full ${getStatusColor(mission.status)}`} />
        </div>
      </div>

      <p className="text-sm text-gray-300 mb-3 line-clamp-2">
        {mission.description}
      </p>

      <div className="space-y-2 text-xs">
        <div className="flex justify-between">
          <span>Progress:</span>
          <span>{formatProgress(mission.progress)}</span>
        </div>

        <div className="flex justify-between">
          <span>Status:</span>
          <span className="capitalize">{mission.status}</span>
        </div>

        <div className="flex justify-between">
          <span>Drones:</span>
          <span>{mission.assigned_drones.length}</span>
        </div>

        <div className="flex justify-between">
          <span>Discoveries:</span>
          <span>{mission.discoveries.length}</span>
        </div>

        {!compactView && (
          <>
            <div className="flex justify-between">
              <span>Start:</span>
              <span>{formatTime(mission.start_time)}</span>
            </div>

            <div className="flex justify-between">
              <span>End:</span>
              <span>{formatTime(mission.end_time)}</span>
            </div>

            <div className="flex justify-between">
              <span>Area:</span>
              <span>{mission.area.radius.toFixed(1)}m radius</span>
            </div>
          </>
        )}
      </div>

      {/* Progress Bar */}
      <div className="mt-3">
        <div className="w-full bg-gray-600 rounded-full h-2">
          <div
            className="bg-blue-500 h-2 rounded-full transition-all duration-300"
            style={{ width: `${mission.progress * 100}%` }}
          />
        </div>
      </div>
    </div>
  );
};

export default MissionPreview;