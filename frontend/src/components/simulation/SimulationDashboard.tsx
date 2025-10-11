import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Alert, AlertDescription } from '../ui/alert';
import {
  Activity,
  MapPin,
  Eye,
  Clock,
  AlertTriangle,
  CheckCircle,
  Zap,
  Wind,
  Thermometer,
  Signal,
  Target
} from 'lucide-react';

interface TelemetryData {
  timestamp: string;
  position: {
    latitude: number;
    longitude: number;
    altitude: number;
    heading: number;
    ground_speed: number;
  };
  battery: {
    level: number;
    voltage: number;
    temperature: number;
    time_remaining: number;
  };
  attitude: {
    roll: number;
    pitch: number;
    yaw: number;
  };
  velocity: {
    vx: number;
    vy: number;
    vz: number;
  };
  signal_strength: number;
  flight_mode: string;
  status: string;
  armed: boolean;
  mission_progress: number;
  wind_speed: number;
  wind_direction: number;
}

interface DetectionEvent {
  event_id: string;
  timestamp: string;
  drone_id: string;
  object_type: string;
  confidence_score: number;
  position: [number, number, number];
  detection_method: string;
  environmental_conditions: any;
  sensor_data: any;
}

interface SimulationStats {
  total_drones: number;
  active_drones: number;
  total_detections: number;
  recent_detections: number;
  average_confidence: number;
  uptime: number;
  total_flight_time: number;
  discoveries: number;
}

interface SimulationDashboardProps {
  drones: Record<string, TelemetryData>;
  detections: DetectionEvent[];
  stats: SimulationStats;
  isConnected: boolean;
  isRunning: boolean;
}

