import React, { useState, useCallback, useEffect } from 'react';
import {
  PlayIcon,
  PauseIcon,
  StopIcon,
  HomeIcon,
  CameraIcon,
  MapPinIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  ArrowLeftIcon,
  ArrowRightIcon,
  ExclamationTriangleIcon,
  Cog6ToothIcon,
  RadioIcon
} from '@heroicons/react/24/outline';
import { Drone, DroneStatus, Coordinates } from '../../types';
import { useDrones } from '../../hooks/useDrones';

interface DroneCommanderProps {
  drone: Drone;
  onCommand?: (command: any) => void;
  disabled?: boolean;
  className?: string;
}

interface ManualControlState {
  enabled: boolean;
  speed: number;
  altitude: number;
  heading: number;
}

interface CameraControlState {
  zoom: number;
  tilt: number;
  pan: number;
  recording: boolean;
  quality: string;
}

const DroneCommander: React.FC<DroneCommanderProps> = ({
  drone,
  onCommand,
  disabled = false,
  className = ''
}) => {
  const { sendCommand, emergencyStop } = useDrones();
  const [activeTab, setActiveTab] = useState<'basic' | 'manual' | 'camera' | 'advanced'>('basic');
  const [manualControl, setManualControl] = useState<ManualControlState>({
    enabled: false,
    speed: 5,
    altitude: 100,
    heading: 0
  });
  const [cameraControl, setCameraControl] = useState<CameraControlState>({
    zoom: 1,
    tilt: 0,
    pan: 0,
    recording: false,
    quality: 'medium'
  });
  const [customCommand, setCustomCommand] = useState('');
  const [isExecuting, setIsExecuting] = useState(false);
  const [lastCommand, setLastCommand] = useState<string | null>(null);

  // Update camera state from drone telemetry
  useEffect(() => {
    if (drone.telemetry?.camera) {
      setCameraControl(prev => ({
        ...prev,
        recording: drone.telemetry!.camera.isRecording,
        quality: drone.telemetry!.camera.quality,
        zoom: drone.telemetry!.camera.zoom
      }));
    }
  }, [drone.telemetry]);

  // Execute command
  const executeCommand = useCallback(async (command: any) => {
    setIsExecuting(true);
    setLastCommand(command.action || 'custom');
    
    try {
      if (onCommand) {
        await onCommand(command);
      } else {
        await sendCommand(drone.id, command);
      }
    } catch (error) {
      console.error('Command execution failed:', error);
    } finally {
      setIsExecuting(false);
      setTimeout(() => setLastCommand(null), 2000);
    }
  }, [drone.id, onCommand, sendCommand]);

  // Basic commands
  const handleBasicCommand = useCallback((action: string, params?: any) => {
    executeCommand({ action, ...params });
  }, [executeCommand]);

  // Manual movement commands
  const handleMovement = useCallback((direction: string, distance: number = 10) => {
    const commands: Record<string, any> = {
      forward: { action: 'move', direction: 'forward', distance },
      backward: { action: 'move', direction: 'backward', distance },
      left: { action: 'move', direction: 'left', distance },
      right: { action: 'move', direction: 'right', distance },
      up: { action: 'move', direction: 'up', distance },
      down: { action: 'move', direction: 'down', distance }
    };

    executeCommand(commands[direction]);
  }, [executeCommand]);

  // Rotation commands
  const handleRotation = useCallback((direction: 'left' | 'right', degrees: number = 45) => {
    executeCommand({
      action: 'rotate',
      direction,
      degrees
    });
  }, [executeCommand]);

  // Go to coordinates
  const handleGoTo = useCallback((coordinates: Coordinates, altitude?: number) => {
    executeCommand({
      action: 'goto',
      latitude: coordinates.latitude,
      longitude: coordinates.longitude,
      altitude: altitude || manualControl.altitude
    });
  }, [executeCommand, manualControl.altitude]);

  // Camera commands
  const handleCameraCommand = useCallback((action: string, params?: any) => {
    executeCommand({ action: `camera_${action}`, ...params });
  }, [executeCommand]);

  // Emergency stop
  const handleEmergencyStop = useCallback(async () => {
    if (window.confirm('Are you sure you want to emergency stop this drone?')) {
      setIsExecuting(true);
      try {
        await emergencyStop(drone.id);
      } catch (error) {
        console.error('Emergency stop failed:', error);
      } finally {
        setIsExecuting(false);
      }
    }
  }, [drone.id, emergencyStop]);

  // Custom command
  const handleCustomCommand = useCallback(() => {
    if (!customCommand.trim()) return;
    
    try {
      const command = JSON.parse(customCommand);
      executeCommand(command);
      setCustomCommand('');
    } catch (error) {
      alert('Invalid JSON command format');
    }
  }, [customCommand, executeCommand]);

  // Check if drone can accept commands
  const canAcceptCommands = !disabled && 
    drone.isConnected && 
    drone.status !== DroneStatus.OFFLINE && 
    drone.status !== DroneStatus.EMERGENCY;

  // Render basic controls
  const renderBasicControls = () => (
    <div className="space-y-4">
      {/* Mission controls */}
      <div className="grid grid-cols-2 gap-3">
        {drone.status === DroneStatus.IDLE && (
          <button
            onClick={() => handleBasicCommand('start_mission')}
            disabled={!canAcceptCommands || isExecuting}
            className="flex items-center justify-center px-4 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <PlayIcon className="w-5 h-5 mr-2" />
            Start Mission
          </button>
        )}

        {drone.status === DroneStatus.ACTIVE && (
          <>
            <button
              onClick={() => handleBasicCommand('pause')}
              disabled={!canAcceptCommands || isExecuting}
              className="flex items-center justify-center px-4 py-3 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <PauseIcon className="w-5 h-5 mr-2" />
              Pause
            </button>

            <button
              onClick={() => handleBasicCommand('resume')}
              disabled={!canAcceptCommands || isExecuting}
              className="flex items-center justify-center px-4 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <PlayIcon className="w-5 h-5 mr-2" />
              Resume
            </button>
          </>
        )}

        <button
          onClick={() => handleBasicCommand('return_home')}
          disabled={!canAcceptCommands || isExecuting}
          className="flex items-center justify-center px-4 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <HomeIcon className="w-5 h-5 mr-2" />
          Return Home
        </button>

        <button
          onClick={() => handleBasicCommand('land')}
          disabled={!canAcceptCommands || isExecuting}
          className="flex items-center justify-center px-4 py-3 bg-orange-500 text-white rounded-lg hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <ArrowDownIcon className="w-5 h-5 mr-2" />
          Land
        </button>
      </div>

      {/* Emergency stop */}
      <button
        onClick={handleEmergencyStop}
        disabled={!drone.isConnected || isExecuting}
        className="w-full flex items-center justify-center px-4 py-3 bg-red-500 text-white rounded-lg hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed font-semibold"
      >
        <ExclamationTriangleIcon className="w-5 h-5 mr-2" />
        EMERGENCY STOP
      </button>
    </div>
  );

  // Render manual controls
  const renderManualControls = () => (
    <div className="space-y-4">
      {/* Manual control toggle */}
      <div className="flex items-center justify-between p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
        <div>
          <div className="font-medium text-yellow-900">Manual Control Mode</div>
          <div className="text-sm text-yellow-700">Direct drone movement control</div>
        </div>
        <button
          onClick={() => setManualControl(prev => ({ ...prev, enabled: !prev.enabled }))}
          disabled={!canAcceptCommands}
          className={`px-3 py-1 rounded-full text-sm font-medium ${
            manualControl.enabled
              ? 'bg-yellow-500 text-white'
              : 'bg-white text-yellow-700 border border-yellow-300'
          }`}
        >
          {manualControl.enabled ? 'Enabled' : 'Disabled'}
        </button>
      </div>

      {manualControl.enabled && (
        <>
          {/* Movement controls */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-3">Movement</h4>
            
            {/* Directional pad */}
            <div className="grid grid-cols-3 gap-2 max-w-48 mx-auto mb-4">
              <div></div>
              <button
                onClick={() => handleMovement('forward')}
                disabled={!canAcceptCommands || isExecuting}
                className="p-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
              >
                <ArrowUpIcon className="w-5 h-5" />
              </button>
              <div></div>

              <button
                onClick={() => handleMovement('left')}
                disabled={!canAcceptCommands || isExecuting}
                className="p-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
              >
                <ArrowLeftIcon className="w-5 h-5" />
              </button>

              <div className="p-3 bg-gray-300 rounded-lg flex items-center justify-center">
                <MapPinIcon className="w-5 h-5 text-gray-600" />
              </div>

              <button
                onClick={() => handleMovement('right')}
                disabled={!canAcceptCommands || isExecuting}
                className="p-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
              >
                <ArrowRightIcon className="w-5 h-5" />
              </button>

              <div></div>
              <button
                onClick={() => handleMovement('backward')}
                disabled={!canAcceptCommands || isExecuting}
                className="p-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
              >
                <ArrowDownIcon className="w-5 h-5" />
              </button>
              <div></div>
            </div>

            {/* Altitude controls */}
            <div className="flex justify-center space-x-4">
              <button
                onClick={() => handleMovement('up')}
                disabled={!canAcceptCommands || isExecuting}
                className="flex items-center px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50"
              >
                <ArrowUpIcon className="w-4 h-4 mr-1" />
                Up
              </button>
              
              <button
                onClick={() => handleMovement('down')}
                disabled={!canAcceptCommands || isExecuting}
                className="flex items-center px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 disabled:opacity-50"
              >
                <ArrowDownIcon className="w-4 h-4 mr-1" />
                Down
              </button>
            </div>
          </div>

          {/* Speed and altitude settings */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Speed (m/s)
              </label>
              <input
                type="range"
                min="1"
                max="20"
                value={manualControl.speed}
                onChange={(e) => setManualControl(prev => ({ ...prev, speed: parseInt(e.target.value) }))}
                className="w-full"
              />
              <div className="text-center text-sm text-gray-600">{manualControl.speed} m/s</div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Target Altitude (m)
              </label>
              <input
                type="range"
                min="10"
                max="500"
                value={manualControl.altitude}
                onChange={(e) => setManualControl(prev => ({ ...prev, altitude: parseInt(e.target.value) }))}
                className="w-full"
              />
              <div className="text-center text-sm text-gray-600">{manualControl.altitude} m</div>
            </div>
          </div>
        </>
      )}
    </div>
  );

  // Render camera controls
  const renderCameraControls = () => (
    <div className="space-y-4">
      {/* Recording controls */}
      <div className="grid grid-cols-2 gap-3">
        <button
          onClick={() => handleCameraCommand('start_recording')}
          disabled={!canAcceptCommands || isExecuting || cameraControl.recording}
          className="flex items-center justify-center px-4 py-3 bg-red-500 text-white rounded-lg hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <CameraIcon className="w-5 h-5 mr-2" />
          Start Recording
        </button>

        <button
          onClick={() => handleCameraCommand('stop_recording')}
          disabled={!canAcceptCommands || isExecuting || !cameraControl.recording}
          className="flex items-center justify-center px-4 py-3 bg-gray-500 text-white rounded-lg hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <StopIcon className="w-5 h-5 mr-2" />
          Stop Recording
        </button>
      </div>

      {/* Camera settings */}
      <div className="bg-gray-50 p-4 rounded-lg space-y-4">
        <h4 className="font-medium text-gray-900">Camera Settings</h4>

        {/* Zoom */}
        <div>
          <div className="flex justify-between items-center mb-1">
            <label className="text-sm font-medium text-gray-700">Zoom</label>
            <span className="text-sm text-gray-600">{cameraControl.zoom}x</span>
          </div>
          <input
            type="range"
            min="1"
            max="10"
            step="0.1"
            value={cameraControl.zoom}
            onChange={(e) => {
              const zoom = parseFloat(e.target.value);
              setCameraControl(prev => ({ ...prev, zoom }));
              handleCameraCommand('set_zoom', { zoom });
            }}
            disabled={!canAcceptCommands}
            className="w-full"
          />
        </div>

        {/* Quality */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Quality
          </label>
          <select
            value={cameraControl.quality}
            onChange={(e) => {
              const quality = e.target.value;
              setCameraControl(prev => ({ ...prev, quality }));
              handleCameraCommand('set_quality', { quality });
            }}
            disabled={!canAcceptCommands}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="low">Low (480p)</option>
            <option value="medium">Medium (720p)</option>
            <option value="high">High (1080p)</option>
            <option value="ultra">Ultra (4K)</option>
          </select>
        </div>

        {/* Pan and Tilt */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="text-sm font-medium text-gray-700">Pan</label>
              <span className="text-sm text-gray-600">{cameraControl.pan}°</span>
            </div>
            <input
              type="range"
              min="-180"
              max="180"
              value={cameraControl.pan}
              onChange={(e) => {
                const pan = parseInt(e.target.value);
                setCameraControl(prev => ({ ...prev, pan }));
                handleCameraCommand('set_pan', { pan });
              }}
              disabled={!canAcceptCommands}
              className="w-full"
            />
          </div>

          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="text-sm font-medium text-gray-700">Tilt</label>
              <span className="text-sm text-gray-600">{cameraControl.tilt}°</span>
            </div>
            <input
              type="range"
              min="-90"
              max="90"
              value={cameraControl.tilt}
              onChange={(e) => {
                const tilt = parseInt(e.target.value);
                setCameraControl(prev => ({ ...prev, tilt }));
                handleCameraCommand('set_tilt', { tilt });
              }}
              disabled={!canAcceptCommands}
              className="w-full"
            />
          </div>
        </div>

        {/* Reset camera */}
        <button
          onClick={() => {
            setCameraControl(prev => ({ ...prev, pan: 0, tilt: 0, zoom: 1 }));
            handleCameraCommand('reset_camera');
          }}
          disabled={!canAcceptCommands || isExecuting}
          className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
        >
          Reset Camera Position
        </button>
      </div>
    </div>
  );

  // Render advanced controls
  const renderAdvancedControls = () => (
    <div className="space-y-4">
      {/* System commands */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <h4 className="font-medium text-gray-900 mb-3">System Commands</h4>
        
        <div className="grid grid-cols-2 gap-3">
          <button
            onClick={() => handleBasicCommand('reboot')}
            disabled={!canAcceptCommands || isExecuting}
            className="px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 disabled:opacity-50"
          >
            <Cog6ToothIcon className="w-4 h-4 inline mr-1" />
            Reboot
          </button>

          <button
            onClick={() => handleBasicCommand('calibrate')}
            disabled={!canAcceptCommands || isExecuting}
            className="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 disabled:opacity-50"
          >
            <RadioIcon className="w-4 h-4 inline mr-1" />
            Calibrate
          </button>
        </div>
      </div>

      {/* Custom command */}
      <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg">
        <h4 className="font-medium text-yellow-900 mb-3">Custom Command</h4>
        <p className="text-sm text-yellow-700 mb-3">
          Send a custom JSON command to the drone. Use with caution.
        </p>
        
        <textarea
          value={customCommand}
          onChange={(e) => setCustomCommand(e.target.value)}
          placeholder='{"action": "custom_action", "parameter": "value"}'
          className="w-full border border-yellow-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-yellow-500 font-mono text-sm"
          rows={3}
        />
        
        <button
          onClick={handleCustomCommand}
          disabled={!canAcceptCommands || isExecuting || !customCommand.trim()}
          className="mt-2 px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 disabled:opacity-50"
        >
          Execute Command
        </button>
      </div>
    </div>
  );

  return (
    <div className={`bg-white rounded-lg border shadow-sm ${className}`}>
      {/* Header */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Drone Commander
            </h3>
            <p className="text-sm text-gray-600">
              {drone.name} • {drone.status}
            </p>
          </div>
          
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${
              drone.isConnected ? 'bg-green-500' : 'bg-red-500'
            }`} />
            <span className="text-sm text-gray-600">
              {drone.isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>

        {/* Status indicators */}
        <div className="mt-3 flex items-center space-x-4 text-sm">
          <div className="flex items-center space-x-1">
            <span className="text-gray-600">Battery:</span>
            <span className={`font-medium ${
              drone.battery > 50 ? 'text-green-600' :
              drone.battery > 20 ? 'text-yellow-600' : 'text-red-600'
            }`}>
              {drone.battery}%
            </span>
          </div>
          
          <div className="flex items-center space-x-1">
            <span className="text-gray-600">Signal:</span>
            <span className={`font-medium ${
              drone.signalStrength > 70 ? 'text-green-600' :
              drone.signalStrength > 40 ? 'text-yellow-600' : 'text-red-600'
            }`}>
              {drone.signalStrength}%
            </span>
          </div>

          {isExecuting && (
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
              <span className="text-blue-600">
                Executing{lastCommand ? ` ${lastCommand}` : ''}...
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b">
        <nav className="flex space-x-8 px-4">
          {[
            { id: 'basic', label: 'Basic' },
            { id: 'manual', label: 'Manual' },
            { id: 'camera', label: 'Camera' },
            { id: 'advanced', label: 'Advanced' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-3 text-sm font-medium border-b-2 ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      <div className="p-4">
        {!canAcceptCommands && (
          <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-center space-x-2">
              <ExclamationTriangleIcon className="w-5 h-5 text-yellow-500" />
              <span className="text-yellow-700">
                {!drone.isConnected 
                  ? 'Drone is disconnected' 
                  : drone.status === DroneStatus.OFFLINE 
                    ? 'Drone is offline'
                    : drone.status === DroneStatus.EMERGENCY
                      ? 'Drone is in emergency state'
                      : 'Commands are disabled'}
              </span>
            </div>
          </div>
        )}

        {activeTab === 'basic' && renderBasicControls()}
        {activeTab === 'manual' && renderManualControls()}
        {activeTab === 'camera' && renderCameraControls()}
        {activeTab === 'advanced' && renderAdvancedControls()}
      </div>
    </div>
  );
};

export default DroneCommander;