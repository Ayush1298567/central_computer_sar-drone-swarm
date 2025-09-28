/**
 * Evidence Viewer Component
 * Displays image/video evidence with metadata and analysis tools
 */

import React, { useState, useRef, useEffect } from 'react';
import { Evidence } from '../../types';

interface EvidenceViewerProps {
  evidence: Evidence[];
  selectedEvidenceId?: string;
  onEvidenceSelect?: (evidenceId: string) => void;
  onEvidenceAnalyze?: (evidenceId: string) => void;
  showMetadata?: boolean;
  showAnalysis?: boolean;
  className?: string;
}

export const EvidenceViewer: React.FC<EvidenceViewerProps> = ({
  evidence,
  selectedEvidenceId,
  onEvidenceSelect,
  onEvidenceAnalyze,
  showMetadata = true,
  showAnalysis = true,
  className = ''
}) => {
  const [selectedEvidence, setSelectedEvidence] = useState<Evidence | null>(
    evidence.find(e => e.id === selectedEvidenceId) || null
  );
  const [viewMode, setViewMode] = useState<'grid' | 'detail'>('grid');
  const [analysisResults, setAnalysisResults] = useState<Record<string, any>>({});
  const videoRefs = useRef<Record<string, HTMLVideoElement>>({});

  useEffect(() => {
    if (selectedEvidenceId) {
      const evidenceItem = evidence.find(e => e.id === selectedEvidenceId);
      setSelectedEvidence(evidenceItem || null);
      if (evidenceItem) {
        setViewMode('detail');
      }
    }
  }, [selectedEvidenceId, evidence]);

  const handleEvidenceClick = (evidenceItem: Evidence) => {
    setSelectedEvidence(evidenceItem);
    setViewMode('detail');
    onEvidenceSelect?.(evidenceItem.id);
  };

  const handleBackToGrid = () => {
    setSelectedEvidence(null);
    setViewMode('grid');
  };

  const handleAnalyze = (evidenceId: string) => {
    onEvidenceAnalyze?.(evidenceId);
    // Simulate analysis results
    setTimeout(() => {
      setAnalysisResults(prev => ({
        ...prev,
        [evidenceId]: {
          objects: Math.floor(Math.random() * 5) + 1,
          confidence: Math.random() * 0.3 + 0.7,
          processingTime: `${Math.random() * 2 + 0.5}s`
        }
      }));
    }, 1000);
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDuration = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const getTypeIcon = (type: string): string => {
    const icons = {
      image: '🖼️',
      video: '🎥',
      thermal: '🌡️',
      audio: '🎵'
    };
    return icons[type as keyof typeof icons] || '📄';
  };

  const getTypeColor = (type: string): string => {
    const colors = {
      image: 'bg-blue-100 text-blue-800',
      video: 'bg-purple-100 text-purple-800',
      thermal: 'bg-red-100 text-red-800',
      audio: 'bg-green-100 text-green-800'
    };
    return colors[type as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  if (evidence.length === 0) {
    return (
      <div className={`flex items-center justify-center h-64 bg-gray-50 rounded-lg ${className}`}>
        <div className="text-center text-gray-500">
          <div className="text-4xl mb-2">📎</div>
          <div className="text-sm">No evidence files</div>
        </div>
      </div>
    );
  }

  if (viewMode === 'detail' && selectedEvidence) {
    const analysis = analysisResults[selectedEvidence.id];

    return (
      <div className={`space-y-4 ${className}`}>
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <button
              onClick={handleBackToGrid}
              className="p-2 hover:bg-gray-100 rounded-full"
            >
              ←
            </button>
            <div>
              <h3 className="text-lg font-semibold">{selectedEvidence.type.charAt(0).toUpperCase() + selectedEvidence.type.slice(1)} Evidence</h3>
              <p className="text-sm text-gray-600">ID: {selectedEvidence.id}</p>
            </div>
          </div>

          {showAnalysis && (
            <button
              onClick={() => handleAnalyze(selectedEvidence.id)}
              disabled={!!analysis}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
            >
              {analysis ? 'Analyzed' : 'Analyze'}
            </button>
          )}
        </div>

        {/* Evidence display */}
        <div className="bg-black rounded-lg overflow-hidden">
          {selectedEvidence.type === 'image' && (
            <img
              src={selectedEvidence.url}
              alt="Evidence"
              className="w-full h-auto max-h-96 object-contain"
            />
          )}

          {selectedEvidence.type === 'video' && (
            <video
              ref={(el) => {
                if (el) videoRefs.current[selectedEvidence.id] = el;
              }}
              src={selectedEvidence.url}
              controls
              className="w-full h-auto max-h-96"
              onLoadedMetadata={() => {
                // Auto-play if duration is short
                const video = videoRefs.current[selectedEvidence.id];
                if (video && selectedEvidence.metadata?.duration && selectedEvidence.metadata.duration < 10) {
                  video.play();
                }
              }}
            />
          )}

          {selectedEvidence.type === 'thermal' && (
            <div className="w-full h-64 bg-gradient-to-br from-blue-900 via-purple-700 to-red-500 flex items-center justify-center text-white">
              <div className="text-center">
                <div className="text-4xl mb-2">🌡️</div>
                <div>Thermal Imaging Data</div>
                <div className="text-sm opacity-75">Heat signature analysis</div>
              </div>
            </div>
          )}

          {selectedEvidence.type === 'audio' && (
            <div className="w-full h-32 bg-gray-900 flex items-center justify-center">
              <audio
                src={selectedEvidence.url}
                controls
                className="w-full max-w-md"
              />
            </div>
          )}
        </div>

        {/* Metadata */}
        {showMetadata && (
          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="font-medium mb-3">Metadata</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Type:</span>
                <div className="font-medium capitalize">{selectedEvidence.type}</div>
              </div>

              <div>
                <span className="text-gray-600">Size:</span>
                <div className="font-medium">
                  {selectedEvidence.metadata?.fileSize
                    ? formatFileSize(selectedEvidence.metadata.fileSize)
                    : 'Unknown'
                  }
                </div>
              </div>

              {selectedEvidence.metadata?.duration && (
                <div>
                  <span className="text-gray-600">Duration:</span>
                  <div className="font-medium">
                    {formatDuration(selectedEvidence.metadata.duration)}
                  </div>
                </div>
              )}

              {selectedEvidence.metadata?.altitude && (
                <div>
                  <span className="text-gray-600">Altitude:</span>
                  <div className="font-medium">{selectedEvidence.metadata.altitude}m</div>
                </div>
              )}

              <div>
                <span className="text-gray-600">Timestamp:</span>
                <div className="font-medium">
                  {selectedEvidence.timestamp.toLocaleString()}
                </div>
              </div>

              {selectedEvidence.metadata?.cameraAngle && (
                <div>
                  <span className="text-gray-600">Camera Angle:</span>
                  <div className="font-medium">{selectedEvidence.metadata.cameraAngle}°</div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Analysis results */}
        {showAnalysis && analysis && (
          <div className="bg-blue-50 rounded-lg p-4">
            <h4 className="font-medium mb-3">Analysis Results</h4>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{analysis.objects}</div>
                <div className="text-gray-600">Objects Detected</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {Math.round(analysis.confidence * 100)}%
                </div>
                <div className="text-gray-600">Confidence</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">{analysis.processingTime}</div>
                <div className="text-gray-600">Processing Time</div>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // Grid view
  return (
    <div className={`${className}`}>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {evidence.map((item) => (
          <div
            key={item.id}
            className="border rounded-lg overflow-hidden cursor-pointer hover:shadow-lg transition-all"
            onClick={() => handleEvidenceClick(item)}
          >
            {/* Thumbnail */}
            <div className="relative bg-gray-100">
              {item.type === 'image' && (
                <img
                  src={item.thumbnail || item.url}
                  alt="Evidence thumbnail"
                  className="w-full h-32 object-cover"
                />
              )}

              {item.type === 'video' && (
                <div className="w-full h-32 bg-gray-900 flex items-center justify-center">
                  <video
                    src={item.url}
                    className="w-full h-32 object-cover"
                    muted
                    onMouseEnter={(e) => e.currentTarget.play()}
                    onMouseLeave={(e) => e.currentTarget.pause()}
                  />
                </div>
              )}

              {item.type === 'thermal' && (
                <div className="w-full h-32 bg-gradient-to-br from-blue-900 via-purple-700 to-red-500 flex items-center justify-center text-white">
                  <span className="text-2xl">🌡️</span>
                </div>
              )}

              {item.type === 'audio' && (
                <div className="w-full h-32 bg-gray-800 flex items-center justify-center text-white">
                  <span className="text-2xl">🎵</span>
                </div>
              )}

              {/* Type badge */}
              <div className={`absolute top-2 left-2 px-2 py-1 text-xs rounded-full ${getTypeColor(item.type)}`}>
                {getTypeIcon(item.type)} {item.type}
              </div>

              {/* Duration for video */}
              {item.type === 'video' && item.metadata?.duration && (
                <div className="absolute bottom-2 right-2 px-2 py-1 text-xs bg-black bg-opacity-75 text-white rounded">
                  {formatDuration(item.metadata.duration)}
                </div>
              )}
            </div>

            {/* Info */}
            <div className="p-3">
              <div className="text-sm font-medium truncate" title={item.url}>
                Evidence {item.id.slice(-8)}
              </div>
              <div className="text-xs text-gray-600 mt-1">
                {item.timestamp.toLocaleDateString()}
              </div>
              {item.metadata?.fileSize && (
                <div className="text-xs text-gray-500">
                  {formatFileSize(item.metadata.fileSize)}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};