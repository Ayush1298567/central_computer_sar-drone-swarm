import React, { useState, useEffect } from 'react';
import { AlertTriangle, Zap, Home, Play, Pause, Shield } from 'lucide-react';
import { Drone, EmergencySituation } from '../../types';
import { apiService } from '../../utils/api';

interface EmergencyPanelProps {
  drones: Drone[];
  onEmergencyAction: (action: string, droneId: string, data?: any) => void;
}

const EmergencyPanel: React.FC<EmergencyPanelProps> = ({ drones, onEmergencyAction }) => {
  const [emergencySituations, setEmergencySituations] = useState<EmergencySituation[]>([]);
  const [isProcessing, setIsProcessing] = useState<{ [droneId: string]: boolean }>({});
  const [globalEmergencyMode, setGlobalEmergencyMode] = useState(false);

  useEffect(() => {
    loadEmergencySituations();
    const interval = setInterval(loadEmergencySituations, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadEmergencySituations = async () => {
    try {
      const situations = await apiService.getEmergencySituations();
      setEmergencySituations(situations);
    } catch (error) {
      console.error('Failed to load emergency situations:', error);
    }
  };

  const handleEmergencyStop = async (droneId: string) => {
    setIsProcessing(prev => ({ ...prev, [droneId]: true }));

    try {
      const result = await apiService.emergencyStop(droneId);
      if (result.success) {
        onEmergencyAction('emergency_stop', droneId, { timestamp: new Date().toISOString() });
      }
    } catch (error) {
      console.error('Emergency stop failed:', error);
    } finally {
      setIsProcessing(prev => ({ ...prev, [droneId]: false }));
    }
  };

  const handleReturnToHome = async (droneId: string) => {
    setIsProcessing(prev => ({ ...prev, [droneId]: true }));

    try {
      const result = await apiService.returnToHome(droneId);
      if (result.success) {
        onEmergencyAction('return_to_home', droneId, { timestamp: new Date().toISOString() });
      }
    } catch (error) {
      console.error('Return to home failed:', error);
    } finally {
      setIsProcessing(prev => ({ ...prev, [droneId]: false }));
    }
  };

  const handleGlobalEmergencyStop = async () => {
    setGlobalEmergencyMode(true);
    const activeDrones = drones.filter(drone =>
      drone.status === 'flying' || drone.status === 'online'
    );

    for (const drone of activeDrones) {
      await handleEmergencyStop(drone.id);
    }

    setGlobalEmergencyMode(false);
  };

  const handleGlobalReturnToHome = async () => {
    setGlobalEmergencyMode(true);
    const activeDrones = drones.filter(drone =>
      drone.status === 'flying' || drone.status === 'online'
    );

    for (const drone of activeDrones) {
      await handleReturnToHome(drone.id);
    }

    setGlobalEmergencyMode(false);
  };

  const getCriticalDrones = () => {
    return drones.filter(drone =>
      drone.battery_level < 20 ||
      drone.signal_strength < 30 ||
      drone.connection_status === 'unstable'
    );
  };

  const criticalDrones = getCriticalDrones();

  return (
    <div className="bg-red-50 border-2 border-red-200 rounded-lg p-6">
      <div className="flex items-center mb-4">
        <AlertTriangle className="h-6 w-6 text-red-600 mr-2" />
        <h2 className="text-xl font-bold text-red-800">Emergency Controls</h2>
      </div>

      {/* Active Emergency Situations */}
      {emergencySituations.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-red-700 mb-2">Active Emergencies</h3>
          <div className="space-y-2">
            {emergencySituations.map(situation => (
              <div key={situation.id} className="bg-red-100 border border-red-300 rounded p-3">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-medium text-red-800">{situation.description}</p>
                    <p className="text-sm text-red-600">
                      Affected Drones: {situation.affected_drones.join(', ')}
                    </p>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    situation.severity === 'critical' ? 'bg-red-600 text-white' :
                    situation.severity === 'high' ? 'bg-orange-600 text-white' :
                    situation.severity === 'medium' ? 'bg-yellow-600 text-white' :
                    'bg-blue-600 text-white'
                  }`}>
                    {situation.severity.toUpperCase()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Critical Drone Warnings */}
      {criticalDrones.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-orange-700 mb-2">Critical Drone Status</h3>
          <div className="space-y-2">
            {criticalDrones.map(drone => (
              <div key={drone.id} className="bg-orange-100 border border-orange-300 rounded p-3">
                <div className="flex justify-between items-center">
                  <div>
                    <p className="font-medium text-orange-800">{drone.name}</p>
                    <div className="text-sm text-orange-600">
                      {drone.battery_level < 20 && <span>Battery: {drone.battery_level}%</span>}
                      {drone.signal_strength < 30 && <span> | Signal: {drone.signal_strength}%</span>}
                      {drone.connection_status === 'unstable' && <span> | Unstable Connection</span>}
                    </div>
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleEmergencyStop(drone.id)}
                      disabled={isProcessing[drone.id]}
                      className="bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white px-3 py-2 rounded text-sm font-medium flex items-center"
                    >
                      <Zap className="h-4 w-4 mr-1" />
                      {isProcessing[drone.id] ? 'Stopping...' : 'EMERGENCY STOP'}
                    </button>
                    <button
                      onClick={() => handleReturnToHome(drone.id)}
                      disabled={isProcessing[drone.id]}
                      className="bg-orange-600 hover:bg-orange-700 disabled:bg-orange-400 text-white px-3 py-2 rounded text-sm font-medium flex items-center"
                    >
                      <Home className="h-4 w-4 mr-1" />
                      {isProcessing[drone.id] ? 'Returning...' : 'RTH'}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Global Emergency Controls */}
      <div className="border-t border-red-200 pt-4">
        <h3 className="text-lg font-semibold text-red-700 mb-4">Global Emergency Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <button
            onClick={handleGlobalEmergencyStop}
            disabled={globalEmergencyMode || drones.filter(d => d.status === 'flying').length === 0}
            className="bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white py-4 px-6 rounded-lg text-lg font-bold flex items-center justify-center"
          >
            <Zap className="h-6 w-6 mr-2" />
            EMERGENCY STOP ALL
          </button>
          <button
            onClick={handleGlobalReturnToHome}
            disabled={globalEmergencyMode || drones.filter(d => d.status === 'flying').length === 0}
            className="bg-orange-600 hover:bg-orange-700 disabled:bg-gray-400 text-white py-4 px-6 rounded-lg text-lg font-bold flex items-center justify-center"
          >
            <Home className="h-6 w-6 mr-2" />
            RETURN ALL TO HOME
          </button>
        </div>

        {globalEmergencyMode && (
          <div className="mt-4 bg-red-600 text-white p-3 rounded-lg text-center">
            <Shield className="h-5 w-5 inline mr-2" />
            Global Emergency Mode Active - All drones responding...
          </div>
        )}
      </div>

      {/* Emergency Status Summary */}
      <div className="mt-6 pt-4 border-t border-red-200">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-red-600">{drones.filter(d => d.status === 'flying').length}</div>
            <div className="text-sm text-gray-600">Flying</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-orange-600">{criticalDrones.length}</div>
            <div className="text-sm text-gray-600">Critical</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-green-600">{emergencySituations.filter(s => s.status === 'resolved').length}</div>
            <div className="text-sm text-gray-600">Resolved</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmergencyPanel;