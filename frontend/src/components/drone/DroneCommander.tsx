import React, { useState, useEffect } from 'react';
import { 
  Play, 
  Square, 
  Home, 
  Navigation,
  AlertTriangle,
  Send,
  MapPin,
  Clock,
  CheckCircle,
  XCircle,
  Loader
} from 'lucide-react';
import { Drone, DroneCommand } from '../../types/drone';
import { apiService } from '../../services/api';
import { webSocketService } from '../../services/websocket';

interface DroneCommanderProps {
  drone: Drone;
  onCommandSent?: (command: DroneCommand) => void;
  onEmergencyStop?: (drone: Drone) => void;
  className?: string;
}

interface CommandForm {
  type: 'takeoff' | 'land' | 'goto' | 'hover' | 'return_home' | 'emergency_stop';
  parameters: {
    latitude?: number;
    longitude?: number;
    altitude?: number;
    speed?: number;
    duration?: number;
  };
  priority: 'low' | 'medium' | 'high' | 'emergency';
}

export const DroneCommander: React.FC<DroneCommanderProps> = ({
  drone,
  onCommandSent,
  onEmergencyStop,
  className = '',
}) => {
  const [commandForm, setCommandForm] = useState<CommandForm>({
    type: 'takeoff',
    parameters: {},
    priority: 'medium',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [recentCommands, setRecentCommands] = useState<DroneCommand[]>([]);
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Subscribe to command updates
  useEffect(() => {
    const handleCommandUpdate = (data: any) => {
      if (data.drone_id === drone.id) {
        setRecentCommands(prev => {
          const updated = prev.map(cmd => 
            cmd.id === data.id ? { ...cmd, ...data } : cmd
          );
          // Add new command if not exists
          if (!updated.find(cmd => cmd.id === data.id)) {
            updated.unshift(data);
          }
          return updated.slice(0, 5); // Keep only recent 5 commands
        });
      }
    };

    webSocketService.subscribe('drone_command_update', handleCommandUpdate);

    return () => {
      webSocketService.unsubscribe('drone_command_update', handleCommandUpdate);
    };
  }, [drone.id]);

  const handleSendCommand = async () => {
    setIsLoading(true);
    try {
      const command = await apiService.sendDroneCommand(drone.id, {
        command_type: commandForm.type,
        parameters: commandForm.parameters,
        priority: commandForm.priority,
      });

      setRecentCommands(prev => [command, ...prev.slice(0, 4)]);
      onCommandSent?.(command);

      // Reset form
      setCommandForm({
        type: 'takeoff',
        parameters: {},
        priority: 'medium',
      });
    } catch (error) {
      console.error('Failed to send command:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleEmergencyStop = async () => {
    setIsLoading(true);
    try {
      await apiService.emergencyStopDrone(drone.id);
      onEmergencyStop?.(drone);
    } catch (error) {
      console.error('Failed to emergency stop drone:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickCommand = async (type: CommandForm['type'], parameters: any = {}) => {
    setIsLoading(true);
    try {
      const command = await apiService.sendDroneCommand(drone.id, {
        command_type: type,
        parameters,
        priority: type === 'emergency_stop' ? 'emergency' : 'high',
      });

      setRecentCommands(prev => [command, ...prev.slice(0, 4)]);
      onCommandSent?.(command);
    } catch (error) {
      console.error('Failed to send quick command:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getCommandIcon = (type: string) => {
    switch (type) {
      case 'takeoff': return <Play size={16} />;
      case 'land': return <Square size={16} />;
      case 'goto': return <Navigation size={16} />;
      case 'hover': return <Clock size={16} />;
      case 'return_home': return <Home size={16} />;
      case 'emergency_stop': return <AlertTriangle size={16} />;
      default: return <Send size={16} />;
    }
  };

  const getCommandStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-100';
      case 'executing': return 'text-blue-600 bg-blue-100';
      case 'pending': return 'text-yellow-600 bg-yellow-100';
      case 'failed': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getCommandStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle size={14} />;
      case 'executing': return <Loader size={14} className="animate-spin" />;
      case 'pending': return <Clock size={14} />;
      case 'failed': return <XCircle size={14} />;
      default: return <Clock size={14} />;
    }
  };

  const canSendCommand = () => {
    return drone.status !== 'offline' && drone.status !== 'error' && !isLoading;
  };

  return (
    <div className={`bg-white rounded-lg shadow-lg ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Drone Commander</h3>
            <p className="text-sm text-gray-600">
              Control {drone.name} ({drone.status})
            </p>
          </div>
          
          <button
            onClick={handleEmergencyStop}
            disabled={!canSendCommand()}
            className="btn btn-danger text-sm"
          >
            <AlertTriangle size={16} className="mr-1" />
            Emergency Stop
          </button>
        </div>
      </div>

      {/* Quick Commands */}
      <div className="p-6 border-b border-gray-200">
        <h4 className="font-medium text-gray-900 mb-4">Quick Commands</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <button
            onClick={() => handleQuickCommand('takeoff', { altitude: 10 })}
            disabled={!canSendCommand() || drone.status === 'active'}
            className="btn btn-primary text-sm"
          >
            <Play size={16} className="mr-1" />
            Takeoff
          </button>
          
          <button
            onClick={() => handleQuickCommand('land')}
            disabled={!canSendCommand() || drone.status !== 'active'}
            className="btn btn-secondary text-sm"
          >
            <Square size={16} className="mr-1" />
            Land
          </button>
          
          <button
            onClick={() => handleQuickCommand('hover', { duration: 30 })}
            disabled={!canSendCommand() || drone.status !== 'active'}
            className="btn btn-secondary text-sm"
          >
            <Clock size={16} className="mr-1" />
            Hover
          </button>
          
          <button
            onClick={() => handleQuickCommand('return_home')}
            disabled={!canSendCommand() || drone.status !== 'active'}
            className="btn btn-warning text-sm"
          >
            <Home size={16} className="mr-1" />
            Return Home
          </button>
        </div>
      </div>

      {/* Advanced Commands */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h4 className="font-medium text-gray-900">Advanced Commands</h4>
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            {showAdvanced ? 'Hide' : 'Show'} Advanced
          </button>
        </div>

        {showAdvanced && (
          <div className="space-y-4">
            {/* Command Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Command Type
              </label>
              <select
                value={commandForm.type}
                onChange={(e) => setCommandForm(prev => ({ 
                  ...prev, 
                  type: e.target.value as CommandForm['type'],
                  parameters: {} // Reset parameters when type changes
                }))}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="takeoff">Takeoff</option>
                <option value="land">Land</option>
                <option value="goto">Go To Location</option>
                <option value="hover">Hover</option>
                <option value="return_home">Return Home</option>
              </select>
            </div>

            {/* Parameters based on command type */}
            {commandForm.type === 'goto' && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    <MapPin size={14} className="inline mr-1" />
                    Latitude
                  </label>
                  <input
                    type="number"
                    step="0.000001"
                    value={commandForm.parameters.latitude || ''}
                    onChange={(e) => setCommandForm(prev => ({
                      ...prev,
                      parameters: { ...prev.parameters, latitude: parseFloat(e.target.value) }
                    }))}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="37.7749"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    <MapPin size={14} className="inline mr-1" />
                    Longitude
                  </label>
                  <input
                    type="number"
                    step="0.000001"
                    value={commandForm.parameters.longitude || ''}
                    onChange={(e) => setCommandForm(prev => ({
                      ...prev,
                      parameters: { ...prev.parameters, longitude: parseFloat(e.target.value) }
                    }))}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="-122.4194"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    <Navigation size={14} className="inline mr-1" />
                    Altitude (m)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="400"
                    value={commandForm.parameters.altitude || ''}
                    onChange={(e) => setCommandForm(prev => ({
                      ...prev,
                      parameters: { ...prev.parameters, altitude: parseInt(e.target.value) }
                    }))}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="50"
                  />
                </div>
              </div>
            )}

            {commandForm.type === 'takeoff' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <Navigation size={14} className="inline mr-1" />
                  Takeoff Altitude (m)
                </label>
                <input
                  type="number"
                  min="1"
                  max="400"
                  value={commandForm.parameters.altitude || 10}
                  onChange={(e) => setCommandForm(prev => ({
                    ...prev,
                    parameters: { ...prev.parameters, altitude: parseInt(e.target.value) }
                  }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            )}

            {commandForm.type === 'hover' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <Clock size={14} className="inline mr-1" />
                  Duration (seconds)
                </label>
                <input
                  type="number"
                  min="1"
                  max="3600"
                  value={commandForm.parameters.duration || 30}
                  onChange={(e) => setCommandForm(prev => ({
                    ...prev,
                    parameters: { ...prev.parameters, duration: parseInt(e.target.value) }
                  }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            )}

            {/* Priority */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Priority
              </label>
              <select
                value={commandForm.priority}
                onChange={(e) => setCommandForm(prev => ({ 
                  ...prev, 
                  priority: e.target.value as CommandForm['priority']
                }))}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="emergency">Emergency</option>
              </select>
            </div>

            {/* Send Command Button */}
            <button
              onClick={handleSendCommand}
              disabled={!canSendCommand()}
              className="w-full btn btn-primary"
            >
              {isLoading ? (
                <Loader size={16} className="mr-2 animate-spin" />
              ) : (
                <Send size={16} className="mr-2" />
              )}
              Send Command
            </button>
          </div>
        )}
      </div>

      {/* Recent Commands */}
      <div className="p-6">
        <h4 className="font-medium text-gray-900 mb-4">Recent Commands</h4>
        {recentCommands.length === 0 ? (
          <p className="text-gray-500 text-sm">No recent commands</p>
        ) : (
          <div className="space-y-2">
            {recentCommands.map(command => (
              <div key={command.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="flex items-center justify-center w-8 h-8 bg-blue-100 rounded-full">
                    {getCommandIcon(command.command_type)}
                  </div>
                  <div>
                    <div className="font-medium text-gray-900 capitalize">
                      {command.command_type.replace('_', ' ')}
                    </div>
                    <div className="text-sm text-gray-600">
                      {new Date(command.created_at).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getCommandStatusColor(command.status)}`}>
                    {getCommandStatusIcon(command.status)}
                    <span className="ml-1 capitalize">{command.status}</span>
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};