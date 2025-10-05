import React, { useState, useEffect, useRef, useCallback } from 'react';
import VideoPlayer from './VideoPlayer';
import VideoControls from './VideoControls';
import { Drone } from '../../types';
import { websocketService } from '../../services';

interface VideoStream {
  id: string;
  droneId: string;
  url: string;
  status: 'loading' | 'playing' | 'error' | 'disconnected';
  metadata?: {
    resolution?: string;
    fps?: number;
    bitrate?: number;
    timestamp?: string;
  };
}

interface VideoWallProps {
  drones: Drone[];
  selectedDrone?: string | null;
  onDroneSelect?: (drone: Drone) => void;
  maxStreams?: number;
  layout?: 'grid' | 'focus';
  className?: string;
}

const VideoWall: React.FC<VideoWallProps> = ({
  drones,
  selectedDrone,
  onDroneSelect,
  maxStreams = 6,
  layout = 'grid',
  className = ''
}) => {
  const [streams, setStreams] = useState<VideoStream[]>([]);
  const [selectedStreamId, setSelectedStreamId] = useState<string | null>(null);
  const [layoutMode, setLayoutMode] = useState<'grid' | 'focus'>(layout);
  const [recordingStatus, setRecordingStatus] = useState<Record<string, boolean>>({});
  const containerRef = useRef<HTMLDivElement>(null);

  // Initialize video streams for active drones
  useEffect(() => {
    const activeDrones = drones.filter(drone => drone.status === 'flying' || drone.status === 'online');
    const activeStreams = activeDrones.slice(0, maxStreams).map(drone => ({
      id: `stream-${drone.drone_id}`,
      droneId: drone.drone_id,
      url: `ws://localhost:8000/video/${drone.drone_id}`, // WebSocket stream URL
      status: 'loading' as const,
      metadata: {
        resolution: '1920x1080',
        fps: 30,
        bitrate: 2000,
        timestamp: new Date().toISOString()
      }
    }));

    setStreams(activeStreams);

    // Set selected stream based on selectedDrone prop
    if (selectedDrone) {
      const stream = activeStreams.find(s => s.droneId === selectedDrone);
      if (stream) {
        setSelectedStreamId(stream.id);
      }
    } else if (activeStreams.length > 0 && !selectedStreamId) {
      setSelectedStreamId(activeStreams[0].id);
    }
  }, [drones, maxStreams, selectedDrone, selectedStreamId]);

  // WebSocket subscriptions for video metadata updates
  useEffect(() => {
    const handleVideoMetadata = (event: CustomEvent) => {
      const metadata = event.detail;
      setStreams(prev => prev.map(stream =>
        stream.droneId === metadata.drone_id
          ? { ...stream, metadata: { ...stream.metadata, ...metadata } }
          : stream
      ));
    };

    window.addEventListener('videoMetadata', handleVideoMetadata as EventListener);

    return () => {
      window.removeEventListener('videoMetadata', handleVideoMetadata as EventListener);
    };
  }, []);

  const handleStreamSelect = useCallback((streamId: string) => {
    setSelectedStreamId(streamId);
    const stream = streams.find(s => s.id === streamId);
    if (stream && onDroneSelect) {
      const drone = drones.find(d => d.drone_id === stream.droneId);
      if (drone) {
        onDroneSelect(drone);
      }
    }
  }, [streams, onDroneSelect, drones]);

  const handleStreamStatusChange = useCallback((streamId: string, status: VideoStream['status']) => {
    setStreams(prev => prev.map(stream =>
      stream.id === streamId ? { ...stream, status } : stream
    ));
  }, []);

  const handleRecordingToggle = useCallback(async (streamId: string) => {
    const stream = streams.find(s => s.id === streamId);
    if (!stream) return;

    try {
      const isRecording = recordingStatus[streamId] || false;
      setRecordingStatus(prev => ({ ...prev, [streamId]: !isRecording }));
      
      // Send recording command via WebSocket
      websocketService.sendMessage('video_command', {
        drone_id: stream.droneId,
        command: isRecording ? 'stop_recording' : 'start_recording'
      });
    } catch (error) {
      console.error('Failed to toggle recording:', error);
    }
  }, [streams, recordingStatus]);

  const getGridLayout = () => {
    const count = streams.length;
    if (count <= 1) return 'grid-cols-1';
    if (count <= 2) return 'grid-cols-2';
    if (count <= 4) return 'grid-cols-2';
    if (count <= 6) return 'grid-cols-3';
    return 'grid-cols-3';
  };

  if (streams.length === 0) {
    return (
      <div className={`flex items-center justify-center h-64 bg-gray-800 rounded-lg border-2 border-dashed border-gray-600 ${className}`}>
        <div className="text-center text-gray-400">
          <div className="text-4xl mb-2">📹</div>
          <p>No active video streams</p>
          <p className="text-sm">Launch drones to start video feeds</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Header with Controls */}
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center space-x-4">
          <h3 className="text-lg font-semibold text-gray-900">Video Wall</h3>
          <span className="text-sm text-gray-500">
            {streams.length} active stream{streams.length !== 1 ? 's' : ''}
          </span>
        </div>
        
        <div className="flex items-center space-x-2">
          {/* Layout Controls */}
          <div className="flex gap-1">
            <button
              onClick={() => setLayoutMode('grid')}
              className={`px-3 py-1 rounded text-sm ${
                layoutMode === 'grid' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
              title="Grid Layout"
            >
              Grid
            </button>
            <button
              onClick={() => setLayoutMode('focus')}
              className={`px-3 py-1 rounded text-sm ${
                layoutMode === 'focus' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
              title="Focus Layout"
            >
              Focus
            </button>
          </div>

          {/* Recording Controls */}
          {selectedStreamId && (
            <button
              onClick={() => handleRecordingToggle(selectedStreamId)}
              className={`px-3 py-1 rounded text-sm ${
                recordingStatus[selectedStreamId]
                  ? 'bg-red-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {recordingStatus[selectedStreamId] ? 'Stop Recording' : 'Start Recording'}
            </button>
          )}
        </div>
      </div>

      {/* Video Streams Container */}
      <div
        ref={containerRef}
        className={`flex-1 ${
          layoutMode === 'grid' 
            ? `grid ${getGridLayout()} gap-4` 
            : 'flex flex-col space-y-2'
        }`}
      >
        {streams.map((stream) => {
          const drone = drones.find(d => d.drone_id === stream.droneId);
          const isSelected = selectedStreamId === stream.id;
          const isRecording = recordingStatus[stream.id] || false;

          return (
            <div
              key={stream.id}
              className={`
                relative bg-gray-800 rounded-lg overflow-hidden border-2 transition-all duration-200 cursor-pointer
                ${layoutMode === 'focus' && isSelected
                  ? 'border-blue-500 flex-1'
                  : layoutMode === 'focus'
                    ? 'border-gray-700 h-32'
                    : isSelected
                      ? 'border-blue-500'
                      : 'border-gray-700 hover:border-gray-600'
                }
              `}
              onClick={() => handleStreamSelect(stream.id)}
            >
              <VideoPlayer
                streamId={stream.id}
                url={stream.url}
                isSelected={isSelected}
                onStatusChange={(status) => handleStreamStatusChange(stream.id, status)}
                className={layoutMode === 'focus' && isSelected ? 'h-full' : 'h-full'}
              />

              {/* Stream Info Overlay */}
              <div className="absolute top-2 left-2 bg-black bg-opacity-70 px-2 py-1 rounded text-xs text-white">
                <div className="font-semibold">
                  {drone?.name || `Drone ${stream.droneId.slice(-4)}`}
                </div>
                <div className={`capitalize ${
                  stream.status === 'playing' ? 'text-green-400' : 
                  stream.status === 'loading' ? 'text-yellow-400' :
                  stream.status === 'error' ? 'text-red-400' : 'text-gray-400'
                }`}>
                  {stream.status}
                </div>
                {stream.metadata && (
                  <div className="text-gray-300">
                    {stream.metadata.resolution} @ {stream.metadata.fps}fps
                  </div>
                )}
              </div>

              {/* Status Indicators */}
              <div className="absolute top-2 right-2 flex space-x-1">
                {/* Connection Status */}
                <div className={`
                  w-3 h-3 rounded-full
                  ${stream.status === 'playing' ? 'bg-green-500' :
                    stream.status === 'loading' ? 'bg-yellow-500' :
                    stream.status === 'error' ? 'bg-red-500' : 'bg-gray-500'}
                `} />
                
                {/* Recording Indicator */}
                {isRecording && (
                  <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
                )}
              </div>

              {/* Battery Indicator */}
              {drone && (
                <div className="absolute bottom-2 left-2 bg-black bg-opacity-70 px-2 py-1 rounded text-xs text-white">
                  <div className="flex items-center space-x-1">
                    <span>Battery:</span>
                    <span className={`font-semibold ${
                      drone.battery_level > 50 ? 'text-green-400' :
                      drone.battery_level > 20 ? 'text-yellow-400' : 'text-red-400'
                    }`}>
                      {drone.battery_level}%
                    </span>
                  </div>
                </div>
              )}

              {/* Selection Indicator */}
              {isSelected && (
                <div className="absolute inset-0 border-2 border-blue-500 pointer-events-none rounded-lg" />
              )}
            </div>
          );
        })}
      </div>

      {/* Controls for Selected Stream */}
      {selectedStreamId && (
        <div className="mt-4">
          <VideoControls
            streamId={selectedStreamId}
            onCommand={(command) => {
              const stream = streams.find(s => s.id === selectedStreamId);
              if (stream) {
                websocketService.sendMessage('video_command', {
                  drone_id: stream.droneId,
                  command
                });
              }
            }}
          />
        </div>
      )}
    </div>
  );
};

export default VideoWall;