import React, { useState, useMemo, useCallback } from 'react';
import {
  MagnifyingGlassIcon,
  FunnelIcon,
  ArrowsUpDownIcon,
  Squares2X2Icon,
  ListBulletIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { Drone, DroneStatus as DroneStatusEnum } from '../../types';
import DroneStatus from './DroneStatus';
import { useDrones } from '../../hooks/useDrones';

interface DroneGridProps {
  drones?: Drone[];
  onDroneSelect?: (drone: Drone) => void;
  onDroneCommand?: (droneId: string, command: any) => void;
  selectable?: boolean;
  selectedDroneIds?: string[];
  className?: string;
}

type SortField = 'name' | 'status' | 'battery' | 'signal' | 'lastSeen';
type SortOrder = 'asc' | 'desc';
type ViewMode = 'grid' | 'list';

const DroneGrid: React.FC<DroneGridProps> = ({
  drones: propDrones,
  onDroneSelect,
  onDroneCommand,
  selectable = false,
  selectedDroneIds = [],
  className = ''
}) => {
  const { drones: hookDrones, loading, error, discoverDrones, emergencyStop } = useDrones();
  const drones = propDrones || hookDrones;

  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<DroneStatusEnum | 'all'>('all');
  const [sortField, setSortField] = useState<SortField>('name');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [showFilters, setShowFilters] = useState(false);

  // Filter and sort drones
  const filteredAndSortedDrones = useMemo(() => {
    let filtered = drones.filter(drone => {
      // Search filter
      const matchesSearch = drone.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           drone.type.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           drone.id.toLowerCase().includes(searchTerm.toLowerCase());

      // Status filter
      const matchesStatus = statusFilter === 'all' || drone.status === statusFilter;

      return matchesSearch && matchesStatus;
    });

    // Sort
    filtered.sort((a, b) => {
      let aValue: any, bValue: any;

      switch (sortField) {
        case 'name':
          aValue = a.name.toLowerCase();
          bValue = b.name.toLowerCase();
          break;
        case 'status':
          aValue = a.status;
          bValue = b.status;
          break;
        case 'battery':
          aValue = a.battery;
          bValue = b.battery;
          break;
        case 'signal':
          aValue = a.signalStrength;
          bValue = b.signalStrength;
          break;
        case 'lastSeen':
          aValue = a.lastSeen.getTime();
          bValue = b.lastSeen.getTime();
          break;
        default:
          return 0;
      }

      if (aValue < bValue) return sortOrder === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });

    return filtered;
  }, [drones, searchTerm, statusFilter, sortField, sortOrder]);

  // Get status counts
  const statusCounts = useMemo(() => {
    const counts = {
      all: drones.length,
      [DroneStatusEnum.IDLE]: 0,
      [DroneStatusEnum.ACTIVE]: 0,
      [DroneStatusEnum.RETURNING]: 0,
      [DroneStatusEnum.CHARGING]: 0,
      [DroneStatusEnum.MAINTENANCE]: 0,
      [DroneStatusEnum.OFFLINE]: 0,
      [DroneStatusEnum.EMERGENCY]: 0
    };

    drones.forEach(drone => {
      counts[drone.status]++;
    });

    return counts;
  }, [drones]);

  // Handle sort
  const handleSort = useCallback((field: SortField) => {
    if (field === sortField) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
  }, [sortField, sortOrder]);

  // Handle drone selection
  const handleDroneClick = useCallback((drone: Drone) => {
    if (onDroneSelect) {
      onDroneSelect(drone);
    }
  }, [onDroneSelect]);

  // Handle emergency stop all
  const handleEmergencyStopAll = useCallback(async () => {
    if (window.confirm('Are you sure you want to emergency stop all active drones?')) {
      const activeDrones = drones.filter(d => d.status === DroneStatusEnum.ACTIVE);
      
      for (const drone of activeDrones) {
        try {
          await emergencyStop(drone.id);
        } catch (error) {
          console.error(`Failed to emergency stop drone ${drone.id}:`, error);
        }
      }
    }
  }, [drones, emergencyStop]);

  // Render status filter buttons
  const renderStatusFilters = () => (
    <div className="flex flex-wrap gap-2">
      <button
        onClick={() => setStatusFilter('all')}
        className={`px-3 py-1 rounded-full text-sm font-medium border ${
          statusFilter === 'all' 
            ? 'bg-blue-500 text-white border-blue-500' 
            : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
        }`}
      >
        All ({statusCounts.all})
      </button>

      {Object.entries(statusCounts).map(([status, count]) => {
        if (status === 'all' || count === 0) return null;

        const statusEnum = status as DroneStatusEnum;
        const isActive = statusFilter === statusEnum;

        return (
          <button
            key={status}
            onClick={() => setStatusFilter(statusEnum)}
            className={`px-3 py-1 rounded-full text-sm font-medium border ${
              isActive
                ? getStatusButtonStyle(statusEnum, true)
                : getStatusButtonStyle(statusEnum, false)
            }`}
          >
            {status} ({count})
          </button>
        );
      })}
    </div>
  );

  // Get status button styling
  const getStatusButtonStyle = (status: DroneStatusEnum, active: boolean) => {
    const baseClasses = active ? 'text-white' : 'text-gray-700 hover:bg-gray-50';
    const borderClasses = active ? '' : 'border-gray-300';

    switch (status) {
      case DroneStatusEnum.ACTIVE:
        return `${baseClasses} ${active ? 'bg-green-500 border-green-500' : borderClasses}`;
      case DroneStatusEnum.IDLE:
        return `${baseClasses} ${active ? 'bg-blue-500 border-blue-500' : borderClasses}`;
      case DroneStatusEnum.RETURNING:
        return `${baseClasses} ${active ? 'bg-yellow-500 border-yellow-500' : borderClasses}`;
      case DroneStatusEnum.CHARGING:
        return `${baseClasses} ${active ? 'bg-purple-500 border-purple-500' : borderClasses}`;
      case DroneStatusEnum.MAINTENANCE:
        return `${baseClasses} ${active ? 'bg-orange-500 border-orange-500' : borderClasses}`;
      case DroneStatusEnum.OFFLINE:
        return `${baseClasses} ${active ? 'bg-gray-500 border-gray-500' : borderClasses}`;
      case DroneStatusEnum.EMERGENCY:
        return `${baseClasses} ${active ? 'bg-red-500 border-red-500' : borderClasses}`;
      default:
        return `${baseClasses} ${active ? 'bg-gray-500 border-gray-500' : borderClasses}`;
    }
  };

  // Render sort buttons
  const renderSortControls = () => (
    <div className="flex items-center space-x-2">
      <span className="text-sm text-gray-600">Sort by:</span>
      
      {(['name', 'status', 'battery', 'signal', 'lastSeen'] as SortField[]).map(field => (
        <button
          key={field}
          onClick={() => handleSort(field)}
          className={`px-2 py-1 text-sm rounded ${
            sortField === field 
              ? 'bg-blue-100 text-blue-700' 
              : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          {field}
          {sortField === field && (
            <ArrowsUpDownIcon className={`w-3 h-3 inline ml-1 ${
              sortOrder === 'desc' ? 'transform rotate-180' : ''
            }`} />
          )}
        </button>
      ))}
    </div>
  );

  // Render grid view
  const renderGridView = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {filteredAndSortedDrones.map(drone => (
        <div key={drone.id} className="relative">
          <DroneStatus
            drone={drone}
            onStatusClick={handleDroneClick}
            onCommandSend={onDroneCommand}
          />
          
          {selectable && (
            <div className="absolute top-2 left-2">
              <input
                type="checkbox"
                checked={selectedDroneIds.includes(drone.id)}
                onChange={() => handleDroneClick(drone)}
                className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
              />
            </div>
          )}
        </div>
      ))}
    </div>
  );

  // Render list view
  const renderListView = () => (
    <div className="space-y-2">
      {filteredAndSortedDrones.map(drone => (
        <div
          key={drone.id}
          className={`flex items-center space-x-4 p-4 bg-white rounded-lg border hover:shadow-sm cursor-pointer ${
            selectedDroneIds.includes(drone.id) ? 'ring-2 ring-blue-500' : ''
          }`}
          onClick={() => handleDroneClick(drone)}
        >
          {selectable && (
            <input
              type="checkbox"
              checked={selectedDroneIds.includes(drone.id)}
              onChange={() => handleDroneClick(drone)}
              className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
            />
          )}
          
          <div className={`w-3 h-3 rounded-full ${
            drone.isConnected ? 'bg-green-500' : 'bg-red-500'
          }`} />
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2">
              <h3 className="font-medium text-gray-900 truncate">{drone.name}</h3>
              <span className="text-sm text-gray-500">({drone.type})</span>
            </div>
            <p className="text-sm text-gray-500 truncate">{drone.id}</p>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="text-center">
              <div className="text-sm font-medium text-gray-900">{drone.battery}%</div>
              <div className="text-xs text-gray-500">Battery</div>
            </div>
            
            <div className="text-center">
              <div className="text-sm font-medium text-gray-900">{drone.signalStrength}%</div>
              <div className="text-xs text-gray-500">Signal</div>
            </div>
            
            <div className="text-center">
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                drone.status === DroneStatusEnum.ACTIVE ? 'bg-green-100 text-green-800' :
                drone.status === DroneStatusEnum.IDLE ? 'bg-blue-100 text-blue-800' :
                drone.status === DroneStatusEnum.EMERGENCY ? 'bg-red-100 text-red-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {drone.status}
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );

  if (loading && drones.length === 0) {
    return (
      <div className={`flex items-center justify-center h-64 ${className}`}>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900">
            Drone Fleet ({filteredAndSortedDrones.length}/{drones.length})
          </h2>
          <p className="text-sm text-gray-600">
            {statusCounts[DroneStatusEnum.ACTIVE]} active • {statusCounts[DroneStatusEnum.EMERGENCY]} emergency
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={discoverDrones}
            disabled={loading}
            className="px-3 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
          >
            Discover Drones
          </button>
          
          {statusCounts[DroneStatusEnum.EMERGENCY] > 0 && (
            <button
              onClick={handleEmergencyStopAll}
              className="px-3 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600"
            >
              <ExclamationTriangleIcon className="w-4 h-4 inline mr-1" />
              Emergency Stop All
            </button>
          )}
        </div>
      </div>

      {/* Controls */}
      <div className="bg-white rounded-lg border p-4 space-y-4">
        {/* Search and view controls */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="relative">
              <MagnifyingGlassIcon className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search drones..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-9 pr-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`p-2 border rounded-lg ${
                showFilters ? 'bg-blue-50 border-blue-300 text-blue-600' : 'border-gray-300 text-gray-600 hover:bg-gray-50'
              }`}
            >
              <FunnelIcon className="w-4 h-4" />
            </button>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 border rounded-lg ${
                viewMode === 'grid' ? 'bg-blue-50 border-blue-300 text-blue-600' : 'border-gray-300 text-gray-600 hover:bg-gray-50'
              }`}
            >
              <Squares2X2Icon className="w-4 h-4" />
            </button>
            
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 border rounded-lg ${
                viewMode === 'list' ? 'bg-blue-50 border-blue-300 text-blue-600' : 'border-gray-300 text-gray-600 hover:bg-gray-50'
              }`}
            >
              <ListBulletIcon className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Filters */}
        {showFilters && (
          <div className="space-y-4 border-t pt-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Filter by Status
              </label>
              {renderStatusFilters()}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Sort Options
              </label>
              {renderSortControls()}
            </div>
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <ExclamationTriangleIcon className="w-5 h-5 text-red-500" />
            <span className="text-red-700">{error}</span>
          </div>
        </div>
      )}

      {/* Drone list/grid */}
      {filteredAndSortedDrones.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-gray-400 mb-4">
            <Squares2X2Icon className="w-12 h-12 mx-auto" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No drones found</h3>
          <p className="text-gray-600">
            {searchTerm || statusFilter !== 'all' 
              ? 'Try adjusting your search or filters' 
              : 'Click "Discover Drones" to find available drones'}
          </p>
        </div>
      ) : (
        viewMode === 'grid' ? renderGridView() : renderListView()
      )}

      {/* Summary */}
      {filteredAndSortedDrones.length > 0 && (
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <span>
              Showing {filteredAndSortedDrones.length} of {drones.length} drones
            </span>
            
            {selectedDroneIds.length > 0 && (
              <span>
                {selectedDroneIds.length} selected
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default DroneGrid;