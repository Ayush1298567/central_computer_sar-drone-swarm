import React, { useState, useEffect } from 'react';

interface DetectionObject {
  id: string;
  type: 'person' | 'vehicle' | 'animal' | 'structure' | 'unknown';
  confidence: number;
  boundingBox: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  coordinates?: {
    lat: number;
    lng: number;
  };
  timestamp: number;
}

interface VideoAnalyticsProps {
  streamId: string;
  detections?: DetectionObject[];
  onDetectionSelect?: (detection: DetectionObject) => void;
  showHeatmap?: boolean;
  sensitivity?: 'low' | 'medium' | 'high';
}

const VideoAnalytics: React.FC<VideoAnalyticsProps> = ({
  streamId,
  detections = [],
  onDetectionSelect,
  showHeatmap = false,
  sensitivity = 'medium',
}) => {
  const [analyticsData, setAnalyticsData] = useState({
    totalDetections: 0,
    detectionRate: 0,
    averageConfidence: 0,
    detectionTypes: {} as Record<string, number>,
  });
  const [heatmapData, setHeatmapData] = useState<number[][]>([]);
  const [selectedDetection, setSelectedDetection] = useState<DetectionObject | null>(null);

  // Calculate analytics from detections
  useEffect(() => {
    if (detections.length === 0) {
      setAnalyticsData({
        totalDetections: 0,
        detectionRate: 0,
        averageConfidence: 0,
        detectionTypes: {},
      });
      return;
    }

    const now = Date.now();
    const recentDetections = detections.filter(d => now - d.timestamp < 60000); // Last minute

    const detectionTypes: Record<string, number> = {};
    let totalConfidence = 0;

    detections.forEach(detection => {
      detectionTypes[detection.type] = (detectionTypes[detection.type] || 0) + 1;
      totalConfidence += detection.confidence;
    });

    const avgConfidence = totalConfidence / detections.length;
    const detectionRate = recentDetections.length; // detections per minute

    setAnalyticsData({
      totalDetections: detections.length,
      detectionRate,
      averageConfidence: avgConfidence,
      detectionTypes,
    });

    // Generate heatmap data
    if (showHeatmap) {
      generateHeatmap(detections);
    }
  }, [detections, showHeatmap]);

  const generateHeatmap = (detections: DetectionObject[]) => {
    // Simple heatmap generation - in real implementation, this would be more sophisticated
    const heatmap: number[][] = Array(20).fill(null).map(() => Array(20).fill(0));

    detections.forEach(detection => {
      const x = Math.floor((detection.boundingBox.x + detection.boundingBox.width / 2) / 5);
      const y = Math.floor((detection.boundingBox.y + detection.boundingBox.height / 2) / 5);

      if (x >= 0 && x < 20 && y >= 0 && y < 20) {
        heatmap[y][x] += detection.confidence;
      }
    });

    setHeatmapData(heatmap);
  };

  const handleDetectionClick = (detection: DetectionObject) => {
    setSelectedDetection(detection);
    onDetectionSelect?.(detection);
  };

  const getDetectionColor = (type: string, confidence: number) => {
    const alpha = Math.max(0.3, confidence);
    switch (type) {
      case 'person': return `rgba(255, 0, 0, ${alpha})`; // Red
      case 'vehicle': return `rgba(0, 255, 0, ${alpha})`; // Green
      case 'animal': return `rgba(255, 255, 0, ${alpha})`; // Yellow
      case 'structure': return `rgba(0, 0, 255, ${alpha})`; // Blue
      default: return `rgba(255, 255, 255, ${alpha})`; // White
    }
  };

  const formatConfidence = (confidence: number) => {
    return Math.round(confidence * 100);
  };

  return (
    <div className="bg-gray-800 rounded-lg p-4 h-full flex flex-col">
      <h3 className="text-lg font-semibold mb-4">Video Analytics</h3>

      {/* Analytics Summary */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-gray-700 p-3 rounded">
          <div className="text-sm text-gray-400">Total Detections</div>
          <div className="text-2xl font-bold">{analyticsData.totalDetections}</div>
        </div>
        <div className="bg-gray-700 p-3 rounded">
          <div className="text-sm text-gray-400">Detection Rate</div>
          <div className="text-2xl font-bold">{analyticsData.detectionRate}/min</div>
        </div>
        <div className="bg-gray-700 p-3 rounded">
          <div className="text-sm text-gray-400">Avg Confidence</div>
          <div className="text-2xl font-bold">{formatConfidence(analyticsData.averageConfidence)}%</div>
        </div>
        <div className="bg-gray-700 p-3 rounded">
          <div className="text-sm text-gray-400">Sensitivity</div>
          <div className="text-sm font-medium capitalize">{sensitivity}</div>
        </div>
      </div>

      {/* Detection Types */}
      <div className="mb-4">
        <h4 className="text-sm font-medium mb-2">Detection Types</h4>
        <div className="flex flex-wrap gap-2">
          {Object.entries(analyticsData.detectionTypes).map(([type, count]) => (
            <div key={type} className="bg-gray-700 px-2 py-1 rounded text-sm">
              <span className="capitalize">{type}</span>: {count}
            </div>
          ))}
        </div>
      </div>

      {/* Heatmap */}
      {showHeatmap && heatmapData.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-medium mb-2">Detection Heatmap</h4>
          <div className="bg-gray-700 p-2 rounded">
            <div className="grid grid-cols-20 gap-px h-32">
              {heatmapData.map((row, y) =>
                row.map((value, x) => (
                  <div
                    key={`${x}-${y}`}
                    className="bg-gray-600"
                    style={{
                      backgroundColor: `rgba(255, 0, 0, ${Math.min(value, 1)})`,
                      opacity: 0.6,
                    }}
                    title={`Heat intensity: ${value.toFixed(2)}`}
                  />
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Recent Detections */}
      <div className="flex-1 overflow-hidden">
        <h4 className="text-sm font-medium mb-2">Recent Detections</h4>
        <div className="space-y-2 max-h-48 overflow-y-auto">
          {detections.slice(-10).reverse().map((detection) => (
            <div
              key={detection.id}
              className={`
                p-2 rounded cursor-pointer transition-colors
                ${selectedDetection?.id === detection.id
                  ? 'bg-blue-600'
                  : 'bg-gray-700 hover:bg-gray-600'
                }
              `}
              onClick={() => handleDetectionClick(detection)}
            >
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full border"
                    style={{
                      backgroundColor: getDetectionColor(detection.type, detection.confidence),
                      borderColor: 'white',
                    }}
                  />
                  <span className="text-sm capitalize font-medium">
                    {detection.type}
                  </span>
                </div>
                <span className="text-xs text-gray-400">
                  {formatConfidence(detection.confidence)}%
                </span>
              </div>
              <div className="text-xs text-gray-400 mt-1">
                {new Date(detection.timestamp).toLocaleTimeString()}
              </div>
            </div>
          ))}
          {detections.length === 0 && (
            <div className="text-center text-gray-500 py-4">
              No detections yet
            </div>
          )}
        </div>
      </div>

      {/* Selected Detection Details */}
      {selectedDetection && (
        <div className="mt-4 p-3 bg-gray-700 rounded">
          <h5 className="text-sm font-medium mb-2">Selected Detection</h5>
          <div className="text-sm space-y-1">
            <div><strong>Type:</strong> {selectedDetection.type}</div>
            <div><strong>Confidence:</strong> {formatConfidence(selectedDetection.confidence)}%</div>
            <div><strong>Position:</strong> ({selectedDetection.boundingBox.x}, {selectedDetection.boundingBox.y})</div>
            <div><strong>Size:</strong> {selectedDetection.boundingBox.width}×{selectedDetection.boundingBox.height}</div>
            {selectedDetection.coordinates && (
              <div>
                <strong>GPS:</strong> {selectedDetection.coordinates.lat.toFixed(6)}, {selectedDetection.coordinates.lng.toFixed(6)}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default VideoAnalytics;