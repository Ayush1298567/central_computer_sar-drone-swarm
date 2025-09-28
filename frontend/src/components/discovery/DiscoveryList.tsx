/**
 * Discovery List Component
 * Discovery management interface with sorting and filtering
 */

import React, { useState, useMemo } from 'react';
import { Discovery } from '../../types';

interface DiscoveryListProps {
  discoveries: Discovery[];
  onDiscoverySelect?: (discoveryId: string) => void;
  onStatusUpdate?: (discoveryId: string, status: Discovery['status']) => void;
  onPriorityUpdate?: (discoveryId: string, priority: Discovery['priority']) => void;
  compact?: boolean;
  showFilters?: boolean;
  maxItems?: number;
  className?: string;
}

export const DiscoveryList: React.FC<DiscoveryListProps> = ({
  discoveries,
  onDiscoverySelect,
  onStatusUpdate,
  onPriorityUpdate,
  compact = false,
  showFilters = true,
  maxItems = 50,
  className = ''
}) => {
  const [filterPriority, setFilterPriority] = useState<Discovery['priority'] | 'all'>('all');
  const [filterStatus, setFilterStatus] = useState<Discovery['status'] | 'all'>('all');
  const [filterType, setFilterType] = useState<Discovery['type'] | 'all'>('all');
  const [sortBy, setSortBy] = useState<'timestamp' | 'priority' | 'confidence' | 'type'>('timestamp');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [selectedDiscovery, setSelectedDiscovery] = useState<string | null>(null);

  // Filter and sort discoveries
  const filteredAndSortedDiscoveries = useMemo(() => {
    let filtered = discoveries.filter(discovery => {
      if (filterPriority !== 'all' && discovery.priority !== filterPriority) return false;
      if (filterStatus !== 'all' && discovery.status !== filterStatus) return false;
      if (filterType !== 'all' && discovery.type !== filterType) return false;
      return true;
    });

    // Sort
    filtered.sort((a, b) => {
      let aValue: any, bValue: any;

      switch (sortBy) {
        case 'timestamp':
          aValue = a.timestamp.getTime();
          bValue = b.timestamp.getTime();
          break;
        case 'priority':
          const priorityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
          aValue = priorityOrder[a.priority];
          bValue = priorityOrder[b.priority];
          break;
        case 'confidence':
          aValue = a.confidence;
          bValue = b.confidence;
          break;
        case 'type':
          aValue = a.type;
          bValue = b.type;
          break;
        default:
          return 0;
      }

      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

    return filtered.slice(0, maxItems);
  }, [discoveries, filterPriority, filterStatus, filterType, sortBy, sortOrder, maxItems]);

  const handleDiscoveryClick = (discoveryId: string) => {
    setSelectedDiscovery(selectedDiscovery === discoveryId ? null : discoveryId);
    onDiscoverySelect?.(discoveryId);
  };

  const handleStatusChange = (discoveryId: string, newStatus: Discovery['status']) => {
    onStatusUpdate?.(discoveryId, newStatus);
  };

  const handlePriorityChange = (discoveryId: string, newPriority: Discovery['priority']) => {
    onPriorityUpdate?.(discoveryId, newPriority);
  };

  const getPriorityColor = (priority: string): string => {
    const colors = {
      critical: 'bg-red-100 text-red-800 border-red-200',
      high: 'bg-orange-100 text-orange-800 border-orange-200',
      medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      low: 'bg-blue-100 text-blue-800 border-blue-200'
    };
    return colors[priority as keyof typeof colors] || colors.medium;
  };

  const getStatusColor = (status: string): string => {
    const colors = {
      new: 'bg-green-100 text-green-800',
      investigating: 'bg-blue-100 text-blue-800',
      confirmed: 'bg-purple-100 text-purple-800',
      false_positive: 'bg-gray-100 text-gray-800'
    };
    return colors[status as keyof typeof colors] || colors.new;
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
    return date.toLocaleString([], {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (discoveries.length === 0) {
    return (
      <div className={`flex items-center justify-center h-32 bg-gray-50 rounded-lg ${className}`}>
        <div className="text-center text-gray-500">
          <div className="text-3xl mb-2">🔍</div>
          <div className="text-sm">No discoveries yet</div>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Filters and sorting */}
      {showFilters && (
        <div className="bg-white border rounded-lg p-3 space-y-3">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {/* Priority filter */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Priority</label>
              <select
                value={filterPriority}
                onChange={(e) => setFilterPriority(e.target.value as Discovery['priority'] | 'all')}
                className="w-full text-xs border rounded px-2 py-1"
              >
                <option value="all">All Priorities</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>

            {/* Status filter */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Status</label>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value as Discovery['status'] | 'all')}
                className="w-full text-xs border rounded px-2 py-1"
              >
                <option value="all">All Status</option>
                <option value="new">New</option>
                <option value="investigating">Investigating</option>
                <option value="confirmed">Confirmed</option>
                <option value="false_positive">False Positive</option>
              </select>
            </div>

            {/* Type filter */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Type</label>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value as Discovery['type'] | 'all')}
                className="w-full text-xs border rounded px-2 py-1"
              >
                <option value="all">All Types</option>
                <option value="person">Person</option>
                <option value="vehicle">Vehicle</option>
                <option value="structure">Structure</option>
                <option value="debris">Debris</option>
                <option value="other">Other</option>
              </select>
            </div>

            {/* Sort by */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Sort By</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
                className="w-full text-xs border rounded px-2 py-1"
              >
                <option value="timestamp">Time</option>
                <option value="priority">Priority</option>
                <option value="confidence">Confidence</option>
                <option value="type">Type</option>
              </select>
            </div>
          </div>

          {/* Results count */}
          <div className="text-xs text-gray-600">
            Showing {filteredAndSortedDiscoveries.length} of {discoveries.length} discoveries
          </div>
        </div>
      )}

      {/* Discovery list */}
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {filteredAndSortedDiscoveries.map((discovery) => (
          <div
            key={discovery.id}
            className={`border rounded-lg p-3 cursor-pointer transition-all ${
              selectedDiscovery === discovery.id
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
            onClick={() => handleDiscoveryClick(discovery.id)}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                {/* Header */}
                <div className="flex items-center space-x-2 mb-2">
                  <span className="text-base">{getTypeIcon(discovery.type)}</span>
                  <span className="font-medium text-sm capitalize">{discovery.type}</span>
                  <span className={`px-2 py-1 text-xs rounded-full border ${getPriorityColor(discovery.priority)}`}>
                    {discovery.priority}
                  </span>
                  <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(discovery.status)}`}>
                    {discovery.status.replace('_', ' ')}
                  </span>
                </div>

                {/* Details */}
                {!compact && (
                  <div className="space-y-1 text-xs text-gray-600">
                    <div className="flex items-center space-x-4">
                      <span>Confidence: {Math.round(discovery.confidence * 100)}%</span>
                      <span>Time: {formatTime(discovery.timestamp)}</span>
                    </div>

                    {discovery.description && (
                      <div className="mt-1 text-gray-700">
                        {discovery.description}
                      </div>
                    )}

                    {discovery.evidence.length > 0 && (
                      <div className="flex items-center space-x-1 mt-1">
                        <span>📎</span>
                        <span>{discovery.evidence.length} evidence file{discovery.evidence.length !== 1 ? 's' : ''}</span>
                      </div>
                    )}
                  </div>
                )}

                {/* Compact view */}
                {compact && (
                  <div className="flex items-center space-x-2 text-xs text-gray-600">
                    <span>{Math.round(discovery.confidence * 100)}%</span>
                    <span>•</span>
                    <span>{formatTime(discovery.timestamp)}</span>
                    {discovery.evidence.length > 0 && (
                      <>
                        <span>•</span>
                        <span>{discovery.evidence.length} files</span>
                      </>
                    )}
                  </div>
                )}
              </div>

              {/* Actions */}
              {selectedDiscovery === discovery.id && (
                <div className="ml-3 flex flex-col space-y-1">
                  {/* Status update */}
                  <select
                    value={discovery.status}
                    onChange={(e) => handleStatusChange(discovery.id, e.target.value as Discovery['status'])}
                    className="text-xs border rounded px-2 py-1"
                  >
                    <option value="new">New</option>
                    <option value="investigating">Investigating</option>
                    <option value="confirmed">Confirmed</option>
                    <option value="false_positive">False Positive</option>
                  </select>

                  {/* Priority update */}
                  <select
                    value={discovery.priority}
                    onChange={(e) => handlePriorityChange(discovery.id, e.target.value as Discovery['priority'])}
                    className="text-xs border rounded px-2 py-1"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};