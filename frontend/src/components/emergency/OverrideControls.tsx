import React, { useState, useEffect } from 'react';
import { Settings, Navigation, Camera, Zap, AlertTriangle, CheckCircle } from 'lucide-react';
import { Drone, Coordinate } from '../../types';
import { apiService } from '../../utils/api';

interface OverrideControlsProps {
  drones: Drone[];
  onManualCommand: (droneId: string, command: any) => void;
}

interface ManualCommand {
  type: 'move' | 'altitude' | 'heading' | 'speed' | 'camera' | 'emergency';
  droneId: string;
  parameters: any;
  timestamp: Date;
  status: 'pending' | 'executing' | 'completed' | 'failed';
}

const OverrideControls: React.FC<OverrideControlsProps> = ({ drones, onManualCommand }) => {
  const [selectedDrone, setSelectedDrone] = useState<string>('');
  const [manualCommands, setManualCommands] = useState<ManualCommand[]>([]);
  const [commandHistory, setCommandHistory] = useState<ManualCommand[]>([]);
  const [isOverrideMode, setIsOverrideMode] = useState(false);

  // Movement controls
  const [moveParameters, setMoveParameters] = useState({
    latitude: '',
    longitude: '',
    altitude: '',
  });

  // Camera controls
  const [cameraParameters, setCameraParameters] = useState({
    zoom: 1,
    angle: 0,
    recording: false,
  });

  const activeDrones = drones.filter(drone => drone.status === 'flying' || drone.status === 'online');

  const handleManualMove = async () => {
    if (!selectedDrone || !moveParameters.latitude || !moveParameters.longitude) {
      return;
    }

    const command: ManualCommand = {
      type: 'move',
      droneId: selectedDrone,
      parameters: {
        target: {
          lat: parseFloat(moveParameters.latitude),
          lng: parseFloat(moveParameters.longitude),
          alt: moveParameters.altitude ? parseFloat(moveParameters.altitude) : undefined,
        },
      },
      timestamp: new Date(),
      status: 'pending',
    };

    setManualCommands(prev => [...prev, command]);
    onManualCommand(selectedDrone, command);

    // Simulate command execution
    setTimeout(() => {
      setManualCommands(prev =>
        prev.map(cmd =>
          cmd === command ? { ...cmd, status: 'completed' } : cmd
        )
      );
      setCommandHistory(prev => [...prev, { ...command, status: 'completed' }]);
    }, 2000);
  };

  const handleEmergencyOverride = async (droneId: string) => {
    const command: ManualCommand = {
      type: 'emergency',
      droneId,
      parameters: {
        action: 'manual_override',
        reason: 'Emergency manual control activated',
      },
      timestamp: new Date(),
      status: 'pending',
    };

    setManualCommands(prev => [...prev, command]);
    onManualCommand(droneId, command);

    // Simulate emergency override
    setTimeout(() => {
      setManualCommands(prev =>
        prev.map(cmd =>
          cmd === command ? { ...cmd, status: 'completed' } : cmd
        )
      );
      setCommandHistory(prev => [...prev, { ...command, status: 'completed' }]);
    }, 1000);
  };

  const handleCameraControl = async () => {
    if (!selectedDrone) return;

    const command: ManualCommand = {
      type: 'camera',
      droneId: selectedDrone,
      parameters: cameraParameters,
      timestamp: new Date(),
      status: 'pending',
    };

    setManualCommands(prev => [...prev, command]);
    onManualCommand(selectedDrone, command);

    setTimeout(() => {
      setManualCommands(prev =>
        prev.map(cmd =>
          cmd === command ? { ...cmd, status: 'completed' } : cmd
        )
      );
      setCommandHistory(prev => [...prev, { ...command, status: 'completed' }]);
    }, 1500);
  };

  const getStatusColor = (status: ManualCommand['status']) => {
    switch (status) {
      case 'pending': return 'text-yellow-600 bg-yellow-50';
      case 'executing': return 'text-blue-600 bg-blue-50';
      case 'completed': return 'text-green-600 bg-green-50';
      case 'failed': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getStatusIcon = (status: ManualCommand['status']) => {
    switch (status) {
      case 'pending': return <AlertTriangle className="h-4 w-4" />;
      case 'executing': return <Settings className="h-4 w-4 animate-spin" />;
      case 'completed': return <CheckCircle className="h-4 w-4" />;
      case 'failed': return <AlertTriangle className="h-4 w-4" />;
      default: return <Settings className="h-4 w-4" />;
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <Settings className="h-6 w-6 text-purple-600 mr-2" />
          <h2 className="text-xl font-bold text-gray-800">Manual Override Controls</h2>
        </div>
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${isOverrideMode ? 'bg-red-500' : 'bg-green-500'}`} />
          <span className="text-sm text-gray-600">
            {isOverrideMode ? 'Override Mode Active' : 'Auto Mode'}
          </span>
        </div>
      </div>

      {/* Drone Selection */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Select Drone for Manual Control
        </label>
        <select
          value={selectedDrone}
          onChange={(e) => setSelectedDrone(e.target.value)}
          className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
        >
          <option value="">Select a drone...</option>
          {activeDrones.map(drone => (
            <option key={drone.id} value={drone.id}>
              {drone.name} - {drone.status} ({drone.battery_level}% battery)
            </option>
          ))}
        </select>
      </div>

      {selectedDrone && (
        <>
          {/* Emergency Override Toggle */}
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-red-800">Emergency Override</h3>
                <p className="text-sm text-red-700">
                  Enable manual control for emergency situations
                </p>
              </div>
              <button
                onClick={() => setIsOverrideMode(!isOverrideMode)}
                className={`px-4 py-2 rounded-md font-medium ${
                  isOverrideMode
                    ? 'bg-red-600 hover:bg-red-700 text-white'
                    : 'bg-gray-200 hover:bg-gray-300 text-gray-700'
                }`}
              >
                {isOverrideMode ? 'Disable Override' : 'Enable Override'}
              </button>
            </div>
            {isOverrideMode && (
              <div className="mt-3">
                <button
                  onClick={() => handleEmergencyOverride(selectedDrone)}
                  className="w-full bg-red-600 hover:bg-red-700 text-white py-2 px-4 rounded-md font-bold"
                >
                  ACTIVATE EMERGENCY OVERRIDE
                </button>
              </div>
            )}
          </div>

          {/* Movement Controls */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
              <Navigation className="h-5 w-5 mr-2" />
              Movement Controls
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Latitude
                </label>
                <input
                  type="number"
                  step="0.000001"
                  value={moveParameters.latitude}
                  onChange={(e) => setMoveParameters(prev => ({ ...prev, latitude: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  placeholder="40.7128"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Longitude
                </label>
                <input
                  type="number"
                  step="0.000001"
                  value={moveParameters.longitude}
                  onChange={(e) => setMoveParameters(prev => ({ ...prev, longitude: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  placeholder="-74.0060"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Altitude (m)
                </label>
                <input
                  type="number"
                  value={moveParameters.altitude}
                  onChange={(e) => setMoveParameters(prev => ({ ...prev, altitude: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  placeholder="20"
                />
              </div>
            </div>
            <button
              onClick={handleManualMove}
              disabled={!moveParameters.latitude || !moveParameters.longitude}
              className="mt-3 w-full bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white py-2 px-4 rounded-md font-medium"
            >
              Move to Position
            </button>
          </div>

          {/* Camera Controls */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
              <Camera className="h-5 w-5 mr-2" />
              Camera Controls
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Zoom Level
                </label>
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={cameraParameters.zoom}
                  onChange={(e) => setCameraParameters(prev => ({ ...prev, zoom: parseInt(e.target.value) }))}
                  className="w-full"
                />
                <span className="text-sm text-gray-600">{cameraParameters.zoom}x</span>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Camera Angle
                </label>
                <input
                  type="range"
                  min="-90"
                  max="90"
                  value={cameraParameters.angle}
                  onChange={(e) => setCameraParameters(prev => ({ ...prev, angle: parseInt(e.target.value) }))}
                  className="w-full"
                />
                <span className="text-sm text-gray-600">{cameraParameters.angle}°</span>
              </div>
              <div className="flex items-center">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={cameraParameters.recording}
                    onChange={(e) => setCameraParameters(prev => ({ ...prev, recording: e.target.checked }))}
                    className="mr-2"
                  />
                  <span className="text-sm font-medium text-gray-700">Recording</span>
                </label>
              </div>
            </div>
            <button
              onClick={handleCameraControl}
              className="mt-3 w-full bg-purple-600 hover:bg-purple-700 text-white py-2 px-4 rounded-md font-medium"
            >
              Apply Camera Settings
            </button>
          </div>
        </>
      )}

      {/* Command Status */}
      {manualCommands.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Command Status</h3>
          <div className="space-y-2">
            {manualCommands.map((command, index) => (
              <div key={index} className={`border rounded p-3 ${getStatusColor(command.status)}`}>
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-medium text-gray-800 capitalize">
                      {command.type} Command
                    </span>
                    <span className="text-sm text-gray-600 ml-2">
                      {command.droneId} - {command.timestamp.toLocaleTimeString()}
                    </span>
                  </div>
                  <div className="flex items-center">
                    {getStatusIcon(command.status)}
                    <span className="ml-2 text-sm font-medium capitalize">
                      {command.status}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Command History */}
      {commandHistory.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Recent Commands</h3>
          <div className="space-y-2 max-h-40 overflow-y-auto">
            {commandHistory.slice(-5).map((command, index) => (
              <div key={index} className="border border-gray-200 rounded p-2 bg-gray-50">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium text-gray-800 capitalize">
                    {command.type}
                  </span>
                  <span className="text-gray-600">
                    {command.timestamp.toLocaleTimeString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Safety Warning */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-start">
          <AlertTriangle className="h-5 w-5 text-yellow-600 mr-2 mt-0.5" />
          <div>
            <h4 className="text-sm font-semibold text-yellow-800">Safety Warning</h4>
            <p className="text-sm text-yellow-700 mt-1">
              Manual override controls should only be used in emergency situations.
              Ensure all safety protocols are followed and maintain visual contact with the drone.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OverrideControls;
