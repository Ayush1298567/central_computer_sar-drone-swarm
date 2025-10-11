import React, { useState, useEffect } from 'react';
import { Plane, Battery, Signal, Settings, Plus, Trash2, Edit, Save, X } from 'lucide-react';
import { Drone, DroneSettings as DroneSettingsType } from '../../types';
import { apiService } from '../../utils/api';

interface DroneSettingsProps {
  drones: Drone[];
  onClose?: () => void;
}

interface DroneFormData {
  id: string;
  name: string;
  model: string;
  max_flight_time: number;
  cruise_speed: number;
  max_range: number;
  coverage_rate: number;
  camera_specs: any;
  sensor_specs: any;
  maintenance_schedule: any;
}

const DroneSettings: React.FC<DroneSettingsProps> = ({ drones, onClose }) => {
  const [droneList, setDroneList] = useState<Drone[]>(drones);
  const [selectedDrone, setSelectedDrone] = useState<string>('');
  const [isEditing, setIsEditing] = useState(false);
  const [isAdding, setIsAdding] = useState(false);
  const [formData, setFormData] = useState<DroneFormData>({
    id: '',
    name: '',
    model: '',
    max_flight_time: 25,
    cruise_speed: 10,
    max_range: 5000,
    coverage_rate: 0.1,
    camera_specs: {},
    sensor_specs: {},
    maintenance_schedule: {},
  });

  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    setDroneList(drones);
  }, [drones]);

  const handleDroneSelect = async (droneId: string) => {
    setSelectedDrone(droneId);
    setIsEditing(false);
    setIsAdding(false);

    if (droneId) {
      try {
        const droneSettings = await apiService.getDroneSettings(droneId);
        setFormData({
          id: droneSettings.id,
          name: droneSettings.name,
          model: droneSettings.model,
          max_flight_time: droneSettings.max_flight_time,
          cruise_speed: droneSettings.cruise_speed,
          max_range: droneSettings.max_range,
          coverage_rate: droneSettings.coverage_rate,
          camera_specs: droneSettings.camera_specs || {},
          sensor_specs: droneSettings.sensor_specs || {},
          maintenance_schedule: droneSettings.maintenance_schedule || {},
        });
      } catch (error) {
        console.error('Failed to load drone settings:', error);
      }
    }
  };

  const handleSaveDrone = async () => {
    setIsLoading(true);
    try {
      const result = await apiService.updateDroneSettings(formData.id, formData);
      if (result.success) {
        // Update local drone list
        setDroneList(prev =>
          prev.map(drone =>
            drone.id === formData.id
              ? {
                  ...drone,
                  name: formData.name,
                  max_flight_time: formData.max_flight_time,
                  cruise_speed: formData.cruise_speed,
                  max_range: formData.max_range,
                  coverage_rate: formData.coverage_rate,
                }
              : drone
          )
        );
        setIsEditing(false);
        alert('Drone settings saved successfully');
      } else {
        alert('Failed to save drone settings');
      }
    } catch (error) {
      console.error('Failed to save drone settings:', error);
      alert('Failed to save drone settings');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddDrone = () => {
    setIsAdding(true);
    setIsEditing(false);
    setSelectedDrone('');
    setFormData({
      id: `drone-${Date.now()}`,
      name: '',
      model: '',
      max_flight_time: 25,
      cruise_speed: 10,
      max_range: 5000,
      coverage_rate: 0.1,
      camera_specs: {},
      sensor_specs: {},
      maintenance_schedule: {},
    });
  };

  const handleDeleteDrone = async (droneId: string) => {
    if (confirm('Are you sure you want to delete this drone? This action cannot be undone.')) {
      try {
        // In a real implementation, you would call an API to delete the drone
        setDroneList(prev => prev.filter(drone => drone.id !== droneId));
        if (selectedDrone === droneId) {
          setSelectedDrone('');
        }
        alert('Drone deleted successfully');
      } catch (error) {
        console.error('Failed to delete drone:', error);
        alert('Failed to delete drone');
      }
    }
  };

  const updateFormData = <K extends keyof DroneFormData>(key: K, value: DroneFormData[K]) => {
    setFormData(prev => ({ ...prev, [key]: value }));
  };

  const getStatusColor = (status: Drone['status']) => {
    switch (status) {
      case 'online': return 'text-green-600 bg-green-100';
      case 'flying': return 'text-blue-600 bg-blue-100';
      case 'charging': return 'text-yellow-600 bg-yellow-100';
      case 'maintenance': return 'text-red-600 bg-red-100';
      case 'offline': return 'text-gray-600 bg-gray-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const formatLastSeen = (lastSeen?: string) => {
    if (!lastSeen) return 'Never';
    const date = new Date(lastSeen);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMinutes = Math.floor(diffMs / (1000 * 60));

    if (diffMinutes < 1) return 'Just now';
    if (diffMinutes < 60) return `${diffMinutes}m ago`;

    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) return `${diffHours}h ago`;

    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <Plane className="h-6 w-6 text-blue-600 mr-2" />
          <h2 className="text-xl font-bold text-gray-800">Drone Management</h2>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={handleAddDrone}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md text-sm font-medium flex items-center"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Drone
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600"
            >
              ×
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Drone List */}
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Registered Drones</h3>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {droneList.map(drone => (
              <div
                key={drone.id}
                className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                  selectedDrone === drone.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:bg-gray-50'
                }`}
                onClick={() => handleDroneSelect(drone.id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center mb-2">
                      <h4 className="font-medium text-gray-800">{drone.name}</h4>
                      <span className={`ml-2 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(drone.status)}`}>
                        {drone.status}
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-sm text-gray-600">
                      <div>Battery: {drone.battery_level}%</div>
                      <div>Signal: {drone.signal_strength}%</div>
                      <div>Range: {drone.max_range}m</div>
                      <div>Missions: {drone.missions_completed}</div>
                    </div>
                    <div className="text-xs text-gray-500 mt-2">
                      Last seen: {formatLastSeen(drone.last_seen)}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2 ml-4">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setIsEditing(true);
                        setIsAdding(false);
                        handleDroneSelect(drone.id);
                      }}
                      className="p-1 text-gray-400 hover:text-gray-600"
                    >
                      <Edit className="h-4 w-4" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteDrone(drone.id);
                      }}
                      className="p-1 text-red-400 hover:text-red-600"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Drone Configuration */}
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-4">
            {isAdding ? 'Add New Drone' : isEditing ? 'Edit Drone Settings' : 'Drone Configuration'}
          </h3>

          {selectedDrone || isAdding ? (
            <div className="space-y-4">
              {/* Basic Information */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Drone ID
                  </label>
                  <input
                    type="text"
                    value={formData.id}
                    onChange={(e) => updateFormData('id', e.target.value)}
                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="drone-001"
                    disabled={!isAdding}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Drone Name
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => updateFormData('name', e.target.value)}
                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Alpha Drone"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Model
                  </label>
                  <select
                    value={formData.model}
                    onChange={(e) => updateFormData('model', e.target.value)}
                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Select Model</option>
                    <option value="DJI Mavic 3">DJI Mavic 3</option>
                    <option value="DJI Phantom 4">DJI Phantom 4</option>
                    <option value="Custom SAR Drone">Custom SAR Drone</option>
                    <option value="Parrot Anafi">Parrot Anafi</option>
                  </select>
                </div>
              </div>

              {/* Performance Settings */}
              <div>
                <h4 className="font-medium text-gray-800 mb-3">Performance Settings</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Max Flight Time (minutes)
                    </label>
                    <input
                      type="number"
                      min="10"
                      max="120"
                      value={formData.max_flight_time}
                      onChange={(e) => updateFormData('max_flight_time', parseInt(e.target.value))}
                      className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Cruise Speed (m/s)
                    </label>
                    <input
                      type="number"
                      min="5"
                      max="25"
                      step="0.1"
                      value={formData.cruise_speed}
                      onChange={(e) => updateFormData('cruise_speed', parseFloat(e.target.value))}
                      className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Max Range (meters)
                    </label>
                    <input
                      type="number"
                      min="1000"
                      max="10000"
                      value={formData.max_range}
                      onChange={(e) => updateFormData('max_range', parseInt(e.target.value))}
                      className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Coverage Rate (km²/minute)
                    </label>
                    <input
                      type="number"
                      min="0.01"
                      max="1"
                      step="0.01"
                      value={formData.coverage_rate}
                      onChange={(e) => updateFormData('coverage_rate', parseFloat(e.target.value))}
                      className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center space-x-3 pt-4 border-t border-gray-200">
                <button
                  onClick={handleSaveDrone}
                  disabled={isLoading}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white py-2 px-4 rounded-md font-medium flex items-center justify-center"
                >
                  {isLoading ? (
                    <>
                      <Settings className="h-4 w-4 mr-2 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save className="h-4 w-4 mr-2" />
                      Save Settings
                    </>
                  )}
                </button>
                {(isEditing || isAdding) && (
                  <button
                    onClick={() => {
                      setIsEditing(false);
                      setIsAdding(false);
                      setSelectedDrone('');
                    }}
                    className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md font-medium"
                  >
                    Cancel
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <Plane className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>Select a drone to view or edit its settings</p>
            </div>
          )}
        </div>
      </div>

      {/* Summary Statistics */}
      <div className="mt-8 pt-6 border-t border-gray-200">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Fleet Summary</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-blue-600">{droneList.length}</div>
            <div className="text-sm text-blue-700">Total Drones</div>
          </div>
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-green-600">
              {droneList.filter(d => d.status === 'online' || d.status === 'flying').length}
            </div>
            <div className="text-sm text-green-700">Active Drones</div>
          </div>
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-yellow-600">
              {droneList.reduce((sum, d) => sum + d.missions_completed, 0)}
            </div>
            <div className="text-sm text-yellow-700">Total Missions</div>
          </div>
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-purple-600">
              {droneList.length > 0 ? (droneList.reduce((sum, d) => sum + d.battery_level, 0) / droneList.length).toFixed(0) : 0}%
            </div>
            <div className="text-sm text-purple-700">Avg Battery</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DroneSettings;
