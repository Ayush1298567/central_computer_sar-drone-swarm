import React, { useState, useMemo } from 'react';
import { Discovery } from '../../types/api';

interface DiscoveryListProps {
  discoveries: Discovery[];
  onDiscoverySelect?: (discovery: Discovery) => void;
  onStatusChange?: (discoveryId: string, status: Discovery['status']) => void;
  onPriorityChange?: (discoveryId: string, priority: Discovery['priority']) => void;
  selectedDiscoveryId?: string;
  filterByStatus?: Discovery['status'][];
  filterByPriority?: Discovery['priority'][];
  filterByType?: Discovery['type'][];
  sortBy?: 'timestamp' | 'priority' | 'confidence' | 'type';
  sortOrder?: 'asc' | 'desc';
  showEvidenceCount?: boolean;
  compactView?: boolean;
}

const DiscoveryList: React.FC<DiscoveryListProps> = ({
  discoveries,
  onDiscoverySelect,
  onStatusChange,
  onPriorityChange,
  selectedDiscoveryId,
  filterByStatus,
  filterByPriority,
  filterByType,
  sortBy = 'timestamp',
  sortOrder = 'desc',
  showEvidenceCount = true,
  compactView = false,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<Discovery['status'] | 'all'>('all');
  const [priorityFilter, setPriorityFilter] = useState<Discovery['priority'] | 'all'>('all');
  const [typeFilter, setTypeFilter] = useState<Discovery['type'] | 'all'>('all');

  // Filter and sort discoveries
  const filteredAndSortedDiscoveries = useMemo(() => {
    let filtered = discoveries.filter(discovery => {
      // Text search
      if (searchTerm && !discovery.description.toLowerCase().includes(searchTerm.toLowerCase())) {
        return false;
      }

      // Status filter
      if (statusFilter !== 'all' && discovery.status !== statusFilter) {
        return false;
      }

      // Priority filter
      if (priorityFilter !== 'all' && discovery.priority !== priorityFilter) {
        return false;
      }

      // Type filter
      if (typeFilter !== 'all' && discovery.type !== typeFilter) {
        return false;
      }

      // External filters
      if (filterByStatus && !filterByStatus.includes(discovery.status)) {
        return false;
      }

      if (filterByPriority && !filterByPriority.includes(discovery.priority)) {
        return false;
      }

      if (filterByType && !filterByType.includes(discovery.type)) {
        return false;
      }

      return true;
    });

    // Sort discoveries
    filtered.sort((a, b) => {
      let aValue: any, bValue: any;

      switch (sortBy) {
        case 'timestamp':
          aValue = a.timestamp;
          bValue = b.timestamp;
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
          aValue = a.timestamp;
          bValue = b.timestamp;
      }

      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

    return filtered;
  }, [discoveries, searchTerm, statusFilter, priorityFilter, typeFilter, sortBy, sortOrder, filterByStatus, filterByPriority, filterByType]);

  const getStatusColor = (status: Discovery['status']) => {
    switch (status) {
      case 'new': return 'bg-blue-600';
      case 'investigating': return 'bg-yellow-600';
      case 'confirmed': return 'bg-green-600';
      case 'false_positive': return 'bg-red-600';
      case 'resolved': return 'bg-gray-600';
      default: return 'bg-gray-600';
    }
  };

  const getPriorityColor = (priority: Discovery['priority']) => {
    switch (priority) {
      case 'critical': return 'text-red-400';
      case 'high': return 'text-orange-400';
      case 'medium': return 'text-yellow-400';
      case 'low': return 'text-green-400';
      default: return 'text-gray-400';
    }
  };

  const getTypeIcon = (type: Discovery['type']) => {
    switch (type) {
      case 'person': return '👤';
      case 'vehicle': return '🚗';
      case 'structure': return '🏢';
      case 'signal': return '📡';
      case 'animal': return '🐕';
      case 'other': return '❓';
      default: return '❓';
    }
  };

  const formatTimestamp = (timestamp: number) => {
    const now = Date.now();
    const diff = now - timestamp;

    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return new Date(timestamp).toLocaleDateString();
  };

  if (discoveries.length === 0) {
    return (
      <div className="text-center text-gray-500 py-8">
        <div className="text-4xl mb-2">🔍</div>
        <p>No discoveries found</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Filters and Search */}
      <div className="space-y-2">
        {/* Search */}
        <input
          type="text"
          placeholder="Search discoveries..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />

        {/* Filter Controls */}
        <div className="flex flex-wrap gap-2">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as Discovery['status'] | 'all')}
            className="px-2 py-1 bg-gray-700 border border-gray-600 rounded text-sm"
          >
            <option value="all">All Status</option>
            <option value="new">New</option>
            <option value="investigating">Investigating</option>
            <option value="confirmed">Confirmed</option>
            <option value="false_positive">False Positive</option>
            <option value="resolved">Resolved</option>
          </select>

          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value as Discovery['priority'] | 'all')}
            className="px-2 py-1 bg-gray-700 border border-gray-600 rounded text-sm"
          >
            <option value="all">All Priority</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>

          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value as Discovery['type'] | 'all')}
            className="px-2 py-1 bg-gray-700 border border-gray-600 rounded text-sm"
          >
            <option value="all">All Types</option>
            <option value="person">Person</option>
            <option value="vehicle">Vehicle</option>
            <option value="structure">Structure</option>
            <option value="signal">Signal</option>
            <option value="animal">Animal</option>
            <option value="other">Other</option>
          </select>
        </div>
      </div>

      {/* Results Count */}
      <div className="text-sm text-gray-400">
        Showing {filteredAndSortedDiscoveries.length} of {discoveries.length} discoveries
      </div>

      {/* Discovery List */}
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {filteredAndSortedDiscoveries.map((discovery) => (
          <div
            key={discovery.id}
            className={`
              p-3 rounded-lg border cursor-pointer transition-all
              ${selectedDiscoveryId === discovery.id
                ? 'bg-blue-900 border-blue-500'
                : 'bg-gray-800 border-gray-700 hover:bg-gray-750'
              }
            `}
            onClick={() => onDiscoverySelect?.(discovery)}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3 flex-1">
                {/* Type Icon */}
                <span className="text-xl">{getTypeIcon(discovery.type)}</span>

                <div className="flex-1 min-w-0">
                  {/* Header */}
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium capitalize">{discovery.type}</span>
                    <span className={`px-2 py-0.5 rounded text-xs ${getPriorityColor(discovery.priority)}`}>
                      {discovery.priority}
                    </span>
                    <span className={`w-2 h-2 rounded-full ${getStatusColor(discovery.status)}`} />
                  </div>

                  {/* Description */}
                  <p className="text-sm text-gray-300 mb-2 line-clamp-2">
                    {discovery.description}
                  </p>

                  {/* Metadata */}
                  <div className="flex items-center gap-4 text-xs text-gray-400">
                    <span>{formatTimestamp(discovery.timestamp)}</span>
                    <span>Confidence: {Math.round(discovery.confidence * 100)}%</span>
                    {showEvidenceCount && (
                      <span>{discovery.evidence.length} evidence</span>
                    )}
                  </div>

                  {/* Location */}
                  <div className="text-xs text-gray-500 mt-1">
                    {discovery.location.lat.toFixed(6)}, {discovery.location.lng.toFixed(6)}
                  </div>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="flex flex-col gap-1 ml-2">
                <select
                  value={discovery.status}
                  onChange={(e) => onStatusChange?.(discovery.id, e.target.value as Discovery['status'])}
                  className="text-xs bg-gray-700 border border-gray-600 rounded px-1 py-0.5"
                >
                  <option value="new">New</option>
                  <option value="investigating">Investigating</option>
                  <option value="confirmed">Confirmed</option>
                  <option value="false_positive">False Positive</option>
                  <option value="resolved">Resolved</option>
                </select>
              </div>
            </div>
          </div>
        ))}
      </div>

      {filteredAndSortedDiscoveries.length === 0 && (
        <div className="text-center text-gray-500 py-8">
          <div className="text-4xl mb-2">🔍</div>
          <p>No discoveries match the current filters</p>
        </div>
      )}
    </div>
  );
};

export default DiscoveryList;