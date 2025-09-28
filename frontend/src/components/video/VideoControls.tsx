import React, { useState } from 'react';

interface VideoCommand {
  action: 'record' | 'stop' | 'snapshot' | 'zoom' | 'focus' | 'night_mode' | 'thermal';
  parameters?: Record<string, any>;
}

interface VideoControlsProps {
  streamId: string;
  onCommand?: (command: VideoCommand) => void;
  isRecording?: boolean;
  isConnected?: boolean;
}

const VideoControls: React.FC<VideoControlsProps> = ({
  streamId,
  onCommand,
  isRecording = false,
  isConnected = true,
}) => {
  const [zoomLevel, setZoomLevel] = useState(1);
  const [isNightMode, setIsNightMode] = useState(false);
  const [isThermalMode, setIsThermalMode] = useState(false);

  const handleCommand = (action: VideoCommand['action'], parameters?: Record<string, any>) => {
    const command: VideoCommand = { action, parameters };
    onCommand?.(command);
  };

  const handleZoomIn = () => {
    const newZoom = Math.min(zoomLevel + 0.5, 5);
    setZoomLevel(newZoom);
    handleCommand('zoom', { level: newZoom });
  };

  const handleZoomOut = () => {
    const newZoom = Math.max(zoomLevel - 0.5, 1);
    setZoomLevel(newZoom);
    handleCommand('zoom', { level: newZoom });
  };

  const handleRecord = () => {
    if (isRecording) {
      handleCommand('stop');
    } else {
      handleCommand('record', { startTime: Date.now() });
    }
  };

  const handleSnapshot = () => {
    handleCommand('snapshot', { timestamp: Date.now() });
  };

  const handleFocus = () => {
    handleCommand('focus', { auto: true });
  };

  const handleNightMode = () => {
    setIsNightMode(!isNightMode);
    handleCommand('night_mode', { enabled: !isNightMode });
  };

  const handleThermalMode = () => {
    setIsThermalMode(!isThermalMode);
    handleCommand('thermal', { enabled: !isThermalMode });
  };

  return (
    <div className="bg-gray-800 rounded-lg p-3">
      <div className="flex flex-wrap gap-2">
        {/* Recording Controls */}
        <div className="flex gap-1">
          <button
            onClick={handleRecord}
            disabled={!isConnected}
            className={`
              px-3 py-1 rounded text-sm font-medium transition-colors
              ${isRecording
                ? 'bg-red-600 hover:bg-red-700'
                : 'bg-green-600 hover:bg-green-700'
              }
              disabled:bg-gray-600 disabled:cursor-not-allowed
            `}
          >
            {isRecording ? '⏹️ Stop Recording' : '⏺️ Record'}
          </button>

          <button
            onClick={handleSnapshot}
            disabled={!isConnected}
            className="px-3 py-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded text-sm"
            title="Take Snapshot"
          >
            📸
          </button>
        </div>

        {/* Zoom Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleZoomOut}
            disabled={!isConnected || zoomLevel <= 1}
            className="px-2 py-1 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 rounded text-sm"
            title="Zoom Out"
          >
            🔍-
          </button>

          <span className="text-sm min-w-[3rem] text-center">
            {zoomLevel}x
          </span>

          <button
            onClick={handleZoomIn}
            disabled={!isConnected || zoomLevel >= 5}
            className="px-2 py-1 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 rounded text-sm"
            title="Zoom In"
          >
            🔍+
          </button>
        </div>

        {/* Mode Controls */}
        <div className="flex gap-1">
          <button
            onClick={handleFocus}
            disabled={!isConnected}
            className="px-3 py-1 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 rounded text-sm"
            title="Auto Focus"
          >
            🎯
          </button>

          <button
            onClick={handleNightMode}
            disabled={!isConnected}
            className={`
              px-3 py-1 rounded text-sm transition-colors
              ${isNightMode
                ? 'bg-yellow-600 hover:bg-yellow-700'
                : 'bg-gray-700 hover:bg-gray-600'
              }
              disabled:bg-gray-800
            `}
            title="Night Mode"
          >
            🌙
          </button>

          <button
            onClick={handleThermalMode}
            disabled={!isConnected}
            className={`
              px-3 py-1 rounded text-sm transition-colors
              ${isThermalMode
                ? 'bg-orange-600 hover:bg-orange-700'
                : 'bg-gray-700 hover:bg-gray-600'
              }
              disabled:bg-gray-800
            `}
            title="Thermal Mode"
          >
            🔥
          </button>
        </div>
      </div>

      {/* Status Indicators */}
      <div className="flex justify-between items-center mt-2 text-xs text-gray-400">
        <span>Stream: {streamId}</span>
        <div className="flex gap-2">
          {isRecording && (
            <span className="flex items-center gap-1 text-red-400">
              <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
              Recording
            </span>
          )}
          {!isConnected && (
            <span className="text-red-400">Disconnected</span>
          )}
          {isNightMode && (
            <span className="text-yellow-400">Night Mode</span>
          )}
          {isThermalMode && (
            <span className="text-orange-400">Thermal</span>
          )}
        </div>
      </div>
    </div>
  );
};

export default VideoControls;