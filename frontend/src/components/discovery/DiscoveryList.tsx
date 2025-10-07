import React, { useState, useMemo } from 'react';
import { Discovery } from '../../types/discovery';

interface DiscoveryListProps {
  discoveries: Discovery[];
  onDiscoverySelect?: (discovery: Discovery) => void;
  onStatusChange?: (discoveryId: number, status: Discovery['status']) => void;
  onPriorityChange?: (discoveryId: number, priority: Discovery['priority']) => void;
  selectedDiscoveryId?: number;
  filterByStatus?: Discovery['status'][];
  filterByPriority?: Discovery['priority'][];
  filterByType?: string[];
  sortBy?: 'timestamp' | 'priority' | 'confidence' | 'type';
  sortOrder?: 'asc' | 'desc';
  showEvidenceCount?: boolean;
  compactView?: boolean;
  className?: string;
}

const DiscoveryList: React.FC<DiscoveryListProps> = ({
  discoveries,
  onDiscoverySelect,
  onStatusChange,
  selectedDiscoveryId,
  filterByStatus,
  filterByPriority,
  filterByType,
  sortBy = 'timestamp',
  sortOrder = 'desc',
  showEvidenceCount = true,
  compactView = false,
  className = ''
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<Discovery['status'] | 'all'>('all');
  const [priorityFilter, setPriorityFilter] = useState<Discovery['priority'] | 'all'>('all');
  const [typeFilter, setTypeFilter] = useState<string | 'all'>('all');

  // Filter and sort discoveries
  const filteredAndSortedDiscoveries = useMemo(() => {
    let filtered = discoveries.filter(discovery => {
      // Text search
      if (searchTerm && !discovery.description?.toLowerCase().includes(searchTerm.toLowerCase())) {
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
      if (typeFilter !== 'all' && discovery.discovery_type !== typeFilter) {
        return false;
      }

      // External filters
      if (filterByStatus && !filterByStatus.includes(discovery.status)) {
        return false;
      }

      if (filterByPriority && !filterByPriority.includes(discovery.priority)) {
        return false;
      }

      if (filterByType && !filterByType.includes(discovery.discovery_type)) {
        return false;
      }

      return true;
    });

    // Sort discoveries
    filtered.sort((a, b) => {
      let aValue: any, bValue: any;

      switch (sortBy) {
        case 'timestamp':
          aValue = new Date(a.created_at).getTime();
          bValue = new Date(b.created_at).getTime();
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
          aValue = a.discovery_type;
          bValue = b.discovery_type;
          break;
        default:
          aValue = new Date(a.created_at).getTime();
          bValue = new Date(b.created_at).getTime();
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
      case 'pending': return 'bg-blue-600';
      case 'investigating': return 'bg-yellow-600';
      case 'resolved': return 'bg-green-600';
      case 'false_positive': return 'bg-red-600';
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

  const getTypeIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'person': return '👤';
      case 'vehicle': return '🚗';
      case 'structure': return '🏢';
      case 'signal': return '📡';
      case 'animal': return '🐕';
      case 'debris': return '📦';
      case 'other': return '❓';
      default: return '❓';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const now = Date.now();
    const diff = now - new Date(timestamp).getTime();

    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return new Date(timestamp).toLocaleDateString();
  };

  if (discoveries.length === 0) {
    return (
      <div className={`text-center text-gray-500 py-8 ${className}`}>
        <div className="text-4xl mb-2">🔍</div>
        <p>No discoveries found</p>
      </div>
    );
  }

  return (
    <div className={`space-y-3 ${className}`}>
      {/* Filters and Search */}
      <div className="space-y-2">
        {/* Search */}
        <input
          type="text"
          placeholder="Search discoveries..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full px-3 py-2 bg-white border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />

        {/* Filter Controls */}
        <div className="flex flex-wrap gap-2">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as Discovery['status'] | 'all')}
            className="px-2 py-1 bg-white border border-gray-300 rounded-md text-sm"
          >
            <option value="all">All Status</option>
            <option value="pending">Pending</option>
            <option value="investigating">Investigating</option>
            <option value="resolved">Resolved</option>
            <option value="false_positive">False Positive</option>
          </select>

          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value as Discovery['priority'] | 'all')}
            className="px-2 py-1 bg-white border border-gray-300 rounded-md text-sm"
          >
            <option value="all">All Priority</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>

          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-2 py-1 bg-white border border-gray-300 rounded-md text-sm"
          >
            <option value="all">All Types</option>
            <option value="person">Person</option>
            <option value="vehicle">Vehicle</option>
            <option value="structure">Structure</option>
            <option value="signal">Signal</option>
            <option value="animal">Animal</option>
            <option value="debris">Debris</option>
            <option value="other">Other</option>
          </select>
        </div>
      </div>

      {/* Results Count */}
      <div className="text-sm text-gray-500">
        Showing {filteredAndSortedDiscoveries.length} of {discoveries.length} discoveries
      </div>

      {/* Discovery List */}
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {filteredAndSortedDiscoveries.map((discovery) => (
          <div
            key={discovery.id}
            className={`
              ${compactView ? 'p-2' : 'p-3'} rounded-lg border cursor-pointer transition-all
              ${selectedDiscoveryId === discovery.id
                ? 'bg-blue-50 border-blue-500'
                : 'bg-white border-gray-200 hover:bg-gray-50'
              }
            `}
            onClick={() => onDiscoverySelect?.(discovery)}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3 flex-1">
                {/* Type Icon */}
                <span className="text-xl">{getTypeIcon(discovery.discovery_type)}</span>

                <div className="flex-1 min-w-0">
                  {/* Header */}
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium capitalize">{discovery.discovery_type}</span>
                    <span className={`px-2 py-0.5 rounded text-xs ${getPriorityColor(discovery.priority)}`}>
                      {discovery.priority}
                    </span>
                    <span className={`w-2 h-2 rounded-full ${getStatusColor(discovery.status)}`} />
                  </div>

                  {/* Description */}
                  <p className="text-sm text-gray-600 mb-2 line-clamp-2">
                    {discovery.description || 'No description available'}
                  </p>

                  {/* Metadata */}
                  <div className="flex items-center gap-4 text-xs text-gray-500">
                    <span>{formatTimestamp(discovery.created_at)}</span>
                    <span>Confidence: {Math.round(discovery.confidence)}%</span>
                    {showEvidenceCount && discovery.image_url && (
                      <span>Has evidence</span>
                    )}
                  </div>

                  {/* Location */}
                  <div className="text-xs text-gray-500 mt-1">
                    {discovery.location_lat.toFixed(6)}, {discovery.location_lng.toFixed(6)}
                  </div>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="flex flex-col gap-1 ml-2">
                <select
                  value={discovery.status}
                  onChange={(e) => onStatusChange?.(discovery.id, e.target.value as Discovery['status'])}
                  className="text-xs bg-white border border-gray-300 rounded px-1 py-0.5"
                >
                  <option value="pending">Pending</option>
                  <option value="investigating">Investigating</option>
                  <option value="resolved">Resolved</option>
                  <option value="false_positive">False Positive</option>
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