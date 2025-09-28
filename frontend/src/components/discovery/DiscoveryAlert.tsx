/**
 * Discovery Alert Component
 * Real-time discovery notification with auto-dismiss
 */

import React, { useState, useEffect } from 'react';
import { Discovery } from '../../types';

interface DiscoveryAlertProps {
  discovery: Discovery;
  onDismiss: () => void;
  onInvestigate?: (discoveryId: string) => void;
  autoHideDelay?: number; // in milliseconds
  className?: string;
}

export const DiscoveryAlert: React.FC<DiscoveryAlertProps> = ({
  discovery,
  onDismiss,
  onInvestigate,
  autoHideDelay = 5000,
  className = ''
}) => {
  const [timeLeft, setTimeLeft] = useState(autoHideDelay / 1000);
  const [isVisible, setIsVisible] = useState(true);

  // Auto-hide countdown
  useEffect(() => {
    if (autoHideDelay <= 0) return;

    const timer = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          setIsVisible(false);
          setTimeout(onDismiss, 300); // Allow fade out animation
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [autoHideDelay, onDismiss]);

  const handleDismiss = () => {
    setIsVisible(false);
    setTimeout(onDismiss, 300);
  };

  const handleInvestigate = () => {
    onInvestigate?.(discovery.id);
    handleDismiss();
  };

  const getPriorityColor = (priority: string): string => {
    const colors = {
      critical: 'border-red-500 bg-red-50',
      high: 'border-orange-500 bg-orange-50',
      medium: 'border-yellow-500 bg-yellow-50',
      low: 'border-blue-500 bg-blue-50'
    };
    return colors[priority as keyof typeof colors] || colors.medium;
  };

  const getPriorityIcon = (priority: string): string => {
    const icons = {
      critical: '🚨',
      high: '⚠️',
      medium: 'ℹ️',
      low: '📍'
    };
    return icons[priority as keyof typeof icons] || icons.medium;
  };

  const getTypeIcon = (type: string): string => {
    const icons = {
      person: '👤',
      vehicle: '🚗',
      structure: '🏢',
      debris: '📦',
      other: '❓'
    };
    return icons[type as keyof typeof icons] || icons.other;
  };

  const formatTime = (date: Date): string => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  if (!isVisible) {
    return null;
  }

  return (
    <div
      className={`border-l-4 p-4 rounded-r-lg shadow-lg transition-all duration-300 ${getPriorityColor(
        discovery.priority
      )} ${className} ${!isVisible ? 'opacity-0 transform translate-x-full' : 'opacity-100 transform translate-x-0'}`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          {/* Header */}
          <div className="flex items-center space-x-2 mb-2">
            <span className="text-lg">{getPriorityIcon(discovery.priority)}</span>
            <span className="font-semibold text-sm uppercase tracking-wide">
              {discovery.priority} {discovery.type}
            </span>
            <span className="text-xs text-gray-500">
              {formatTime(discovery.timestamp)}
            </span>
          </div>

          {/* Content */}
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="text-base">{getTypeIcon(discovery.type)}</span>
              <span className="text-sm font-medium">
                Potential {discovery.type} detected
              </span>
            </div>

            <div className="text-xs text-gray-600">
              Confidence: <span className="font-medium">{Math.round(discovery.confidence * 100)}%</span>
            </div>

            {discovery.description && (
              <div className="text-xs text-gray-700 mt-1">
                {discovery.description}
              </div>
            )}

            {/* Progress bar for auto-hide */}
            {autoHideDelay > 0 && (
              <div className="mt-2">
                <div className="w-full bg-gray-200 rounded-full h-1">
                  <div
                    className="bg-current h-1 rounded-full transition-all duration-1000 ease-linear"
                    style={{
                      width: `${(timeLeft / (autoHideDelay / 1000)) * 100}%`,
                      backgroundColor: discovery.priority === 'critical' ? '#ef4444' :
                                     discovery.priority === 'high' ? '#f97316' :
                                     discovery.priority === 'medium' ? '#eab308' : '#3b82f6'
                    }}
                  ></div>
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  Auto-dismiss in {timeLeft}s
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-col space-y-1 ml-3">
          {onInvestigate && (
            <button
              onClick={handleInvestigate}
              className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
            >
              Investigate
            </button>
          )}
          <button
            onClick={handleDismiss}
            className="px-2 py-1 text-xs text-gray-600 hover:text-gray-800 transition-colors"
            title="Dismiss alert"
          >
            ✕
          </button>
        </div>
      </div>

      {/* Evidence count */}
      {discovery.evidence.length > 0 && (
        <div className="mt-2 pt-2 border-t border-gray-200">
          <div className="flex items-center space-x-1 text-xs text-gray-600">
            <span>📎</span>
            <span>{discovery.evidence.length} evidence file{discovery.evidence.length !== 1 ? 's' : ''}</span>
          </div>
        </div>
      )}
    </div>
  );
};