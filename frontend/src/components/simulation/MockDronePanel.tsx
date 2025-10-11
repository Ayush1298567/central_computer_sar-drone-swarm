import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Alert, AlertDescription } from '../ui/alert';
import {
  Plane,
  Battery,
  Signal,
  MapPin,
  Play,
  Square,
  RotateCcw,
  AlertTriangle,
  CheckCircle,
  Clock
} from 'lucide-react';

interface DroneData {
  drone_id: string;
  status: string;
  flight_mode: string;
  armed: boolean;
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
  mission?: {
    current_mission_id: string;
    progress: number;
    current_waypoint: number;
    total_waypoints: number;
  };
}

interface MockDronePanelProps {
  drone: DroneData;
  onArm: (droneId: string) => void;
  onDisarm: (droneId: string) => void;
  onTakeoff: (droneId: string, altitude: number) => void;
  onLand: (droneId: string) => void;
  onReturnToLaunch: (droneId: string) => void;
  onStartMission: (droneId: string, missionId: string) => void;
}

const MockDronePanel: React.FC<MockDronePanelProps> = ({
  drone,
  onArm,
  onDisarm,
  onTakeoff,
  onLand,
  onReturnToLaunch,
  onStartMission
}) => {
  const [takeoffAltitude, setTakeoffAltitude] = useState(10);
  const [selectedMission, setSelectedMission] = useState('');

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

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'flying': return <Plane className="w-4 h-4" />;
      case 'online': return <CheckCircle className="w-4 h-4" />;
      case 'offline': return <AlertTriangle className="w-4 h-4" />;
      case 'low_battery': return <Battery className="w-4 h-4" />;
      case 'error': return <AlertTriangle className="w-4 h-4" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

  const formatBatteryLevel = (level: number) => {
    if (level < 15) return 'critical';
    if (level < 30) return 'low';
    if (level < 50) return 'medium';
    return 'high';
  };

  const getBatteryColor = (level: number) => {
    if (level < 15) return 'bg-red-500';
    if (level < 30) return 'bg-orange-500';
    if (level < 50) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const formatTimeRemaining = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-lg">
          <div className="flex items-center gap-2">
            {getStatusIcon(drone.status)}
            Drone {drone.drone_id}
          </div>
          <Badge variant={getStatusColor(drone.status)}>
            {drone.status.toUpperCase()}
          </Badge>
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Position Information */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <MapPin className="w-4 h-4 text-muted-foreground" />
              <span className="font-medium">Position</span>
            </div>
            <div className="pl-6 space-y-1">
              <div>Lat: {drone.position.latitude.toFixed(6)}</div>
              <div>Lon: {drone.position.longitude.toFixed(6)}</div>
              <div>Alt: {drone.position.altitude.toFixed(1)}m</div>
              <div>Speed: {drone.position.ground_speed.toFixed(1)}m/s</div>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Battery className="w-4 h-4 text-muted-foreground" />
              <span className="font-medium">Battery</span>
            </div>
            <div className="pl-6 space-y-1">
              <div className="flex items-center gap-2">
                <div className="flex-1">
                  <Progress
                    value={drone.battery.level}
                    className="h-2"
                  />
                </div>
                <span className="text-sm font-medium">
                  {drone.battery.level.toFixed(1)}%
                </span>
              </div>
              <div>Voltage: {drone.battery.voltage.toFixed(1)}V</div>
              <div>Time: {formatTimeRemaining(drone.battery.time_remaining)}</div>
              {drone.battery.level < 15 && (
                <Alert className="mt-2">
                  <AlertTriangle className="w-4 h-4" />
                  <AlertDescription className="text-xs">
                    Low battery - return to launch recommended
                  </AlertDescription>
                </Alert>
              )}
            </div>
          </div>
        </div>

        {/* Flight Mode and Armed Status */}
        <div className="flex items-center justify-between text-sm">
          <div>
            <span className="font-medium">Flight Mode: </span>
            <Badge variant="outline">{drone.flight_mode.toUpperCase()}</Badge>
          </div>
          <div>
            <span className="font-medium">Armed: </span>
            <Badge variant={drone.armed ? 'default' : 'secondary'}>
              {drone.armed ? 'YES' : 'NO'}
            </Badge>
          </div>
        </div>

        {/* Mission Progress */}
        {drone.mission && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-medium text-sm">Mission Progress</span>
              <span className="text-sm">{drone.mission.progress.toFixed(1)}%</span>
            </div>
            <Progress value={drone.mission.progress} className="h-2" />
            <div className="text-xs text-muted-foreground">
              Waypoint {drone.mission.current_waypoint} of {drone.mission.total_waypoints}
            </div>
          </div>
        )}

        {/* Control Buttons */}
        <div className="grid grid-cols-2 gap-2">
          {!drone.armed ? (
            <Button
              onClick={() => onArm(drone.drone_id)}
              disabled={drone.status === 'offline'}
              size="sm"
            >
              ARM
            </Button>
          ) : (
            <Button
              onClick={() => onDisarm(drone.drone_id)}
              variant="outline"
              size="sm"
            >
              DISARM
            </Button>
          )}

          {drone.status === 'online' && drone.armed && !drone.mission ? (
            <div className="space-y-1">
              <input
                type="number"
                value={takeoffAltitude}
                onChange={(e) => setTakeoffAltitude(parseInt(e.target.value))}
                className="w-full px-2 py-1 text-xs border rounded"
                min="5"
                max="50"
                placeholder="Alt (m)"
              />
              <Button
                onClick={() => onTakeoff(drone.drone_id, takeoffAltitude)}
                size="sm"
                className="w-full"
              >
                <Play className="w-3 h-3 mr-1" />
                TAKEOFF
              </Button>
            </div>
          ) : null}

          {drone.status === 'flying' && (
            <>
              <Button
                onClick={() => onLand(drone.drone_id)}
                variant="outline"
                size="sm"
              >
                <Square className="w-3 h-3 mr-1" />
                LAND
              </Button>
              <Button
                onClick={() => onReturnToLaunch(drone.drone_id)}
                variant="outline"
                size="sm"
              >
                RTL
              </Button>
            </>
          )}
        </div>

        {/* Mission Selection (when not flying) */}
        {drone.status === 'online' && !drone.mission && (
          <div className="space-y-2">
            <select
              value={selectedMission}
              onChange={(e) => setSelectedMission(e.target.value)}
              className="w-full px-3 py-2 text-sm border rounded-md"
            >
              <option value="">Select Mission</option>
              <option value="building_collapse">Building Collapse</option>
              <option value="wilderness_search">Wilderness Search</option>
              <option value="maritime_search">Maritime Search</option>
            </select>
            {selectedMission && (
              <Button
                onClick={() => onStartMission(drone.drone_id, selectedMission)}
                className="w-full"
                size="sm"
              >
                Start Mission
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default MockDronePanel;
