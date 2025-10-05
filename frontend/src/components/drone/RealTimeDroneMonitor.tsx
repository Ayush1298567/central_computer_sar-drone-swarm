import React, { useState, useEffect, useCallback } from 'react';
import { droneConnectionService, DroneInfo, DroneConnection } from '../../services/droneConnections';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { 
  Play, 
  Pause, 
  Square, 
  AlertTriangle, 
  Wifi, 
  Battery, 
  MapPin, 
  Signal,
  RefreshCw,
  Power,
  Zap,
  Home,
  Navigation
} from 'lucide-react';
import { toast } from 'react-hot-toast';

interface RealTimeDroneMonitorProps {
  className?: string;
  onDroneSelect?: (drone: DroneInfo) => void;
  selectedDroneId?: string;
}

const RealTimeDroneMonitor: React.FC<RealTimeDroneMonitorProps> = ({
  className = '',
  onDroneSelect,
  selectedDroneId
}) => {
  const [drones, setDrones] = useState<DroneInfo[]>([]);
  const [connections, setConnections] = useState<Record<string, DroneConnection>>({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [discoveryActive, setDiscoveryActive] = useState(false);

  // Load drones and connections
  const loadData = useCallback(async () => {
    try {
      setRefreshing(true);
      
      // Load drones and connections in parallel
      const [dronesData, connectionsData] = await Promise.all([
        droneConnectionService.getAllDrones(),
        droneConnectionService.getConnections()
      ]);

      setDrones(dronesData.drones.all);
      setConnections(connectionsData.connections);
      setDiscoveryActive(dronesData.statistics.discovery_active);
      
    } catch (error) {
      console.error('Error loading drone data:', error);
      toast.error('Failed to load drone data');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    loadData();
  }, [loadData]);

  // Auto-refresh every 5 seconds
  useEffect(() => {
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, [loadData]);

  // Handle drone commands
  const handleCommand = async (droneId: string, command: string, params: any = {}) => {
    try {
      let success = false;
      
      switch (command) {
        case 'takeoff':
          success = await droneConnectionService.takeoff(droneId, params.altitude);
          break;
        case 'land':
          success = await droneConnectionService.land(droneId, params.location);
          break;
        case 'return_home':
          success = await droneConnectionService.returnHome(droneId);
          break;
        case 'emergency_stop':
          success = await droneConnectionService.emergencyStop(droneId);
          break;
        case 'pause_mission':
          success = await droneConnectionService.pauseMission(droneId);
          break;
        case 'resume_mission':
          success = await droneConnectionService.resumeMission(droneId);
          break;
        default:
          success = await droneConnectionService.sendCommand(droneId, {
            command_type: command,
            parameters: params,
            priority: 2
          });
      }

      if (success) {
        toast.success(`Command ${command} sent to ${droneId}`);
      } else {
        toast.error(`Failed to send ${command} to ${droneId}`);
      }
    } catch (error) {
      console.error(`Error sending command ${command}:`, error);
      toast.error(`Error sending ${command} command`);
    }
  };

  // Get status color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected':
      case 'flying':
        return 'bg-green-500';
      case 'connecting':
      case 'idle':
        return 'bg-yellow-500';
      case 'disconnected':
      case 'offline':
        return 'bg-red-500';
      case 'emergency':
        return 'bg-red-600';
      case 'charging':
      case 'maintenance':
        return 'bg-blue-500';
      default:
        return 'bg-gray-500';
    }
  };

  // Get battery color
  const getBatteryColor = (battery: number) => {
    if (battery > 50) return 'text-green-500';
    if (battery > 20) return 'text-yellow-500';
    return 'text-red-500';
  };

  // Get signal strength color
  const getSignalColor = (strength: number) => {
    if (strength > 70) return 'text-green-500';
    if (strength > 40) return 'text-yellow-500';
    return 'text-red-500';
  };

  // Toggle discovery
  const toggleDiscovery = async () => {
    try {
      if (discoveryActive) {
        await droneConnectionService.stopDiscovery();
        setDiscoveryActive(false);
        toast.success('Discovery stopped');
      } else {
        await droneConnectionService.startDiscovery();
        setDiscoveryActive(true);
        toast.success('Discovery started');
      }
    } catch (error) {
      console.error('Error toggling discovery:', error);
      toast.error('Failed to toggle discovery');
    }
  };

  if (loading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Wifi className="h-5 w-5" />
            Real-Time Drone Monitor
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="h-6 w-6 animate-spin" />
            <span className="ml-2">Loading drones...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Wifi className="h-5 w-5" />
            Real-Time Drone Monitor
          </CardTitle>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={loadData}
              disabled={refreshing}
            >
              <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
            </Button>
            <Button
              variant={discoveryActive ? "default" : "outline"}
              size="sm"
              onClick={toggleDiscovery}
            >
              <Power className="h-4 w-4" />
              {discoveryActive ? 'Stop Discovery' : 'Start Discovery'}
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {drones.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Wifi className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No drones found</p>
            <p className="text-sm">Start discovery to find available drones</p>
          </div>
        ) : (
          <div className="space-y-4">
            {drones.map((drone) => {
              const connection = connections[`${drone.drone_id}_${drone.connection_type}`];
              const isSelected = selectedDroneId === drone.drone_id;
              
              return (
                <Card 
                  key={drone.drone_id}
                  className={`cursor-pointer transition-all ${
                    isSelected ? 'ring-2 ring-blue-500 bg-blue-50' : 'hover:shadow-md'
                  }`}
                  onClick={() => onDroneSelect?.(drone)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className={`w-3 h-3 rounded-full ${getStatusColor(drone.status)}`} />
                        <div>
                          <h3 className="font-semibold">{drone.name}</h3>
                          <p className="text-sm text-gray-500">{drone.model}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">{drone.connection_type}</Badge>
                        <Badge variant="secondary">{drone.status}</Badge>
                      </div>
                    </div>

                    {/* Status indicators */}
                    <div className="grid grid-cols-4 gap-4 mb-3">
                      <div className="text-center">
                        <Battery className={`h-4 w-4 mx-auto mb-1 ${getBatteryColor(drone.battery_level)}`} />
                        <p className="text-xs text-gray-500">Battery</p>
                        <p className={`text-sm font-medium ${getBatteryColor(drone.battery_level)}`}>
                          {drone.battery_level}%
                        </p>
                      </div>
                      <div className="text-center">
                        <Signal className={`h-4 w-4 mx-auto mb-1 ${getSignalColor(drone.signal_strength)}`} />
                        <p className="text-xs text-gray-500">Signal</p>
                        <p className={`text-sm font-medium ${getSignalColor(drone.signal_strength)}`}>
                          {drone.signal_strength}%
                        </p>
                      </div>
                      <div className="text-center">
                        <MapPin className="h-4 w-4 mx-auto mb-1 text-blue-500" />
                        <p className="text-xs text-gray-500">Altitude</p>
                        <p className="text-sm font-medium">{drone.position.alt.toFixed(1)}m</p>
                      </div>
                      <div className="text-center">
                        <Navigation className="h-4 w-4 mx-auto mb-1 text-green-500" />
                        <p className="text-xs text-gray-500">Speed</p>
                        <p className="text-sm font-medium">{drone.speed.toFixed(1)}m/s</p>
                      </div>
                    </div>

                    {/* Connection metrics */}
                    {connection?.metrics && (
                      <div className="mb-3">
                        <div className="flex justify-between text-xs text-gray-500 mb-1">
                          <span>Connection Stability</span>
                          <span>{Math.round(connection.metrics.connection_stability * 100)}%</span>
                        </div>
                        <Progress 
                          value={connection.metrics.connection_stability * 100} 
                          className="h-1"
                        />
                      </div>
                    )}

                    {/* Control buttons */}
                    <div className="flex items-center gap-2">
                      {drone.status === 'connected' || drone.status === 'idle' ? (
                        <>
                          <Button
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleCommand(drone.drone_id, 'takeoff', { altitude: 50 });
                            }}
                          >
                            <Play className="h-3 w-3 mr-1" />
                            Takeoff
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleCommand(drone.drone_id, 'land');
                            }}
                          >
                            <Square className="h-3 w-3 mr-1" />
                            Land
                          </Button>
                        </>
                      ) : drone.status === 'flying' ? (
                        <>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleCommand(drone.drone_id, 'pause_mission');
                            }}
                          >
                            <Pause className="h-3 w-3 mr-1" />
                            Pause
                          </Button>
                          <Button
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleCommand(drone.drone_id, 'return_home');
                            }}
                          >
                            <Home className="h-3 w-3 mr-1" />
                            RTH
                          </Button>
                        </>
                      ) : drone.status === 'emergency' ? (
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleCommand(drone.drone_id, 'emergency_stop');
                          }}
                        >
                          <AlertTriangle className="h-3 w-3 mr-1" />
                          Emergency Stop
                        </Button>
                      ) : null}

                      {/* Emergency button (always available) */}
                      {drone.status !== 'disconnected' && drone.status !== 'offline' && (
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleCommand(drone.drone_id, 'emergency_stop');
                          }}
                        >
                          <Zap className="h-3 w-3" />
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default RealTimeDroneMonitor;
