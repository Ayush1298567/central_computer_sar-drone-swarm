import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { 
  CheckCircle, 
  AlertTriangle, 
  Clock, 
  MapPin, 
  Zap, 
  Users, 
  Eye,
  Edit,
  Save,
  X
} from 'lucide-react';
import { Mission, MissionPriority } from '../../types/mission';
import { apiService } from '../../services/api';
import { CreateMissionRequest } from '../../types/api';

interface MissionPreviewProps {
  mission: Partial<Mission>;
  onMissionCreate: (mission: Mission) => void;
}

const MissionPreview: React.FC<MissionPreviewProps> = ({ mission, onMissionCreate }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedMission, setEditedMission] = useState<Partial<Mission>>(mission);

  const createMissionMutation = useMutation({
    mutationFn: (data: CreateMissionRequest) => apiService.createMission(data),
    onSuccess: (response) => {
      onMissionCreate(response.data);
    },
  });

  const handleCreateMission = () => {
    if (!editedMission.search_area) return;

    const missionData: CreateMissionRequest = {
      name: editedMission.name || 'Unnamed Mission',
      description: editedMission.description || '',
      priority: editedMission.priority || MissionPriority.MEDIUM,
      search_area: {
        name: editedMission.search_area.name,
        type: editedMission.search_area.type,
        coordinates: editedMission.search_area.coordinates,
        center: editedMission.search_area.center,
        radius: editedMission.search_area.radius,
      },
      weather_requirements: editedMission.weather_conditions ? {
        max_wind_speed_kmh: 25,
        min_visibility_km: 5,
        no_precipitation: true,
      } : undefined,
      time_constraints: editedMission.time_constraints ? {
        max_duration_hours: editedMission.time_constraints.max_duration_hours,
        daylight_only: editedMission.time_constraints.daylight_only,
        start_time: editedMission.time_constraints.start_time,
        end_time: editedMission.time_constraints.end_time,
      } : undefined,
      drone_requirements: {
        min_count: editedMission.assigned_drones?.length || 1,
        preferred_types: ['quadcopter'],
        required_capabilities: ['camera', 'gps'],
      },
    };

    createMissionMutation.mutate(missionData);
  };

  const getPriorityColor = (priority: MissionPriority) => {
    const colors = {
      [MissionPriority.LOW]: 'text-green-700 bg-green-100',
      [MissionPriority.MEDIUM]: 'text-yellow-700 bg-yellow-100',
      [MissionPriority.HIGH]: 'text-orange-700 bg-orange-100',
      [MissionPriority.CRITICAL]: 'text-red-700 bg-red-100',
    };
    return colors[priority] || colors[MissionPriority.MEDIUM];
  };

  const validationIssues = [];
  if (!editedMission.name) validationIssues.push('Mission name is required');
  if (!editedMission.search_area) validationIssues.push('Search area must be defined');
  if (!editedMission.description) validationIssues.push('Mission description is recommended');

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-6 max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-1">Mission Preview</h2>
            <p className="text-gray-600">Review and finalize your mission parameters</p>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setIsEditing(!isEditing)}
              className="flex items-center space-x-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors"
            >
              {isEditing ? <X className="w-4 h-4" /> : <Edit className="w-4 h-4" />}
              <span>{isEditing ? 'Cancel' : 'Edit'}</span>
            </button>
            <button
              onClick={handleCreateMission}
              disabled={validationIssues.length > 0 || createMissionMutation.isPending}
              className="btn-primary flex items-center space-x-2 disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              <span>Create Mission</span>
            </button>
          </div>
        </div>

        {/* Validation Issues */}
        {validationIssues.length > 0 && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center space-x-2 mb-2">
              <AlertTriangle className="w-5 h-5 text-red-600" />
              <span className="font-medium text-red-900">Validation Issues</span>
            </div>
            <ul className="list-disc list-inside space-y-1 text-sm text-red-700">
              {validationIssues.map((issue, index) => (
                <li key={index}>{issue}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Basic Information */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Eye className="w-5 h-5 mr-2 text-primary-600" />
              Basic Information
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Mission Name
                </label>
                {isEditing ? (
                  <input
                    type="text"
                    value={editedMission.name || ''}
                    onChange={(e) => setEditedMission(prev => ({ ...prev, name: e.target.value }))}
                    className="input-field"
                    placeholder="Enter mission name"
                  />
                ) : (
                  <p className="text-gray-900">{editedMission.name || 'Unnamed Mission'}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                {isEditing ? (
                  <textarea
                    value={editedMission.description || ''}
                    onChange={(e) => setEditedMission(prev => ({ ...prev, description: e.target.value }))}
                    className="input-field"
                    rows={3}
                    placeholder="Enter mission description"
                  />
                ) : (
                  <p className="text-gray-900">{editedMission.description || 'No description provided'}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Priority
                </label>
                {isEditing ? (
                  <select
                    value={editedMission.priority || MissionPriority.MEDIUM}
                    onChange={(e) => setEditedMission(prev => ({ ...prev, priority: e.target.value as MissionPriority }))}
                    className="input-field"
                  >
                    <option value={MissionPriority.LOW}>Low</option>
                    <option value={MissionPriority.MEDIUM}>Medium</option>
                    <option value={MissionPriority.HIGH}>High</option>
                    <option value={MissionPriority.CRITICAL}>Critical</option>
                  </select>
                ) : (
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    getPriorityColor(editedMission.priority || MissionPriority.MEDIUM)
                  }`}>
                    {editedMission.priority || 'Medium'}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Search Area */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <MapPin className="w-5 h-5 mr-2 text-primary-600" />
              Search Area
            </h3>
            
            {editedMission.search_area ? (
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Type:</span>
                  <span className="text-sm font-medium capitalize">{editedMission.search_area.type}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Area:</span>
                  <span className="text-sm font-medium">{editedMission.search_area.area_km2?.toFixed(2)} km²</span>
                </div>
                {editedMission.search_area.center && (
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Center:</span>
                    <span className="text-sm font-medium">
                      {editedMission.search_area.center[0].toFixed(4)}, {editedMission.search_area.center[1].toFixed(4)}
                    </span>
                  </div>
                )}
                {editedMission.search_area.radius && (
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Radius:</span>
                    <span className="text-sm font-medium">{(editedMission.search_area.radius / 1000).toFixed(1)} km</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Terrain:</span>
                  <span className="text-sm font-medium capitalize">{editedMission.search_area.terrain_type || 'Unknown'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Difficulty:</span>
                  <span className="text-sm font-medium capitalize">{editedMission.search_area.difficulty_level || 'Medium'}</span>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <MapPin className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                <p>No search area defined</p>
              </div>
            )}
          </div>

          {/* Time Constraints */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Clock className="w-5 h-5 mr-2 text-primary-600" />
              Time Constraints
            </h3>
            
            {editedMission.time_constraints ? (
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Max Duration:</span>
                  <span className="text-sm font-medium">{editedMission.time_constraints.max_duration_hours} hours</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Daylight Only:</span>
                  <span className="text-sm font-medium">{editedMission.time_constraints.daylight_only ? 'Yes' : 'No'}</span>
                </div>
                {editedMission.time_constraints.start_time && (
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Start Time:</span>
                    <span className="text-sm font-medium">
                      {new Date(editedMission.time_constraints.start_time).toLocaleString()}
                    </span>
                  </div>
                )}
                {editedMission.time_constraints.end_time && (
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">End Time:</span>
                    <span className="text-sm font-medium">
                      {new Date(editedMission.time_constraints.end_time).toLocaleString()}
                    </span>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Clock className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                <p>No time constraints specified</p>
              </div>
            )}
          </div>

          {/* Drone Assignments */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Users className="w-5 h-5 mr-2 text-primary-600" />
              Drone Assignments
            </h3>
            
            {editedMission.assigned_drones && editedMission.assigned_drones.length > 0 ? (
              <div className="space-y-3">
                {editedMission.assigned_drones.map((assignment, index) => (
                  <div key={index} className="border border-gray-200 rounded p-3">
                    <div className="flex justify-between items-start">
                      <div>
                        <span className="font-medium">Drone {assignment.drone_id}</span>
                        <div className="text-sm text-gray-600 mt-1">
                          Role: <span className="capitalize">{assignment.role}</span>
                        </div>
                        {assignment.estimated_flight_time_minutes && (
                          <div className="text-sm text-gray-600">
                            Est. Flight Time: {assignment.estimated_flight_time_minutes} min
                          </div>
                        )}
                      </div>
                      <span className={`status-badge ${
                        assignment.status === 'assigned' ? 'status-active' : 'status-inactive'
                      }`}>
                        {assignment.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Users className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                <p>Drones will be assigned automatically</p>
              </div>
            )}
          </div>

          {/* Weather Conditions */}
          <div className="card lg:col-span-2">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Zap className="w-5 h-5 mr-2 text-primary-600" />
              Weather & Safety
            </h3>
            
            {editedMission.weather_conditions ? (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900">{editedMission.weather_conditions.temperature_c}°C</div>
                  <div className="text-sm text-gray-600">Temperature</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900">{editedMission.weather_conditions.wind_speed_kmh} km/h</div>
                  <div className="text-sm text-gray-600">Wind Speed</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900">{editedMission.weather_conditions.visibility_km} km</div>
                  <div className="text-sm text-gray-600">Visibility</div>
                </div>
                <div className="text-center">
                  <div className={`text-2xl font-bold ${editedMission.weather_conditions.is_suitable_for_flight ? 'text-green-600' : 'text-red-600'}`}>
                    {editedMission.weather_conditions.is_suitable_for_flight ? 'GO' : 'NO-GO'}
                  </div>
                  <div className="text-sm text-gray-600">Flight Status</div>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Zap className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                <p>Weather conditions will be checked before mission start</p>
              </div>
            )}
          </div>
        </div>

        {/* Mission Summary */}
        <div className="mt-6 card bg-primary-50 border-primary-200">
          <h3 className="text-lg font-semibold text-primary-900 mb-4 flex items-center">
            <CheckCircle className="w-5 h-5 mr-2" />
            Mission Summary
          </h3>
          <div className="text-sm text-primary-800">
            <p>
              This {editedMission.priority?.toLowerCase() || 'medium'} priority search and rescue mission will cover{' '}
              {editedMission.search_area?.area_km2?.toFixed(2) || 'an undefined'} km² using{' '}
              {editedMission.assigned_drones?.length || 'automatically assigned'} drones.
              {editedMission.time_constraints?.max_duration_hours && (
                <span> The mission is planned to run for a maximum of {editedMission.time_constraints.max_duration_hours} hours.</span>
              )}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MissionPreview;