const SimulationDashboard: React.FC<SimulationDashboardProps> = ({
  drones,
  detections,
  stats,
  isConnected,
  isRunning
}) => {
  const [selectedDrone, setSelectedDrone] = useState<string | null>(null);
  const [recentDetections, setRecentDetections] = useState<DetectionEvent[]>([]);

  useEffect(() => {
    // Update recent detections
    const recent = detections
      .filter(d => {
        const detectionTime = new Date(d.timestamp).getTime();
        const fiveMinutesAgo = Date.now() - 5 * 60 * 1000;
        return detectionTime > fiveMinutesAgo;
      })
      .slice(-10); // Last 10 detections

    setRecentDetections(recent);
  }, [detections]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'flying': return 'default';
      case 'online': return 'secondary';
      case 'offline': return 'destructive';
      case 'low_battery': return 'destructive';
      case 'error': return 'destructive';
      default: return 'outline';
    }
  };

  const getFlightModeColor = (mode: string) => {
    switch (mode) {
      case 'mission': return 'default';
      case 'auto': return 'secondary';
      case 'manual': return 'outline';
      case 'rtl': return 'destructive';
      default: return 'outline';
    }
  };

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  };

  const getBatteryColor = (level: number) => {
    if (level < 15) return 'text-red-500';
    if (level < 30) return 'text-orange-500';
    if (level < 50) return 'text-yellow-500';
    return 'text-green-500';
  };

  const selectedDroneData = selectedDrone ? drones[selectedDrone] : null;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Overview Stats */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="w-5 h-5" />
            Simulation Overview
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center p-3 bg-muted rounded-lg">
              <div className="text-2xl font-bold">{stats.total_drones}</div>
              <div className="text-sm text-muted-foreground">Total Drones</div>
            </div>
            <div className="text-center p-3 bg-muted rounded-lg">
              <div className="text-2xl font-bold text-green-600">{stats.active_drones}</div>
              <div className="text-sm text-muted-foreground">Active Drones</div>
            </div>
            <div className="text-center p-3 bg-muted rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{stats.total_detections}</div>
              <div className="text-sm text-muted-foreground">Total Detections</div>
            </div>
            <div className="text-center p-3 bg-muted rounded-lg">
              <div className="text-2xl font-bold text-purple-600">{stats.recent_detections}</div>
              <div className="text-sm text-muted-foreground">Recent (5m)</div>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Average Confidence</span>
              <span>{stats.average_confidence.toFixed(1)}%</span>
            </div>
            <Progress value={stats.average_confidence} className="h-2" />
          </div>

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="font-medium">Uptime: </span>
              {formatDuration(stats.uptime)}
            </div>
            <div>
              <span className="font-medium">Flight Time: </span>
              {formatDuration(stats.total_flight_time)}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Connection Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Signal className="w-5 h-5" />
            System Status
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="font-medium">Connection</span>
            <Badge variant={isConnected ? 'default' : 'destructive'}>
              {isConnected ? 'Connected' : 'Disconnected'}
            </Badge>
          </div>

          <div className="flex items-center justify-between">
            <span className="font-medium">Simulation</span>
            <Badge variant={isRunning ? 'default' : 'secondary'}>
              {isRunning ? 'Running' : 'Stopped'}
            </Badge>
          </div>

          <div className="flex items-center justify-between">
            <span className="font-medium">Discoveries</span>
            <div className="flex items-center gap-2">
              <Target className="w-4 h-4" />
              <span className="font-bold text-lg">{stats.discoveries}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Drone List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="w-5 h-5" />
            Active Drones
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {Object.entries(drones).map(([droneId, drone]) => (
              <div
                key={droneId}
                className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                  selectedDrone === droneId ? 'border-blue-500 bg-blue-50' : 'hover:bg-gray-50'
                }`}
                onClick={() => setSelectedDrone(selectedDrone === droneId ? null : droneId)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">Drone {droneId}</span>
                    <Badge variant={getStatusColor(drone.status)} className="text-xs">
                      {drone.status}
                    </Badge>
                  </div>
                  <div className="text-right text-sm">
                    <div>{drone.position.altitude.toFixed(0)}m</div>
                    <div className={getBatteryColor(drone.battery.level)}>
                      {drone.battery.level.toFixed(0)}%
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Selected Drone Details */}
      {selectedDroneData && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MapPin className="w-5 h-5" />
              Drone {selectedDrone} Details
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Position */}
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-medium">Position:</span>
                <div className="mt-1 space-y-1">
                  <div>Lat: {selectedDroneData.position.latitude.toFixed(6)}</div>
                  <div>Lon: {selectedDroneData.position.longitude.toFixed(6)}</div>
                  <div>Alt: {selectedDroneData.position.altitude.toFixed(1)}m</div>
                </div>
              </div>
              <div>
                <span className="font-medium">Movement:</span>
                <div className="mt-1 space-y-1">
                  <div>Speed: {selectedDroneData.position.ground_speed.toFixed(1)}m/s</div>
                  <div>Heading: {selectedDroneData.position.heading.toFixed(0)}°</div>
                  <div>Mode: <Badge variant={getFlightModeColor(selectedDroneData.flight_mode)} className="text-xs">{selectedDroneData.flight_mode}</Badge></div>
                </div>
              </div>
            </div>

            {/* Battery */}
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="font-medium">Battery</span>
                <span className={getBatteryColor(selectedDroneData.battery.level)}>
                  {selectedDroneData.battery.level.toFixed(1)}%
                </span>
              </div>
              <Progress value={selectedDroneData.battery.level} className="h-2" />
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>Voltage: {selectedDroneData.battery.voltage.toFixed(1)}V</div>
                <div>Time: {formatTime(selectedDroneData.battery.time_remaining)}</div>
              </div>
            </div>

            {/* Environment */}
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="flex items-center gap-2">
                <Wind className="w-4 h-4 text-muted-foreground" />
                <div>
                  <div className="font-medium">Wind</div>
                  <div>{selectedDroneData.wind_speed.toFixed(1)}m/s</div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Thermometer className="w-4 h-4 text-muted-foreground" />
                <div>
                  <div className="font-medium">Signal</div>
                  <div>{selectedDroneData.signal_strength}%</div>
                </div>
              </div>
            </div>

            {/* Mission Progress */}
            {selectedDroneData.mission_progress > 0 && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="font-medium">Mission Progress</span>
                  <span>{selectedDroneData.mission_progress.toFixed(1)}%</span>
                </div>
                <Progress value={selectedDroneData.mission_progress} className="h-2" />
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Recent Detections */}
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Eye className="w-5 h-5" />
            Recent Detections (Last 5 minutes)
          </CardTitle>
        </CardHeader>
        <CardContent>
          {recentDetections.length > 0 ? (
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {recentDetections.map(detection => (
                <div key={detection.event_id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-3">
                    <Target className="w-4 h-4 text-blue-500" />
                    <div>
                      <div className="font-medium capitalize">{detection.object_type}</div>
                      <div className="text-sm text-muted-foreground">
                        Drone {detection.drone_id} • {detection.detection_method}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <div className="text-sm font-medium">
                        {detection.confidence_score.toFixed(1)}%
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {new Date(detection.timestamp).toLocaleTimeString()}
                      </div>
                    </div>
                    <Badge variant="outline" className="text-xs">
                      {detection.position[2].toFixed(0)}m
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <Alert>
              <AlertTriangle className="w-4 h-4" />
              <AlertDescription>
                No recent detections. Objects may not be in detection range or conditions may not be favorable.
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default SimulationDashboard;
