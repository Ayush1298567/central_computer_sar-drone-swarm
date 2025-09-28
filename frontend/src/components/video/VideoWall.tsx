/**
 * Video Wall Component
 * Displays multiple video streams in a grid layout
 */

import React, { useState, useEffect } from 'react';
import { VideoStream } from '../../types';
import { VideoPlayer } from './VideoPlayer';

interface VideoWallProps {
  streams: VideoStream[];
  maxStreams?: number;
  onStreamSelect?: (streamId: string) => void;
  className?: string;
}

export const VideoWall: React.FC<VideoWallProps> = ({
  streams,
  maxStreams = 4,
  onStreamSelect,
  className = ''
}) => {
  const [selectedStream, setSelectedStream] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'grid' | 'focus'>('grid');

  // Filter and limit streams
  const displayStreams = streams
    .filter(stream => stream.status === 'connected')
    .slice(0, maxStreams);

  const handleStreamClick = (streamId: string) => {
    if (viewMode === 'grid') {
      setSelectedStream(streamId);
      setViewMode('focus');
      onStreamSelect?.(streamId);
    } else {
      setSelectedStream(null);
      setViewMode('grid');
    }
  };

  const handleBackToGrid = () => {
    setSelectedStream(null);
    setViewMode('grid');
  };

  if (displayStreams.length === 0) {
    return (
      <div className={`flex items-center justify-center h-64 bg-gray-100 rounded-lg ${className}`}>
        <div className="text-center text-gray-500">
          <div className="text-4xl mb-2">📹</div>
          <p>No active video streams</p>
        </div>
      </div>
    );
  }

  if (viewMode === 'focus' && selectedStream) {
    const stream = displayStreams.find(s => s.id === selectedStream);
    if (!stream) {
      handleBackToGrid();
      return null;
    }

    return (
      <div className={`relative ${className}`}>
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold">Drone {stream.droneId} - Live Feed</h3>
          <button
            onClick={handleBackToGrid}
            className="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700"
          >
            Back to Grid
          </button>
        </div>

        <div className="aspect-video bg-black rounded-lg overflow-hidden">
          <VideoPlayer
            stream={stream}
            autoPlay={true}
            showControls={true}
            className="w-full h-full"
          />
        </div>

        <div className="mt-2 text-sm text-gray-600">
          Status: <span className="capitalize">{stream.status}</span> |
          Quality: <span className="capitalize">{stream.quality}</span>
        </div>
      </div>
    );
  }

  // Grid view
  const getGridCols = () => {
    const count = displayStreams.length;
    if (count === 1) return 'grid-cols-1';
    if (count === 2) return 'grid-cols-2';
    if (count === 3 || count === 4) return 'grid-cols-2';
    return 'grid-cols-3';
  };

  return (
    <div className={`${className}`}>
      <div className={`grid ${getGridCols()} gap-2`}>
        {displayStreams.map((stream) => (
          <div
            key={stream.id}
            className="relative bg-gray-900 rounded-lg overflow-hidden cursor-pointer hover:ring-2 hover:ring-blue-500 transition-all"
            onClick={() => handleStreamClick(stream.id)}
          >
            <div className="aspect-video">
              <VideoPlayer
                stream={stream}
                autoPlay={true}
                showControls={false}
                className="w-full h-full"
              />
            </div>

            {/* Stream overlay info */}
            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black to-transparent p-2">
              <div className="flex justify-between items-center text-white text-xs">
                <span className="font-medium">Drone {stream.droneId}</span>
                <div className="flex items-center space-x-1">
                  <div className={`w-2 h-2 rounded-full ${
                    stream.status === 'connected' ? 'bg-green-500' :
                    stream.status === 'connecting' ? 'bg-yellow-500' : 'bg-red-500'
                  }`}></div>
                  <span className="capitalize text-xs">{stream.quality}</span>
                </div>
              </div>
            </div>

            {/* Connection status indicator */}
            {stream.status !== 'connected' && (
              <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50">
                <div className="text-center text-white">
                  <div className="text-2xl mb-1">
                    {stream.status === 'connecting' ? '🔄' : '⚠️'}
                  </div>
                  <div className="text-xs capitalize">{stream.status}</div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {displayStreams.length > 0 && (
        <div className="mt-2 text-xs text-gray-500 text-center">
          {displayStreams.length} of {streams.length} streams active
        </div>
      )}
    </div>
  );
};