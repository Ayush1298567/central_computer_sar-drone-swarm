import React, { useState, useEffect } from 'react';
import { Shield, AlertTriangle, CheckCircle, XCircle, Wifi, WifiOff, Battery, Thermometer, Wind } from 'lucide-react';
import { Drone, Mission } from '../../types';

interface SafetyMonitorProps {
  drones: Drone[];
  currentMission?: Mission;
  weatherConditions?: {
    temperature: number;
    windSpeed: number;
    windDirection: number;
    visibility: number;
  };
}

interface SafetyCheck {
  id: string;
  type: 'drone' | 'weather' | 'communication' | 'system';
  status: 'pass' | 'warning' | 'fail';
  message: string;
  droneId?: string;
  timestamp: Date;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

const SafetyMonitor: React.FC<SafetyMonitorProps> = ({
  drones,
  currentMission,
  weatherConditions
}) => {
  const [safetyChecks, setSafetyChecks] = useState<SafetyCheck[]>([]);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [isMonitoring, setIsMonitoring] = useState(true);

  useEffect(() => {
    performSafetyChecks();
    const interval = setInterval(performSafetyChecks, 10000); // Check every 10 seconds
    return () => clearInterval(interval);
  }, [drones, currentMission, weatherConditions]);

  const performSafetyChecks = () => {
    const checks: SafetyCheck[] = [];
    const now = new Date();

    // Drone-specific checks
    drones.forEach(drone => {
      // Battery check
      if (drone.battery_level < 20) {
        checks.push({
          id: `battery-${drone.id}`,
          type: 'drone',
          status: drone.battery_level < 10 ? 'fail' : 'warning',
          message: `Drone ${drone.name} battery at ${drone.battery_level}%`,
          droneId: drone.id,
          timestamp: now,
          severity: drone.battery_level < 10 ? 'critical' : 'high'
        });
      } else {
        checks.push({
          id: `battery-${drone.id}`,
          type: 'drone',
          status: 'pass',
          message: `Drone ${drone.name} battery OK (${drone.battery_level}%)`,
          droneId: drone.id,
          timestamp: now,
          severity: 'low'
        });
      }

      // Signal strength check
      if (drone.signal_strength < 30) {
        checks.push({
          id: `signal-${drone.id}`,
          type: 'communication',
          status: drone.signal_strength < 10 ? 'fail' : 'warning',
          message: `Drone ${drone.name} signal strength at ${drone.signal_strength}%`,
          droneId: drone.id,
          timestamp: now,
          severity: drone.signal_strength < 10 ? 'critical' : 'high'
        });
      } else {
        checks.push({
          id: `signal-${drone.id}`,
          type: 'communication',
          status: 'pass',
          message: `Drone ${drone.name} signal OK (${drone.signal_strength}%)`,
          droneId: drone.id,
          timestamp: now,
          severity: 'low'
        });
      }

      // Connection status check
      if (drone.connection_status === 'unstable' || drone.connection_status === 'disconnected') {
        checks.push({
          id: `connection-${drone.id}`,
          type: 'communication',
          status: 'fail',
          message: `Drone ${drone.name} connection ${drone.connection_status}`,
          droneId: drone.id,
          timestamp: now,
          severity: 'critical'
        });
      } else {
        checks.push({
          id: `connection-${drone.id}`,
          type: 'communication',
          status: 'pass',
          message: `Drone ${drone.name} connection stable`,
          droneId: drone.id,
          timestamp: now,
          severity: 'low'
        });
      }
    });

    // Weather checks
    if (weatherConditions) {
      if (weatherConditions.windSpeed > 15) {
        checks.push({
          id: 'wind-high',
          type: 'weather',
          status: 'warning',
          message: `High winds detected (${weatherConditions.windSpeed} m/s)`,
          timestamp: now,
          severity: 'high'
        });
      } else {
        checks.push({
          id: 'wind-ok',
          type: 'weather',
          status: 'pass',
          message: `Wind conditions acceptable (${weatherConditions.windSpeed} m/s)`,
          timestamp: now,
          severity: 'low'
        });
      }

      if (weatherConditions.temperature < 0 || weatherConditions.temperature > 40) {
        checks.push({
          id: 'temperature-extreme',
          type: 'weather',
          status: 'warning',
          message: `Extreme temperature: ${weatherConditions.temperature}°C`,
          timestamp: now,
          severity: 'medium'
        });
      } else {
        checks.push({
          id: 'temperature-ok',
          type: 'weather',
          status: 'pass',
          message: `Temperature acceptable (${weatherConditions.temperature}°C)`,
          timestamp: now,
          severity: 'low'
        });
      }

      if (weatherConditions.visibility < 1000) {
        checks.push({
          id: 'visibility-poor',
          type: 'weather',
          status: 'warning',
          message: `Poor visibility: ${weatherConditions.visibility}m`,
          timestamp: now,
          severity: 'medium'
        });
      } else {
        checks.push({
          id: 'visibility-ok',
          type: 'weather',
          status: 'pass',
          message: `Visibility acceptable (${weatherConditions.visibility}m)`,
          timestamp: now,
          severity: 'low'
        });
      }
    }

    // Mission-specific checks
    if (currentMission) {
      if (currentMission.status === 'active') {
        const flyingDrones = drones.filter(d => d.status === 'flying');
        const expectedDrones = currentMission.assigned_drone_count;

        if (flyingDrones.length < expectedDrones) {
          checks.push({
            id: 'mission-drones-missing',
            type: 'system',
            status: 'warning',
            message: `Mission active but only ${flyingDrones.length}/${expectedDrones} drones flying`,
            timestamp: now,
            severity: 'high'
          });
        } else {
          checks.push({
            id: 'mission-drones-ok',
            type: 'system',
            status: 'pass',
            message: `All mission drones operational (${flyingDrones.length}/${expectedDrones})`,
            timestamp: now,
            severity: 'low'
          });
        }
      }
    }

    setSafetyChecks(checks);
    setLastUpdate(now);
  };

  const getStatusColor = (status: SafetyCheck['status']) => {
    switch (status) {
      case 'pass': return 'text-green-600';
      case 'warning': return 'text-yellow-600';
      case 'fail': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusIcon = (status: SafetyCheck['status']) => {
    switch (status) {
      case 'pass': return <CheckCircle className="h-4 w-4" />;
      case 'warning': return <AlertTriangle className="h-4 w-4" />;
      case 'fail': return <XCircle className="h-4 w-4" />;
      default: return <Shield className="h-4 w-4" />;
    }
  };

  const getSeverityColor = (severity: SafetyCheck['severity']) => {
    switch (severity) {
      case 'critical': return 'border-red-500 bg-red-50';
      case 'high': return 'border-orange-500 bg-orange-50';
      case 'medium': return 'border-yellow-500 bg-yellow-50';
      case 'low': return 'border-green-500 bg-green-50';
      default: return 'border-gray-500 bg-gray-50';
    }
  };

  const criticalIssues = safetyChecks.filter(check => check.severity === 'critical' && check.status !== 'pass');
  const warningIssues = safetyChecks.filter(check => check.severity === 'high' && check.status !== 'pass');
  const passedChecks = safetyChecks.filter(check => check.status === 'pass');

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <Shield className="h-6 w-6 text-blue-600 mr-2" />
          <h2 className="text-xl font-bold text-gray-800">Safety Monitor</h2>
        </div>
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${isMonitoring ? 'bg-green-500' : 'bg-gray-400'}`} />
          <span className="text-sm text-gray-600">
            Last update: {lastUpdate.toLocaleTimeString()}
          </span>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-red-50 border border-red-200 rounded p-3 text-center">
          <div className="text-2xl font-bold text-red-600">{criticalIssues.length}</div>
          <div className="text-sm text-red-700">Critical</div>
        </div>
        <div className="bg-orange-50 border border-orange-200 rounded p-3 text-center">
          <div className="text-2xl font-bold text-orange-600">{warningIssues.length}</div>
          <div className="text-sm text-orange-700">Warnings</div>
        </div>
        <div className="bg-green-50 border border-green-200 rounded p-3 text-center">
          <div className="text-2xl font-bold text-green-600">{passedChecks.length}</div>
          <div className="text-sm text-green-700">OK</div>
        </div>
        <div className="bg-blue-50 border border-blue-200 rounded p-3 text-center">
          <div className="text-2xl font-bold text-blue-600">{safetyChecks.length}</div>
          <div className="text-sm text-blue-700">Total Checks</div>
        </div>
      </div>

      {/* Critical Issues */}
      {criticalIssues.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-red-700 mb-2 flex items-center">
            <XCircle className="h-5 w-5 mr-2" />
            Critical Issues
          </h3>
          <div className="space-y-2">
            {criticalIssues.map(check => (
              <div key={check.id} className="border border-red-300 bg-red-50 rounded p-3">
                <div className="flex items-center">
                  <XCircle className="h-5 w-5 text-red-600 mr-2" />
                  <span className="font-medium text-red-800">{check.message}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Warnings */}
      {warningIssues.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-orange-700 mb-2 flex items-center">
            <AlertTriangle className="h-5 w-5 mr-2" />
            Warnings
          </h3>
          <div className="space-y-2">
            {warningIssues.map(check => (
              <div key={check.id} className="border border-orange-300 bg-orange-50 rounded p-3">
                <div className="flex items-center">
                  <AlertTriangle className="h-5 w-5 text-orange-600 mr-2" />
                  <span className="font-medium text-orange-800">{check.message}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* All Safety Checks */}
      <div className="space-y-2">
        <h3 className="text-lg font-semibold text-gray-700 mb-2">All Safety Checks</h3>
        {safetyChecks.map(check => (
          <div key={check.id} className={`border rounded p-3 ${getSeverityColor(check.severity)}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <span className={getStatusColor(check.status)}>
                  {getStatusIcon(check.status)}
                </span>
                <span className="ml-2 text-sm font-medium text-gray-800">{check.message}</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-xs text-gray-500 capitalize">{check.type}</span>
                <span className="text-xs text-gray-500">
                  {check.timestamp.toLocaleTimeString()}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Weather Information */}
      {weatherConditions && (
        <div className="mt-6 pt-4 border-t border-gray-200">
          <h3 className="text-lg font-semibold text-gray-700 mb-3 flex items-center">
            <Thermometer className="h-5 w-5 mr-2" />
            Weather Conditions
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-lg font-semibold text-gray-800">{weatherConditions.temperature}°C</div>
              <div className="text-sm text-gray-600">Temperature</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-semibold text-gray-800">{weatherConditions.windSpeed} m/s</div>
              <div className="text-sm text-gray-600">Wind Speed</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-semibold text-gray-800">{weatherConditions.windDirection}°</div>
              <div className="text-sm text-gray-600">Wind Direction</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-semibold text-gray-800">{weatherConditions.visibility}m</div>
              <div className="text-sm text-gray-600">Visibility</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SafetyMonitor;