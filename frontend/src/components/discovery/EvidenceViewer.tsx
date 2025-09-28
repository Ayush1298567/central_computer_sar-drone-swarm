import React, { useState } from 'react';
import { Evidence } from '../../types/api';

interface EvidenceViewerProps {
  evidence: Evidence[];
  selectedEvidenceId?: string;
  onEvidenceSelect?: (evidence: Evidence) => void;
  onEvidenceDelete?: (evidenceId: string) => void;
  showMetadata?: boolean;
  allowDownload?: boolean;
  compactView?: boolean;
}

const EvidenceViewer: React.FC<EvidenceViewerProps> = ({
  evidence,
  selectedEvidenceId,
  onEvidenceSelect,
  onEvidenceDelete,
  showMetadata = true,
  allowDownload = true,
  compactView = false,
}) => {
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [filterType, setFilterType] = useState<Evidence['type'] | 'all'>('all');

  const filteredEvidence = evidence.filter(item =>
    filterType === 'all' || item.type === filterType
  );

  const getTypeIcon = (type: Evidence['type']) => {
    switch (type) {
      case 'image': return '🖼️';
      case 'video': return '🎥';
      case 'audio': return '🎵';
      case 'thermal': return '🌡️';
      case 'sensor': return '📊';
      default: return '📄';
    }
  };

  const getTypeColor = (type: Evidence['type']) => {
    switch (type) {
      case 'image': return 'bg-green-600';
      case 'video': return 'bg-blue-600';
      case 'audio': return 'bg-purple-600';
      case 'thermal': return 'bg-orange-600';
      case 'sensor': return 'bg-gray-600';
      default: return 'bg-gray-600';
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleDownload = async (evidence: Evidence) => {
    try {
      const response = await fetch(evidence.url);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = evidence.metadata?.filename || `evidence-${evidence.id}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error downloading evidence:', error);
    }
  };

  if (evidence.length === 0) {
    return (
      <div className="text-center text-gray-500 py-8">
        <div className="text-4xl mb-2">📁</div>
        <p>No evidence available</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex justify-between items-center">
        <div className="flex gap-2">
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value as Evidence['type'] | 'all')}
            className="px-2 py-1 bg-gray-700 border border-gray-600 rounded text-sm"
          >
            <option value="all">All Types</option>
            <option value="image">Images</option>
            <option value="video">Videos</option>
            <option value="audio">Audio</option>
            <option value="thermal">Thermal</option>
            <option value="sensor">Sensor Data</option>
          </select>

          <div className="flex border border-gray-600 rounded">
            <button
              onClick={() => setViewMode('grid')}
              className={`px-3 py-1 text-sm ${viewMode === 'grid' ? 'bg-blue-600' : 'bg-gray-700'}`}
            >
              Grid
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`px-3 py-1 text-sm ${viewMode === 'list' ? 'bg-blue-600' : 'bg-gray-700'}`}
            >
              List
            </button>
          </div>
        </div>

        <div className="text-sm text-gray-400">
          {filteredEvidence.length} of {evidence.length} files
        </div>
      </div>

      {/* Evidence Display */}
      {viewMode === 'grid' ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {filteredEvidence.map((item) => (
            <div
              key={item.id}
              className={`
                relative bg-gray-800 rounded-lg overflow-hidden cursor-pointer transition-all
                ${selectedEvidenceId === item.id ? 'ring-2 ring-blue-500' : 'hover:bg-gray-750'}
              `}
              onClick={() => onEvidenceSelect?.(item)}
            >
              {/* Thumbnail */}
              <div className="aspect-video bg-gray-700 flex items-center justify-center">
                {item.type === 'image' ? (
                  <img
                    src={item.thumbnail_url || item.url}
                    alt="Evidence"
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="text-center">
                    <span className="text-3xl">{getTypeIcon(item.type)}</span>
                    <div className="text-xs text-gray-400 mt-1">
                      {item.type.toUpperCase()}
                    </div>
                  </div>
                )}
              </div>

              {/* Type Badge */}
              <div className="absolute top-2 left-2">
                <span className={`px-2 py-1 rounded text-xs text-white ${getTypeColor(item.type)}`}>
                  {item.type}
                </span>
              </div>

              {/* Duration for videos */}
              {item.metadata?.duration && (
                <div className="absolute bottom-2 right-2 bg-black bg-opacity-75 px-1 rounded text-xs">
                  {formatDuration(item.metadata.duration)}
                </div>
              )}

              {/* Metadata Overlay */}
              {showMetadata && (
                <div className="absolute inset-0 bg-black bg-opacity-0 hover:bg-opacity-75 transition-all flex items-end p-2">
                  <div className="text-xs text-white">
                    <div>{formatFileSize(item.metadata?.size || 0)}</div>
                    <div>{new Date(item.timestamp).toLocaleDateString()}</div>
                  </div>
                </div>
              )}

              {/* Download Button */}
              {allowDownload && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDownload(item);
                  }}
                  className="absolute top-2 right-2 w-6 h-6 bg-black bg-opacity-50 hover:bg-opacity-75 rounded flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity"
                >
                  ⬇️
                </button>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-2">
          {filteredEvidence.map((item) => (
            <div
              key={item.id}
              className={`
                flex items-center gap-3 p-3 bg-gray-800 rounded-lg cursor-pointer transition-all
                ${selectedEvidenceId === item.id ? 'bg-blue-900' : 'hover:bg-gray-750'}
              `}
              onClick={() => onEvidenceSelect?.(item)}
            >
              {/* Type Icon */}
              <span className="text-xl">{getTypeIcon(item.type)}</span>

              {/* File Info */}
              <div className="flex-1 min-w-0">
                <div className="font-medium truncate">
                  {item.metadata?.filename || `Evidence ${item.id.slice(-8)}`}
                </div>
                <div className="text-sm text-gray-400">
                  {formatFileSize(item.metadata?.size || 0)} • {new Date(item.timestamp).toLocaleDateString()}
                </div>
                {item.metadata?.duration && (
                  <div className="text-sm text-gray-400">
                    Duration: {formatDuration(item.metadata.duration)}
                  </div>
                )}
              </div>

              {/* Type Badge */}
              <span className={`px-2 py-1 rounded text-xs text-white ${getTypeColor(item.type)}`}>
                {item.type}
              </span>

              {/* Actions */}
              <div className="flex gap-1">
                {allowDownload && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDownload(item);
                    }}
                    className="p-1 hover:bg-gray-700 rounded"
                    title="Download"
                  >
                    ⬇️
                  </button>
                )}
                {onEvidenceDelete && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onEvidenceDelete(item.id);
                    }}
                    className="p-1 hover:bg-red-700 rounded text-red-400"
                    title="Delete"
                  >
                    🗑️
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {filteredEvidence.length === 0 && (
        <div className="text-center text-gray-500 py-8">
          <div className="text-4xl mb-2">🔍</div>
          <p>No evidence matches the current filter</p>
        </div>
      )}
    </div>
  );
};

export default EvidenceViewer;