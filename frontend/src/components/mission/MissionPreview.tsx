/**
 * Mission Preview Component for SAR Mission Commander.
 * Displays visual mission plan with drone assignments, timeline, and coverage areas.
 */

import React, { useState, useEffect } from 'react';
import {
  MapPin,
  Clock,
  Users,
  Target,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Play,
  Pause,
  RotateCcw,
  Download,
  Share2,
  Eye,
  EyeOff,
} from 'lucide-react';

// Import types
import {
  Mission,
  MissionPlan,
  DroneAssignment,
  WeatherImpact,
  RiskAssessment,
  MissionProgress,
  Coordinate,
} from '../../types';

// Import components
import InteractiveMap from '../map/InteractiveMap';

interface MissionPreviewProps {
  mission?: Mission;
  missionPlan?: MissionPlan;
  missionProgress?: MissionProgress;
  drones?: any[];
  onApprove?: () => void;
  onModify?: () => void;
  onStart?: () => void;
  onExport?: () => void;
  className?: string;
}

export const MissionPreview: React.FC<MissionPreviewProps> = ({
  mission,
  missionPlan,
  missionProgress,
  drones = [],
  onApprove,
  onModify,
  onStart,
  onExport,
  className = '',
}) => {
  const [showDetails, setShowDetails] = useState(true);
  const [selectedDrone, setSelectedDrone] = useState<string | null>(null);

  // Calculate mission metrics
  const missionMetrics = React.useMemo(() => {
    if (!mission || !missionPlan) return null;

    const totalArea = missionPlan.estimated_coverage || 0;
    const droneCount = missionPlan.drone_assignments?.length || 0;
    const estimatedDuration = MissionService.calculateEstimatedDuration(totalArea, droneCount);

    return {
      totalArea,
      droneCount,
      estimatedDuration,
      coveragePercentage: missionPlan.estimated_coverage > 0 ? 100 : 0,
      riskLevel: missionPlan.risk_assessment?.overall_risk || 'medium',
    };
  }, [mission, missionPlan]);

  // Handle drone selection
  const handleDroneSelect = (drone: any) => {
    setSelectedDrone(drone.id === selectedDrone ? null : drone.id);
  };

  // Weather impact display
  const WeatherImpactDisplay: React.FC<{ impact: WeatherImpact }> = ({ impact }) => (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
      <div className="flex items-center mb-2">
        <Target className="w-5 h-5 text-blue-600 mr-2" />
        <h4 className="font-semibold text-blue-800">Weather Impact</h4>
        <span className={`ml-auto px-2 py-1 text-xs rounded ${
          impact.safety_score >= 80 ? 'bg-green-100 text-green-700' :
          impact.safety_score >= 60 ? 'bg-yellow-100 text-yellow-700' :
          'bg-red-100 text-red-700'
        }`}>
          {impact.safety_score >= 80 ? 'Good' : impact.safety_score >= 60 ? 'Fair' : 'Poor'}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <p className="text-blue-700 font-medium">Conditions</p>
          <p className="text-blue-600">{impact.conditions.condition}</p>
          <p className="text-blue-600">{impact.conditions.temperature}°C, {impact.conditions.wind_speed} m/s wind</p>
        </div>
        <div>
          <p className="text-blue-700 font-medium">Restrictions</p>
          {impact.flight_restrictions.length > 0 ? (
            <ul className="text-blue-600 list-disc list-inside">
              {impact.flight_restrictions.slice(0, 2).map((restriction, index) => (
                <li key={index}>{restriction}</li>
              ))}
            </ul>
          ) : (
            <p className="text-green-600">No restrictions</p>
          )}
        </div>
      </div>
    </div>
  );

  // Risk assessment display
  const RiskAssessmentDisplay: React.FC<{ assessment: RiskAssessment }> = ({ assessment }) => (
    <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
      <div className="flex items-center mb-2">
        <AlertTriangle className="w-5 h-5 text-orange-600 mr-2" />
        <h4 className="font-semibold text-orange-800">Risk Assessment</h4>
        <span className={`ml-auto px-2 py-1 text-xs rounded ${
          assessment.overall_risk === 'low' ? 'bg-green-100 text-green-700' :
          assessment.overall_risk === 'medium' ? 'bg-yellow-100 text-yellow-700' :
          assessment.overall_risk === 'high' ? 'bg-orange-100 text-orange-700' :
          'bg-red-100 text-red-700'
        }`}>
          {assessment.overall_risk.toUpperCase()}
        </span>
      </div>

      <div className="space-y-2">
        {assessment.risk_factors.slice(0, 3).map((factor, index) => (
          <div key={index} className="flex items-center justify-between text-sm">
            <span className="text-orange-700">{factor.type}</span>
            <span className={`px-2 py-1 text-xs rounded ${
              factor.severity === 'low' ? 'bg-green-100 text-green-700' :
              factor.severity === 'medium' ? 'bg-yellow-100 text-yellow-700' :
              factor.severity === 'high' ? 'bg-orange-100 text-orange-700' :
              'bg-red-100 text-red-700'
            }`}>
              {factor.severity}
            </span>
          </div>
        ))}
      </div>
    </div>
  );

  // Drone assignment display
  const DroneAssignmentDisplay: React.FC<{ assignments: DroneAssignment[] }> = ({ assignments }) => (
    <div className="space-y-3">
      {assignments.map((assignment, index) => (
        <div
          key={assignment.id}
          className={`p-3 border rounded-lg cursor-pointer transition-colors ${
            selectedDrone === assignment.drone_id
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-200 hover:border-gray-300'
          }`}
          onClick={() => handleDroneSelect({ id: assignment.drone_id })}
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center">
              <div className={`w-3 h-3 rounded-full mr-2 ${
                assignment.status === 'completed' ? 'bg-green-500' :
                assignment.status === 'active' ? 'bg-blue-500' :
                'bg-gray-400'
              }`} />
              <span className="font-medium">Drone {assignment.drone_id}</span>
            </div>
            <span className="text-sm text-gray-500">
              {assignment.progress_percentage.toFixed(0)}%
            </span>
          </div>

          <div className="text-sm text-gray-600">
            <p>Area: {assignment.assigned_area ? 'Defined' : 'Pending'}</p>
            <p>Estimated time: {assignment.estimated_coverage_time} minutes</p>
            <p>Priority: {assignment.priority_level}</p>
          </div>
        </div>
      ))}
    </div>
  );

  // Timeline display
  const TimelineDisplay: React.FC = () => {
    if (!missionMetrics) return null;

    const phases = [
      { name: 'Planning', duration: 5, completed: true },
      { name: 'Launch', duration: 10, completed: missionProgress?.phase !== 'initializing' },
      { name: 'Search', duration: missionMetrics.estimatedDuration - 15, completed: false },
      { name: 'Return', duration: 5, completed: false },
    ];

    return (
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="font-semibold text-gray-800 mb-3 flex items-center">
          <Clock className="w-5 h-5 mr-2" />
          Mission Timeline
        </h4>

        <div className="space-y-2">
          {phases.map((phase, index) => (
            <div key={index} className="flex items-center">
              <div className={`w-4 h-4 rounded-full mr-3 flex-shrink-0 ${
                phase.completed ? 'bg-green-500' : 'bg-gray-300'
              }`} />
              <div className="flex-1">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">{phase.name}</span>
                  <span className="text-xs text-gray-500">{phase.duration} min</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-3 pt-3 border-t border-gray-200">
          <div className="flex justify-between text-sm">
            <span className="font-medium">Total Duration:</span>
            <span>{missionMetrics.estimatedDuration} minutes</span>
          </div>
        </div>
      </div>
    );
  };

  // Mission summary stats
  const MissionSummaryStats: React.FC = () => {
    if (!missionMetrics) return null;

    const stats = [
      {
        icon: Target,
        label: 'Coverage Area',
        value: `${missionMetrics.totalArea.toFixed(1)} km²`,
        color: 'text-green-600',
      },
      {
        icon: Users,
        label: 'Drones',
        value: missionMetrics.droneCount.toString(),
        color: 'text-blue-600',
      },
      {
        icon: Clock,
        label: 'Duration',
        value: `${missionMetrics.estimatedDuration} min`,
        color: 'text-purple-600',
      },
      {
        icon: CheckCircle,
        label: 'Coverage',
        value: `${missionMetrics.coveragePercentage.toFixed(0)}%`,
        color: 'text-orange-600',
      },
    ];

    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, index) => (
          <div key={index} className="bg-white border rounded-lg p-4 text-center">
            <stat.icon className={`w-8 h-8 mx-auto mb-2 ${stat.color}`} />
            <div className="text-2xl font-bold text-gray-800">{stat.value}</div>
            <div className="text-sm text-gray-600">{stat.label}</div>
          </div>
        ))}
      </div>
    );
  };

  if (!mission || !missionPlan) {
    return (
      <div className={`bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-8 text-center ${className}`}>
        <MapPin className="w-12 h-12 mx-auto mb-4 text-gray-400" />
        <h3 className="text-lg font-medium text-gray-600 mb-2">No Mission Plan Available</h3>
        <p className="text-gray-500">Complete your mission planning to see the preview here.</p>
      </div>
    );
  }

  return (
    <div className={`bg-white border rounded-lg shadow-sm ${className}`}>
      {/* Header */}
      <div className="p-4 border-b bg-gray-50 rounded-t-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <Eye className="w-5 h-5 mr-2 text-blue-500" />
            <h3 className="font-semibold text-gray-800">Mission Preview</h3>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="p-1 text-gray-500 hover:text-gray-700"
              title={showDetails ? 'Hide details' : 'Show details'}
            >
              {showDetails ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
            {onExport && (
              <button
                onClick={onExport}
                className="p-1 text-gray-500 hover:text-gray-700"
                title="Export mission plan"
              >
                <Download className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Mission Status */}
        <div className="mt-2 flex items-center space-x-4 text-sm">
          <span className="text-gray-600">Status:</span>
          <span className={`px-2 py-1 rounded text-xs font-medium ${
            mission.status === 'ready' ? 'bg-green-100 text-green-700' :
            mission.status === 'active' ? 'bg-blue-100 text-blue-700' :
            'bg-gray-100 text-gray-700'
          }`}>
            {mission.status.toUpperCase()}
          </span>
          {mission.ai_confidence && (
            <>
              <span className="text-gray-600">AI Confidence:</span>
              <span className="font-medium">{Math.round(mission.ai_confidence * 100)}%</span>
            </>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Summary Stats */}
        <MissionSummaryStats />

        {/* Detailed View Toggle */}
        {showDetails && (
          <div className="mt-6 space-y-6">
            {/* Weather Impact */}
            {missionPlan.weather_impact && (
              <WeatherImpactDisplay impact={missionPlan.weather_impact} />
            )}

            {/* Risk Assessment */}
            {missionPlan.risk_assessment && (
              <RiskAssessmentDisplay assessment={missionPlan.risk_assessment} />
            )}

            {/* Map Preview */}
            <div>
              <h4 className="font-semibold text-gray-800 mb-3 flex items-center">
                <MapPin className="w-5 h-5 mr-2" />
                Mission Area
              </h4>
              <div className="h-64 border rounded-lg overflow-hidden">
                <InteractiveMap
                  mission={mission}
                  drones={drones}
                  selectedDrone={selectedDrone}
                  onDroneSelect={handleDroneSelect}
                  height="100%"
                  className="rounded-lg"
                />
              </div>
            </div>

            {/* Drone Assignments */}
            {missionPlan.drone_assignments && missionPlan.drone_assignments.length > 0 && (
              <div>
                <h4 className="font-semibold text-gray-800 mb-3 flex items-center">
                  <Users className="w-5 h-5 mr-2" />
                  Drone Assignments ({missionPlan.drone_assignments.length})
                </h4>
                <DroneAssignmentDisplay assignments={missionPlan.drone_assignments} />
              </div>
            )}

            {/* Timeline */}
            <TimelineDisplay />

            {/* Action Buttons */}
            <div className="flex items-center justify-between pt-4 border-t">
              <div className="flex space-x-2">
                {onModify && (
                  <button
                    onClick={onModify}
                    className="px-4 py-2 text-sm border border-gray-300 text-gray-700 rounded hover:bg-gray-50 flex items-center"
                  >
                    <RotateCcw className="w-4 h-4 mr-2" />
                    Modify Plan
                  </button>
                )}
                {onExport && (
                  <button
                    onClick={onExport}
                    className="px-4 py-2 text-sm border border-gray-300 text-gray-700 rounded hover:bg-gray-50 flex items-center"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Export
                  </button>
                )}
              </div>

              <div className="flex space-x-2">
                {onApprove && (
                  <button
                    onClick={onApprove}
                    className="px-4 py-2 text-sm bg-green-600 text-white rounded hover:bg-green-700 flex items-center"
                  >
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Approve Plan
                  </button>
                )}
                {onStart && (
                  <button
                    onClick={onStart}
                    className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center"
                  >
                    <Play className="w-4 h-4 mr-2" />
                    Start Mission
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Mission preview utilities
export class MissionPreviewUtils {
  /**
   * Generate a visual summary of the mission plan
   */
  static generateMissionSummary(mission: Mission, missionPlan: MissionPlan): string {
    const summary = [
      `Mission: ${mission.name}`,
      `Target: ${mission.search_target}`,
      `Area: ${missionPlan.estimated_coverage.toFixed(1)} km²`,
      `Drones: ${missionPlan.drone_assignments.length}`,
      `Duration: ${MissionService.calculateEstimatedDuration(
        missionPlan.estimated_coverage,
        missionPlan.drone_assignments.length
      )} minutes`,
      `Risk Level: ${missionPlan.risk_assessment.overall_risk}`,
    ];

    if (missionPlan.weather_impact) {
      summary.push(`Weather: ${missionPlan.weather_impact.conditions.condition} (${missionPlan.weather_impact.safety_score}% safe)`);
    }

    return summary.join('\n');
  }

  /**
   * Calculate optimal map bounds for mission preview
   */
  static calculateMapBounds(mission: Mission): L.LatLngBounds | null {
    if (!mission.search_area) return null;

    try {
      const coordinates = mission.search_area.coordinates[0];
      const lats = coordinates.map(coord => coord[1]);
      const lngs = coordinates.map(coord => coord[0]);

      const minLat = Math.min(...lats);
      const maxLat = Math.max(...lats);
      const minLng = Math.min(...lngs);
      const maxLng = Math.max(...lngs);

      return L.latLngBounds([
        [minLat, minLng],
        [maxLat, maxLng],
      ]);
    } catch (error) {
      console.error('Error calculating map bounds:', error);
      return null;
    }
  }

  /**
   * Validate mission plan completeness
   */
  static validateMissionPlan(mission: Mission, missionPlan: MissionPlan): {
    isValid: boolean;
    issues: string[];
  } {
    const issues: string[] = [];

    if (!mission.name) issues.push('Mission name is required');
    if (!mission.search_target) issues.push('Search target is required');
    if (!mission.search_area) issues.push('Search area is required');
    if (!mission.launch_point) issues.push('Launch point is required');

    if (!missionPlan.drone_assignments || missionPlan.drone_assignments.length === 0) {
      issues.push('No drone assignments defined');
    }

    if (missionPlan.estimated_coverage <= 0) {
      issues.push('Invalid coverage area');
    }

    if (missionPlan.risk_assessment.overall_risk === 'critical') {
      issues.push('Mission has critical risk level');
    }

    return {
      isValid: issues.length === 0,
      issues,
    };
  }
}

// Import required dependencies
import L from 'leaflet';
import { MissionService } from '../../services';

export default MissionPreview;