import React, { useState, useEffect, useMemo } from 'react';
import { 
  Search, 
  Filter, 
  Grid3X3, 
  List, 
  RefreshCw,
  Plus,
  AlertTriangle,
  Battery,
  Signal
} from 'lucide-react';
import { Drone } from '../../types/drone';
import { DroneStatus } from './DroneStatus';
import { apiService } from '../../services/api';
import { webSocketService } from '../../services/websocket';

interface DroneGridProps {
  drones?: Drone[];
  onDroneSelect?: (drone: Drone) => void;
  onDiscoverDrones?: () => void;
  showControls?: boolean;
  className?: string;
}

type ViewMode = 'grid' | 'list';
type FilterStatus = 'all' | 'active' | 'idle' | 'charging' | 'error' | 'offline';
type SortBy = 'name' | 'status' | 'battery' | 'signal' | 'last_seen';

export const DroneGrid: React.FC<DroneGridProps> = ({
  drones: initialDrones = [],
  onDroneSelect,
  onDiscoverDrones,
  showControls = true,
  className = '',
}) => {
  const [drones, setDrones] = useState<Drone[]>(initialDrones);
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState<FilterStatus>('all');
  const [sortBy, setSortBy] = useState<SortBy>('name');
  const [isLoading, setIsLoading] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  // Update drones when props change
  useEffect(() => {
    setDrones(initialDrones);
  }, [initialDrones]);

  // Subscribe to real-time drone updates
  useEffect(() => {
    const handleDroneTelemetry = (data: any) => {
      setDrones(prevDrones => 
        prevDrones.map(drone => 
          drone.id === data.drone_id 
            ? { 
                ...drone, 
                position: data.position,
                battery_level: data.battery_level,
                status: data.status,
                signal_strength: data.signal_strength,
                telemetry: data,
                last_seen: data.timestamp
              }
            : drone
        )
      );
      setLastRefresh(new Date());
    };

    webSocketService.subscribe('drone_telemetry', handleDroneTelemetry);

    // Subscribe to all drones
    drones.forEach(drone => {
      webSocketService.subscribeDrone(drone.id);
    });

    return () => {
      webSocketService.unsubscribe('drone_telemetry', handleDroneTelemetry);
      drones.forEach(drone => {
        webSocketService.unsubscribeDrone(drone.id);
      });
    };
  }, [drones]);

  // Filter and sort drones
  const filteredAndSortedDrones = useMemo(() => {
    let filtered = drones;

    // Apply search filter
    if (searchQuery) {
      filtered = filtered.filter(drone =>
        drone.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        drone.model.toLowerCase().includes(searchQuery.toLowerCase()) ||
        drone.id.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Apply status filter
    if (filterStatus !== 'all') {
      filtered = filtered.filter(drone => drone.status === filterStatus);
    }

    // Apply sorting
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.name.localeCompare(b.name);
        case 'status':
          return a.status.localeCompare(b.status);
        case 'battery':
          return b.battery_level - a.battery_level;
        case 'signal':
          return b.signal_strength - a.signal_strength;
        case 'last_seen':
          return new Date(b.last_seen).getTime() - new Date(a.last_seen).getTime();
        default:
          return 0;
      }
    });

    return filtered;
  }, [drones, searchQuery, filterStatus, sortBy]);

  // Calculate fleet statistics
  const fleetStats = useMemo(() => {
    const total = drones.length;
    const active = drones.filter(d => d.status === 'active').length;
    const idle = drones.filter(d => d.status === 'idle').length;
    const charging = drones.filter(d => d.status === 'charging').length;
    const offline = drones.filter(d => d.status === 'offline').length;
    const errors = drones.filter(d => d.status === 'error').length;
    
    const avgBattery = total > 0 
      ? drones.reduce((sum, d) => sum + d.battery_level, 0) / total 
      : 0;
    
    const avgSignal = total > 0 
      ? drones.reduce((sum, d) => sum + d.signal_strength, 0) / total 
      : 0;

    return {
      total,
      active,
      idle,
      charging,
      offline,
      errors,
      avgBattery,
      avgSignal,
    };
  }, [drones]);

  const handleRefresh = async () => {
    setIsLoading(true);
    try {
      const response = await apiService.getDrones();
      setDrones(response.drones);
      setLastRefresh(new Date());
    } catch (error) {
      console.error('Failed to refresh drones:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDiscoverDrones = async () => {
    if (!onDiscoverDrones) return;
    
    setIsLoading(true);
    try {
      onDiscoverDrones();
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusCount = (status: FilterStatus) => {
    if (status === 'all') return fleetStats.total;
    return drones.filter(d => d.status === status).length;
  };

  return (
    <div className={`bg-white rounded-lg shadow-lg ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Drone Fleet</h2>
            <p className="text-gray-600">
              {fleetStats.total} drones • Last updated {lastRefresh.toLocaleTimeString()}
            </p>
          </div>

          {showControls && (
            <div className="flex items-center space-x-2">
              <button
                onClick={handleRefresh}
                disabled={isLoading}
                className="btn btn-secondary text-sm"
              >
                <RefreshCw size={16} className={`mr-1 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
              
              {onDiscoverDrones && (
                <button
                  onClick={handleDiscoverDrones}
                  disabled={isLoading}
                  className="btn btn-primary text-sm"
                >
                  <Plus size={16} className="mr-1" />
                  Discover
                </button>
              )}
            </div>
          )}
        </div>

        {/* Fleet Statistics */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{fleetStats.active}</div>
            <div className="text-sm text-gray-600">Active</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{fleetStats.idle}</div>
            <div className="text-sm text-gray-600">Idle</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-600">{fleetStats.charging}</div>
            <div className="text-sm text-gray-600">Charging</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">{fleetStats.errors}</div>
            <div className="text-sm text-gray-600">Errors</div>
          </div>
          
          <div className="text-center">
            <div className="flex items-center justify-center space-x-1">
              <Battery size={16} className="text-gray-400" />
              <span className="text-2xl font-bold text-gray-900">{fleetStats.avgBattery.toFixed(0)}%</span>
            </div>
            <div className="text-sm text-gray-600">Avg Battery</div>
          </div>
          
          <div className="text-center">
            <div className="flex items-center justify-center space-x-1">
              <Signal size={16} className="text-gray-400" />
              <span className="text-2xl font-bold text-gray-900">{fleetStats.avgSignal.toFixed(0)}%</span>
            </div>
            <div className="text-sm text-gray-600">Avg Signal</div>
          </div>
        </div>

        {/* Controls */}
        {showControls && (
          <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
            {/* Search */}
            <div className="relative">
              <Search size={20} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search drones..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div className="flex items-center space-x-4">
              {/* Status Filter */}
              <div className="flex items-center space-x-2">
                <Filter size={16} className="text-gray-400" />
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value as FilterStatus)}
                  className="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">All ({getStatusCount('all')})</option>
                  <option value="active">Active ({getStatusCount('active')})</option>
                  <option value="idle">Idle ({getStatusCount('idle')})</option>
                  <option value="charging">Charging ({getStatusCount('charging')})</option>
                  <option value="error">Error ({getStatusCount('error')})</option>
                  <option value="offline">Offline ({getStatusCount('offline')})</option>
                </select>
              </div>

              {/* Sort */}
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as SortBy)}
                className="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="name">Sort by Name</option>
                <option value="status">Sort by Status</option>
                <option value="battery">Sort by Battery</option>
                <option value="signal">Sort by Signal</option>
                <option value="last_seen">Sort by Last Seen</option>
              </select>

              {/* View Mode */}
              <div className="flex border border-gray-300 rounded-md overflow-hidden">
                <button
                  onClick={() => setViewMode('grid')}
                  className={`p-2 ${viewMode === 'grid' ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'}`}
                >
                  <Grid3X3 size={16} />
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`p-2 ${viewMode === 'list' ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'}`}
                >
                  <List size={16} />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Drone Grid/List */}
      <div className="p-6">
        {filteredAndSortedDrones.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-400 mb-4">
              {searchQuery || filterStatus !== 'all' ? (
                <div>
                  <Search size={48} className="mx-auto mb-2" />
                  <p>No drones match your search criteria</p>
                </div>
              ) : (
                <div>
                  <AlertTriangle size={48} className="mx-auto mb-2" />
                  <p>No drones available</p>
                </div>
              )}
            </div>
            {onDiscoverDrones && (
              <button
                onClick={handleDiscoverDrones}
                disabled={isLoading}
                className="btn btn-primary"
              >
                <Plus size={20} className="mr-2" />
                Discover Drones
              </button>
            )}
          </div>
        ) : (
          <div className={
            viewMode === 'grid' 
              ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6'
              : 'space-y-4'
          }>
            {filteredAndSortedDrones.map(drone => (
              <DroneStatus
                key={drone.id}
                drone={drone}
                showDetails={viewMode === 'list'}
                onStatusClick={onDroneSelect}
                className={viewMode === 'list' ? 'w-full' : ''}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};