import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { 
  // MapPin, 
  // Radio, 
  Pause, 
  Play, 
  Square, 
  AlertTriangle,
  // Clock,
  Battery,
  Signal,
  Camera,
  Search,
  // Users,
  Activity,
  Eye,
  // MessageSquare
} from 'lucide-react';
import { MapContainer, TileLayer, Polygon, Circle, Marker, Popup } from 'react-leaflet';
import { apiService } from '../services/api';
import { Mission, MissionStatus } from '../types/mission';
import { Discovery } from '../types/discovery';
import { Drone } from '../types/drone';
import 'leaflet/dist/leaflet.css';

const LiveMission: React.FC = () => {
  const { missionId } = useParams<{ missionId: string }>();
  const [selectedDrone, setSelectedDrone] = useState<string | null>(null);
  const [mapCenter, setMapCenter] = useState<[number, number]>([40.7128, -74.0060]);

  // Fetch mission data
  const { data: missionData, isLoading: missionLoading } = useQuery({
    queryKey: ['mission', missionId],
    queryFn: () => apiService.getMission(missionId!),
    enabled: !!missionId,
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  // Fetch drones data
  const { data: dronesData } = useQuery({
    queryKey: ['drones', { mission_id: missionId }],
    queryFn: () => apiService.getDrones({ mission_id: missionId }),
    enabled: !!missionId,
    refetchInterval: 2000, // Refresh every 2 seconds
  });

  // Fetch discoveries
  const { data: discoveriesData } = useQuery({
    queryKey: ['discoveries', missionId],
    queryFn: () => apiService.getDiscoveries(missionId),
    enabled: !!missionId,
    refetchInterval: 3000, // Refresh every 3 seconds
  });

  const mission: Mission | undefined = missionData?.data;
  const drones: Drone[] = dronesData?.data?.items || [];
  const discoveries: Discovery[] = discoveriesData?.data || [];

  // Update map center when mission loads
  useEffect(() => {
    if (mission?.search_area?.center) {
      setMapCenter(mission.search_area.center);
    }
  }, [mission?.search_area?.center]);

  const getStatusColor = (status: MissionStatus) => {
    const colors = {
      [MissionStatus.ACTIVE]: 'text-green-700 bg-green-100',
      [MissionStatus.PAUSED]: 'text-yellow-700 bg-yellow-100',
      [MissionStatus.COMPLETED]: 'text-blue-700 bg-blue-100',
      [MissionStatus.ABORTED]: 'text-red-700 bg-red-100',
      [MissionStatus.FAILED]: 'text-red-700 bg-red-100',
      [MissionStatus.PLANNING]: 'text-purple-700 bg-purple-100',
      [MissionStatus.READY]: 'text-gray-700 bg-gray-100',
    };
    return colors[status] || colors[MissionStatus.PLANNING];
  };

  if (missionLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading mission data...</p>
        </div>
      </div>
    );
  }

  if (!mission) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Mission Not Found</h2>
          <p className="text-gray-600">The requested mission could not be loaded.</p>
        </div>
      </div>
    );
  }

  const activeDrones = drones.filter(d => d.current_mission_id === missionId);
  const progressPercent = mission.progress?.overall_percent || 0;

  return (
    <div className="h-[calc(100vh-120px)] flex flex-col">
      {/* Mission Header */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div>
              <h1 className="text-xl font-bold text-gray-900">{mission.name}</h1>
              <p className="text-sm text-gray-600">{mission.description}</p>
            </div>
            <span className={`status-badge ${getStatusColor(mission.status)}`}>
              {mission.status}
            </span>
          </div>
          
          <div className="flex items-center space-x-3">
            {/* Mission Controls */}
            {mission.status === MissionStatus.ACTIVE && (
              <button className="flex items-center space-x-2 px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg">
                <Pause className="w-4 h-4" />
                <span>Pause</span>
              </button>
            )}
            
            {mission.status === MissionStatus.PAUSED && (
              <button className="flex items-center space-x-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg">
                <Play className="w-4 h-4" />
                <span>Resume</span>
              </button>
            )}
            
            {(mission.status === MissionStatus.ACTIVE || mission.status === MissionStatus.PAUSED) && (
              <button className="flex items-center space-x-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg">
                <Square className="w-4 h-4" />
                <span>Abort</span>
              </button>
            )}
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mt-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Mission Progress</span>
            <span className="text-sm text-gray-600">{progressPercent.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-primary-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            ></div>
          </div>
        </div>
      </div>

      <div className="flex-1 flex">
        {/* Map View */}
        <div className="flex-1 relative">
          <MapContainer
            center={mapCenter}
            zoom={13}
            style={{ height: '100%', width: '100%' }}
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
            
            {/* Search Area */}
            {mission.search_area && (
              <>
                {mission.search_area.type === 'polygon' && (
                  <Polygon
                    positions={mission.search_area.coordinates[0].map((coord: any) => [coord[1], coord[0]])}
                    pathOptions={{
                      color: '#3b82f6',
                      fillColor: '#3b82f6',
                      fillOpacity: 0.1,
                      weight: 2
                    }}
                  />
                )}
                {mission.search_area.type === 'circle' && mission.search_area.center && (
                  <Circle
                    center={mission.search_area.center}
                    radius={mission.search_area.radius || 1000}
                    pathOptions={{
                      color: '#3b82f6',
                      fillColor: '#3b82f6',
                      fillOpacity: 0.1,
                      weight: 2
                    }}
                  />
                )}
              </>
            )}

            {/* Drone Positions */}
            {activeDrones.map((drone) => (
              drone.location && (
                <Marker
                  key={drone.id}
                  position={[drone.location.latitude, drone.location.longitude]}
                  eventHandlers={{
                    click: () => setSelectedDrone(drone.id)
                  }}
                >
                  <Popup>
                    <div className="p-2">
                      <h4 className="font-semibold">{drone.name}</h4>
                      <p className="text-sm text-gray-600">{drone.status}</p>
                      <p className="text-sm">Battery: {drone.battery_level}%</p>
                      <p className="text-sm">Altitude: {drone.location.altitude_m}m</p>
                    </div>
                  </Popup>
                </Marker>
              )
            ))}

            {/* Discoveries */}
            {discoveries.map((discovery) => (
              <Marker
                key={discovery.id}
                position={discovery.coordinates}
              >
                <Popup>
                  <div className="p-2">
                    <h4 className="font-semibold capitalize">{discovery.type}</h4>
                    <p className="text-sm text-gray-600">{discovery.description}</p>
                    <p className="text-sm">Confidence: {(discovery.confidence * 100).toFixed(1)}%</p>
                    <p className="text-sm">Priority: <span className="capitalize">{discovery.priority}</span></p>
                  </div>
                </Popup>
              </Marker>
            ))}
          </MapContainer>

          {/* Map Legend */}
          <div className="absolute top-4 left-4 bg-white p-3 rounded-lg shadow-lg border border-gray-200">
            <h4 className="font-semibold text-gray-900 mb-2">Legend</h4>
            <div className="space-y-1 text-sm">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                <span>Search Area</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <span>Active Drones</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                <span>Discoveries</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Sidebar */}
        <div className="w-80 bg-white border-l border-gray-200 flex flex-col">
          {/* Mission Stats */}
          <div className="p-4 border-b border-gray-200">
            <h3 className="font-semibold text-gray-900 mb-3">Mission Statistics</h3>
            <div className="grid grid-cols-2 gap-3">
              <div className="text-center">
                <div className="text-lg font-bold text-gray-900">{activeDrones.length}</div>
                <div className="text-xs text-gray-600">Active Drones</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-bold text-gray-900">{discoveries.length}</div>
                <div className="text-xs text-gray-600">Discoveries</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-bold text-gray-900">
                  {mission.progress?.area_covered_km2?.toFixed(1) || '0.0'}
                </div>
                <div className="text-xs text-gray-600">km² Covered</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-bold text-gray-900">
                  {mission.progress?.flight_time_total_minutes || 0}
                </div>
                <div className="text-xs text-gray-600">Flight Minutes</div>
              </div>
            </div>
          </div>

          {/* Active Drones */}
          <div className="p-4 border-b border-gray-200">
            <h3 className="font-semibold text-gray-900 mb-3">Active Drones</h3>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {activeDrones.map((drone) => (
                <div
                  key={drone.id}
                  className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                    selectedDrone === drone.id
                      ? 'border-primary-300 bg-primary-50'
                      : 'border-gray-200 hover:bg-gray-50'
                  }`}
                  onClick={() => setSelectedDrone(drone.id)}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-sm">{drone.name}</span>
                    <div className="flex items-center space-x-1">
                      <Battery className="w-3 h-3 text-gray-400" />
                      <span className="text-xs text-gray-600">{drone.battery_level}%</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-xs text-gray-600">
                    <span className="flex items-center">
                      <Signal className="w-3 h-3 mr-1" />
                      {drone.connection_status}
                    </span>
                    <span className="flex items-center">
                      <Activity className="w-3 h-3 mr-1" />
                      {drone.status}
                    </span>
                  </div>
                  {drone.location && (
                    <div className="text-xs text-gray-500 mt-1">
                      Alt: {drone.location.altitude_m}m | Speed: {drone.location.speed_kmh} km/h
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Recent Discoveries */}
          <div className="flex-1 p-4 overflow-y-auto">
            <h3 className="font-semibold text-gray-900 mb-3">Recent Discoveries</h3>
            <div className="space-y-3">
              {discoveries.slice(0, 10).map((discovery) => (
                <div key={discovery.id} className="p-3 border border-gray-200 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-sm capitalize">{discovery.type}</span>
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      discovery.priority === 'critical' ? 'bg-red-100 text-red-800' :
                      discovery.priority === 'high' ? 'bg-orange-100 text-orange-800' :
                      discovery.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {discovery.priority}
                    </span>
                  </div>
                  <p className="text-xs text-gray-600 mb-2">{discovery.description}</p>
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>Confidence: {(discovery.confidence * 100).toFixed(1)}%</span>
                    <span>{new Date(discovery.timestamp).toLocaleTimeString()}</span>
                  </div>
                  <div className="flex items-center space-x-2 mt-2">
                    {discovery.image_url && (
                      <button className="flex items-center space-x-1 text-xs text-primary-600 hover:text-primary-700">
                        <Camera className="w-3 h-3" />
                        <span>View Image</span>
                      </button>
                    )}
                    <button className="flex items-center space-x-1 text-xs text-gray-600 hover:text-gray-700">
                      <Eye className="w-3 h-3" />
                      <span>Details</span>
                    </button>
                  </div>
                </div>
              ))}
              
              {discoveries.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  <Search className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                  <p className="text-sm">No discoveries yet</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LiveMission;