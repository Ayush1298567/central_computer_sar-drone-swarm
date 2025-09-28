/**
 * Video Analytics Component
 * Displays object detection and analysis overlays on video streams
 */

import React, { useState, useEffect } from 'react';
import { VideoStream } from '../../types';

export interface DetectedObject {
  id: string;
  type: 'person' | 'vehicle' | 'animal' | 'structure' | 'other';
  confidence: number;
  boundingBox: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  timestamp: Date;
  attributes?: {
    color?: string;
    size?: 'small' | 'medium' | 'large';
    direction?: 'north' | 'south' | 'east' | 'west' | 'stationary';
  };
}

interface VideoAnalyticsProps {
  stream: VideoStream;
  detectedObjects: DetectedObject[];
  showBoundingBoxes?: boolean;
  showLabels?: boolean;
  showConfidence?: boolean;
  onObjectSelect?: (objectId: string) => void;
  className?: string;
}

export const VideoAnalytics: React.FC<VideoAnalyticsProps> = ({
  stream,
  detectedObjects,
  showBoundingBoxes = true,
  showLabels = true,
  showConfidence = true,
  onObjectSelect,
  className = ''
}) => {
  const [selectedObject, setSelectedObject] = useState<string | null>(null);
  const [analyticsMode, setAnalyticsMode] = useState<'detection' | 'tracking' | 'heatmap'>('detection');

  const handleObjectClick = (objectId: string) => {
    setSelectedObject(selectedObject === objectId ? null : objectId);
    onObjectSelect?.(objectId);
  };

  const getObjectColor = (type: string, confidence: number): string => {
    const colors = {
      person: `rgba(34, 197, 94, ${confidence})`, // Green
      vehicle: `rgba(59, 130, 246, ${confidence})`, // Blue
      animal: `rgba(245, 158, 11, ${confidence})`, // Yellow
      structure: `rgba(156, 163, 175, ${confidence})`, // Gray
      other: `rgba(168, 85, 247, ${confidence})` // Purple
    };
    return colors[type as keyof typeof colors] || colors.other;
  };

  const getObjectIcon = (type: string): string => {
    const icons = {
      person: '👤',
      vehicle: '🚗',
      animal: '🐕',
      structure: '🏢',
      other: '📦'
    };
    return icons[type as keyof typeof icons] || '❓';
  };

  const formatConfidence = (confidence: number): string => {
    return `${Math.round(confidence * 100)}%`;
  };

  if (stream.status !== 'connected') {
    return (
      <div className={`flex items-center justify-center h-32 bg-gray-100 rounded-lg ${className}`}>
        <div className="text-center text-gray-500">
          <div className="text-2xl mb-1">🔍</div>
          <div className="text-sm">Analytics unavailable</div>
        </div>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      {/* Analytics controls */}
      <div className="mb-2 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setAnalyticsMode('detection')}
            className={`px-3 py-1 text-xs rounded ${
              analyticsMode === 'detection'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Detection
          </button>
          <button
            onClick={() => setAnalyticsMode('tracking')}
            className={`px-3 py-1 text-xs rounded ${
              analyticsMode === 'tracking'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Tracking
          </button>
          <button
            onClick={() => setAnalyticsMode('heatmap')}
            className={`px-3 py-1 text-xs rounded ${
              analyticsMode === 'heatmap'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Heatmap
          </button>
        </div>

        <div className="flex items-center space-x-2 text-xs text-gray-600">
          <span>{detectedObjects.length} objects detected</span>
        </div>
      </div>

      {/* Analytics overlay */}
      <div className="relative bg-black rounded-lg overflow-hidden aspect-video">
        {/* Base video element would go here */}
        <div className="w-full h-full bg-gray-900 flex items-center justify-center text-white">
          <div className="text-center">
            <div className="text-4xl mb-2">📹</div>
            <div className="text-sm">Video Stream</div>
            <div className="text-xs text-gray-400 mt-1">
              Analytics overlay would be rendered here
            </div>
          </div>
        </div>

        {/* Bounding boxes and labels */}
        {showBoundingBoxes && analyticsMode === 'detection' && (
          <div className="absolute inset-0">
            {detectedObjects.map((obj) => (
              <div
                key={obj.id}
                className={`absolute cursor-pointer transition-all ${
                  selectedObject === obj.id ? 'ring-2 ring-white' : ''
                }`}
                style={{
                  left: `${obj.boundingBox.x}%`,
                  top: `${obj.boundingBox.y}%`,
                  width: `${obj.boundingBox.width}%`,
                  height: `${obj.boundingBox.height}%`,
                  border: `2px solid ${getObjectColor(obj.type, obj.confidence)}`,
                  borderRadius: '4px'
                }}
                onClick={() => handleObjectClick(obj.id)}
              >
                {/* Object label */}
                {showLabels && (
                  <div
                    className="absolute -top-6 left-0 px-2 py-1 text-xs font-medium text-white whitespace-nowrap"
                    style={{
                      backgroundColor: getObjectColor(obj.type, obj.confidence)
                    }}
                  >
                    <span className="mr-1">{getObjectIcon(obj.type)}</span>
                    <span className="capitalize">{obj.type}</span>
                    {showConfidence && (
                      <span className="ml-1 opacity-75">
                        {formatConfidence(obj.confidence)}
                      </span>
                    )}
                  </div>
                )}

                {/* Confidence indicator */}
                {showConfidence && (
                  <div className="absolute -bottom-1 left-0 right-0 h-1 bg-gray-800">
                    <div
                      className="h-full transition-all"
                      style={{
                        width: `${obj.confidence * 100}%`,
                        backgroundColor: getObjectColor(obj.type, 1)
                      }}
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Tracking trails */}
        {analyticsMode === 'tracking' && (
          <div className="absolute inset-0">
            {detectedObjects.map((obj) => (
              <div
                key={`track-${obj.id}`}
                className="absolute w-3 h-3 rounded-full animate-pulse"
                style={{
                  left: `${obj.boundingBox.x}%`,
                  top: `${obj.boundingBox.y}%`,
                  backgroundColor: getObjectColor(obj.type, obj.confidence),
                  transform: 'translate(-50%, -50%)'
                }}
              />
            ))}
          </div>
        )}

        {/* Heatmap overlay */}
        {analyticsMode === 'heatmap' && (
          <div className="absolute inset-0">
            {/* Heatmap would be generated based on object density */}
            <div className="w-full h-full bg-gradient-to-br from-transparent via-red-500/20 to-yellow-500/40" />
            <div className="absolute bottom-2 left-2 text-xs text-white bg-black bg-opacity-50 px-2 py-1 rounded">
              High activity areas shown in red/yellow
            </div>
          </div>
        )}
      </div>

      {/* Object details panel */}
      {selectedObject && (
        <div className="mt-2 p-3 bg-gray-50 rounded-lg border">
          {(() => {
            const obj = detectedObjects.find(o => o.id === selectedObject);
            if (!obj) return null;

            return (
              <div>
                <h4 className="font-medium text-sm mb-2">
                  {getObjectIcon(obj.type)} {obj.type.charAt(0).toUpperCase() + obj.type.slice(1)} Detection
                </h4>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-gray-600">Confidence:</span>
                    <span className="ml-1 font-medium">{formatConfidence(obj.confidence)}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Position:</span>
                    <span className="ml-1 font-medium">
                      ({Math.round(obj.boundingBox.x)}%, {Math.round(obj.boundingBox.y)}%)
                    </span>
                  </div>
                  {obj.attributes && (
                    <>
                      {obj.attributes.size && (
                        <div>
                          <span className="text-gray-600">Size:</span>
                          <span className="ml-1 font-medium capitalize">{obj.attributes.size}</span>
                        </div>
                      )}
                      {obj.attributes.direction && (
                        <div>
                          <span className="text-gray-600">Direction:</span>
                          <span className="ml-1 font-medium capitalize">{obj.attributes.direction}</span>
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            );
          })()}
        </div>
      )}
    </div>
  );
};