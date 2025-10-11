import React, { useState, useEffect } from 'react';
import { Discovery } from '../../types/api';
import { DiscoveryAlert as DiscoveryAlertType } from '../../types/discovery';

interface DiscoveryAlertProps {
  discovery: Discovery;
  alertType: DiscoveryAlertType['type'];
  onAcknowledge?: (discoveryId: string) => void;
  onInvestigate?: (discoveryId: string) => void;
  onDismiss?: (discoveryId: string) => void;
  autoHide?: boolean;
  autoHideDelay?: number;
}

const DiscoveryAlert: React.FC<DiscoveryAlertProps> = ({
  discovery,
  alertType,
  onAcknowledge,
  onInvestigate,
  onDismiss,
  autoHide = false,
  autoHideDelay = 10000,
}) => {
  const [isVisible, setIsVisible] = useState(true);
  const [isAcknowledged, setIsAcknowledged] = useState(false);

  // Auto-hide functionality
  useEffect(() => {
    if (autoHide && autoHideDelay > 0) {
      const timer = setTimeout(() => {
        setIsVisible(false);
        onDismiss?.(discovery.id);
      }, autoHideDelay);

      return () => clearTimeout(timer);
    }
  }, [autoHide, autoHideDelay, discovery.id, onDismiss]);

  const handleAcknowledge = () => {
    setIsAcknowledged(true);
    onAcknowledge?.(discovery.id);
  };

  const handleInvestigate = () => {
    onInvestigate?.(discovery.id);
  };

  const handleDismiss = () => {
    setIsVisible(false);
    onDismiss?.(discovery.id);
  };

  const getAlertStyles = () => {
    const baseStyles = "p-4 rounded-lg border-l-4 shadow-lg transition-all duration-300";

    switch (alertType) {
      case 'new_discovery':
        return `${baseStyles} bg-blue-900 border-blue-500`;
      case 'priority_upgrade':
        return `${baseStyles} bg-yellow-900 border-yellow-500`;
      case 'investigation_complete':
        return `${baseStyles} bg-green-900 border-green-500`;
      default:
        return `${baseStyles} bg-gray-900 border-gray-500`;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'text-red-400';
      case 'high': return 'text-orange-400';
      case 'medium': return 'text-yellow-400';
      case 'low': return 'text-green-400';
      default: return 'text-gray-400';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'person': return '👤';
      case 'vehicle': return '🚗';
      case 'structure': return '🏢';
      case 'signal': return '📡';
      case 'animal': return '🐕';
      default: return '❓';
    }
  };

  if (!isVisible) return null;

  return (
    <div className={getAlertStyles()}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          {/* Header */}
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl">{getTypeIcon(discovery.type)}</span>
            <div>
              <h3 className="font-semibold text-lg">
                New {discovery.type} Discovery
              </h3>
              <p className="text-sm text-gray-300">
                {new Date(discovery.timestamp).toLocaleString()}
              </p>
            </div>
            <div className={`px-2 py-1 rounded text-xs font-medium ${getPriorityColor(discovery.priority)}`}>
              {discovery.priority.toUpperCase()}
            </div>
          </div>

          {/* Description */}
          <p className="text-gray-200 mb-3">
            {discovery.description}
          </p>

          {/* Location */}
          <div className="text-sm text-gray-400 mb-3">
            <strong>Location:</strong> {discovery.location.lat.toFixed(6)}, {discovery.location.lng.toFixed(6)}
            {discovery.location.altitude && (
              <span> • {discovery.location.altitude.toFixed(1)}m altitude</span>
            )}
          </div>

          {/* Evidence Count */}
          {discovery.evidence.length > 0 && (
            <div className="text-sm text-gray-400 mb-3">
              <strong>Evidence:</strong> {discovery.evidence.length} file{discovery.evidence.length !== 1 ? 's' : ''}
            </div>
          )}

          {/* Alert Type Badge */}
          <div className="flex items-center gap-2 mb-3">
            <span className="text-xs bg-gray-700 px-2 py-1 rounded">
              {alertType.replace('_', ' ').toUpperCase()}
            </span>
            <span className="text-xs text-gray-400">
              Confidence: {Math.round(discovery.confidence * 100)}%
            </span>
          </div>

          {/* Tags */}
          {discovery.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mb-3">
              {discovery.tags.map((tag, index) => (
                <span
                  key={index}
                  className="text-xs bg-gray-700 text-gray-300 px-2 py-1 rounded"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Status Indicator */}
        <div className="ml-4">
          <div className={`
            w-3 h-3 rounded-full
            ${discovery.status === 'new' ? 'bg-blue-500 animate-pulse' :
              discovery.status === 'investigating' ? 'bg-yellow-500' :
              discovery.status === 'confirmed' ? 'bg-green-500' :
              discovery.status === 'false_positive' ? 'bg-red-500' : 'bg-gray-500'}
          `} />
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-between items-center mt-4 pt-3 border-t border-gray-600">
        <div className="flex gap-2">
          {!isAcknowledged && (
            <button
              onClick={handleAcknowledge}
              className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm transition-colors"
            >
              Acknowledge
            </button>
          )}

          <button
            onClick={handleInvestigate}
            className="px-3 py-1 bg-purple-600 hover:bg-purple-700 rounded text-sm transition-colors"
          >
            Investigate
          </button>
        </div>

        <button
          onClick={handleDismiss}
          className="px-3 py-1 bg-gray-600 hover:bg-gray-700 rounded text-sm transition-colors"
        >
          Dismiss
        </button>
      </div>

      {/* Acknowledged State */}
      {isAcknowledged && (
        <div className="mt-3 pt-3 border-t border-gray-600">
          <div className="flex items-center gap-2 text-green-400 text-sm">
            <span>✓</span>
            <span>Acknowledged</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default DiscoveryAlert;