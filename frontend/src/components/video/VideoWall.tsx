import React, { useState, useEffect, useRef } from 'react';
import VideoPlayer from './VideoPlayer';
import VideoControls from './VideoControls';

interface VideoStream {
  id: string;
  droneId: string;
  url: string;
  status: 'loading' | 'playing' | 'error' | 'disconnected';
  metadata?: {
    resolution?: string;
    fps?: number;
    bitrate?: number;
  };
}

interface VideoWallProps {
  droneIds: string[];
  onStreamSelect?: (droneId: string) => void;
  maxStreams?: number;
  layout?: 'grid' | 'focus';
}

const VideoWall: React.FC<VideoWallProps> = ({
  droneIds,
  onStreamSelect,
  maxStreams = 6,
  layout = 'grid'
}) => {
  const [streams, setStreams] = useState<VideoStream[]>([]);
  const [selectedStreamId, setSelectedStreamId] = useState<string | null>(null);
  const [layoutMode, setLayoutMode] = useState<'grid' | 'focus'>(layout);
  const containerRef = useRef<HTMLDivElement>(null);

  // Initialize video streams for active drones
  useEffect(() => {
    const activeStreams = droneIds.slice(0, maxStreams).map(droneId => ({
      id: `stream-${droneId}`,
      droneId,
      url: `ws://localhost:8000/video/${droneId}`, // WebSocket stream URL
      status: 'loading' as const,
    }));

    setStreams(activeStreams);

    // Set first stream as selected if none selected
    if (activeStreams.length > 0 && !selectedStreamId) {
      setSelectedStreamId(activeStreams[0].id);
    }
  }, [droneIds, maxStreams, selectedStreamId]);

  const handleStreamSelect = (streamId: string) => {
    setSelectedStreamId(streamId);
    const stream = streams.find(s => s.id === streamId);
    if (stream && onStreamSelect) {
      onStreamSelect(stream.droneId);
    }
  };

  const handleStreamStatusChange = (streamId: string, status: VideoStream['status']) => {
    setStreams(prev => prev.map(stream =>
      stream.id === streamId ? { ...stream, status } : stream
    ));
  };

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
      <div className="flex items-center justify-center h-64 bg-gray-800 rounded-lg border-2 border-dashed border-gray-600">
        <div className="text-center text-gray-400">
          <div className="text-4xl mb-2">📹</div>
          <p>No active video streams</p>
          <p className="text-sm">Launch drones to start video feeds</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Layout Controls */}
      <div className="flex justify-between items-center mb-2">
        <span className="text-sm text-gray-400">
          {streams.length} active stream{streams.length !== 1 ? 's' : ''}
        </span>
        <div className="flex gap-1">
          <button
            onClick={() => setLayoutMode('grid')}
            className={`p-1 rounded ${layoutMode === 'grid' ? 'bg-blue-600' : 'bg-gray-700'}`}
            title="Grid Layout"
          >
            ⊞
          </button>
          <button
            onClick={() => setLayoutMode('focus')}
            className={`p-1 rounded ${layoutMode === 'focus' ? 'bg-blue-600' : 'bg-gray-700'}`}
            title="Focus Layout"
          >
            ⊙
          </button>
        </div>
      </div>

      {/* Video Streams Container */}
      <div
        ref={containerRef}
        className={`flex-1 ${layoutMode === 'grid' ? `grid ${getGridLayout()} gap-2` : 'flex flex-col'}`}
      >
        {streams.map((stream) => (
          <div
            key={stream.id}
            className={`
              relative bg-gray-800 rounded-lg overflow-hidden border-2 transition-all duration-200
              ${layoutMode === 'focus' && selectedStreamId === stream.id
                ? 'border-blue-500 flex-1'
                : layoutMode === 'focus'
                  ? 'border-gray-700 h-32'
                  : selectedStreamId === stream.id
                    ? 'border-blue-500'
                    : 'border-gray-700 hover:border-gray-600'
              }
            `}
            onClick={() => handleStreamSelect(stream.id)}
          >
            <VideoPlayer
              streamId={stream.id}
              url={stream.url}
              isSelected={selectedStreamId === stream.id}
              onStatusChange={(status) => handleStreamStatusChange(stream.id, status)}
              className={layoutMode === 'focus' && selectedStreamId === stream.id ? 'h-full' : 'h-full'}
            />

            {/* Stream Info Overlay */}
            <div className="absolute top-2 left-2 bg-black bg-opacity-50 px-2 py-1 rounded text-xs">
              <div className="font-semibold">Drone {stream.droneId.slice(-4)}</div>
              <div className={`capitalize ${stream.status === 'playing' ? 'text-green-400' : 'text-yellow-400'}`}>
                {stream.status}
              </div>
            </div>

            {/* Status Indicator */}
            <div className="absolute top-2 right-2">
              <div className={`
                w-3 h-3 rounded-full
                ${stream.status === 'playing' ? 'bg-green-500' :
                  stream.status === 'loading' ? 'bg-yellow-500' :
                  stream.status === 'error' ? 'bg-red-500' : 'bg-gray-500'}
              `} />
            </div>

            {/* Selection Indicator */}
            {selectedStreamId === stream.id && (
              <div className="absolute inset-0 border-2 border-blue-500 pointer-events-none" />
            )}
          </div>
        ))}
      </div>

      {/* Controls for Selected Stream */}
      {selectedStreamId && (
        <div className="mt-2">
          <VideoControls
            streamId={selectedStreamId}
            onCommand={(command, params) => {
              // Handle video control commands
              console.log('Video command:', command, params);
            }}
          />
        </div>
      )}
    </div>
  );
};

export default VideoWall;