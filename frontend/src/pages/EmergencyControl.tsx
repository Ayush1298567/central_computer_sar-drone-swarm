import React, { useState, useEffect } from 'react';
import { wsService } from '../services/websocket';

interface Emergency {
  id: string;
  type: string;
  level: string;
  reason: string;
  operator: string;
  timestamp: string;
  status: string;
  drone_ids: string[];
}

const EmergencyControl: React.FC = () => {
  const [activeEmergencies, setActiveEmergencies] = useState<Emergency[]>([]);
  const [emergencyHistory, setEmergencyHistory] = useState<Emergency[]>([]);
  const [selectedDrones, setSelectedDrones] = useState<string[]>([]);
  const [emergencyReason, setEmergencyReason] = useState('');
  const [isTriggering, setIsTriggering] = useState(false);

  useEffect(() => {
    // Listen for emergency updates
    const unsubEmergencies = wsService.on('emergency_updates', (data) => {
      if (data.status === 'active') {
        setActiveEmergencies(prev => {
          const updated = prev.filter(e => e.id !== data.id);
          return [data, ...updated];
        });
      } else if (data.status === 'resolved') {
        setActiveEmergencies(prev => prev.filter(e => e.id !== data.id));
        setEmergencyHistory(prev => [data, ...prev].slice(0, 50));
      }
    });

    // Request current emergency status
    wsService.send({
      type: 'get_emergency_status',
      payload: {}
    });

    return () => {
      unsubEmergencies();
    };
  }, []);

  const triggerEmergencyStop = async () => {
    if (!emergencyReason.trim()) {
      alert('Please provide a reason for the emergency stop');
      return;
    }

    if (window.confirm('Are you sure you want to trigger emergency stop? This will immediately halt all drone operations.')) {
      setIsTriggering(true);
      
      try {
        wsService.triggerEmergencyStop(emergencyReason);
        setEmergencyReason('');
      } catch (error) {
        console.error('Emergency stop failed:', error);
        alert('Failed to trigger emergency stop');
      } finally {
        setIsTriggering(false);
      }
    }
  };

  const resolveEmergency = (emergencyId: string) => {
    const resolution = prompt('Enter resolution details:');
    if (resolution) {
      wsService.send({
        type: 'resolve_emergency',
        payload: {
          emergency_id: emergencyId,
          resolution: resolution,
          operator: 'dashboard_user'
        }
      });
    }
  };

  const getEmergencyLevelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getEmergencyIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'emergency_stop':
        return '🛑';
      case 'low_battery':
        return '🔋';
      case 'communication_loss':
        return '📡';
      case 'weather_emergency':
        return '⛈️';
      case 'collision_risk':
        return '⚠️';
      case 'system_failure':
        return '🔧';
      default:
        return '🚨';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Emergency Control</h1>
          <p className="text-gray-600 mt-2">Emergency response and safety management</p>
        </div>

        {/* Emergency Stop Panel */}
        <div className="bg-white rounded-lg shadow mb-8">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">Emergency Stop</h2>
            <p className="text-gray-600 mt-1">Immediately halt all drone operations</p>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Reason for Emergency Stop
                </label>
                <textarea
                  value={emergencyReason}
                  onChange={(e) => setEmergencyReason(e.target.value)}
                  placeholder="Describe the reason for emergency stop..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                  rows={3}
                />
              </div>
              <button
                onClick={triggerEmergencyStop}
                disabled={isTriggering || !emergencyReason.trim()}
                className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium text-lg"
              >
                {isTriggering ? 'Triggering...' : '🚨 EMERGENCY STOP ALL DRONES'}
              </button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Active Emergencies */}
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-semibold text-gray-900">Active Emergencies</h2>
                <span className="px-2 py-1 bg-red-100 text-red-800 text-sm font-medium rounded-full">
                  {activeEmergencies.length} Active
                </span>
              </div>
            </div>
            <div className="p-6">
              {activeEmergencies.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <div className="text-4xl mb-4">✅</div>
                  <p>No active emergencies</p>
                  <p className="text-sm mt-2">All systems operating normally</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {activeEmergencies.map((emergency) => (
                    <div key={emergency.id} className={`p-4 border rounded-lg ${getEmergencyLevelColor(emergency.level)}`}>
                      <div className="flex items-start justify-between">
                        <div className="flex items-start space-x-3">
                          <span className="text-2xl">{getEmergencyIcon(emergency.type)}</span>
                          <div className="flex-1">
                            <div className="flex items-center space-x-2 mb-2">
                              <h3 className="font-semibold text-gray-900 capitalize">
                                {emergency.type.replace('_', ' ')}
                              </h3>
                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getEmergencyLevelColor(emergency.level)}`}>
                                {emergency.level}
                              </span>
                            </div>
                            <p className="text-sm text-gray-700 mb-2">{emergency.reason}</p>
                            <div className="text-xs text-gray-600 space-y-1">
                              <p>Operator: {emergency.operator}</p>
                              <p>Time: {new Date(emergency.timestamp).toLocaleString()}</p>
                              {emergency.drone_ids.length > 0 && (
                                <p>Drones: {emergency.drone_ids.join(', ')}</p>
                              )}
                            </div>
                          </div>
                        </div>
                        <button
                          onClick={() => resolveEmergency(emergency.id)}
                          className="px-3 py-1 bg-green-100 text-green-800 text-sm rounded hover:bg-green-200"
                        >
                          Resolve
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Emergency History */}
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">Emergency History</h2>
              <p className="text-gray-600 mt-1">Recent emergency events</p>
            </div>
            <div className="p-6">
              {emergencyHistory.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <div className="text-4xl mb-4">📋</div>
                  <p>No emergency history</p>
                  <p className="text-sm mt-2">Emergency events will appear here</p>
                </div>
              ) : (
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {emergencyHistory.map((emergency) => (
                    <div key={emergency.id} className="p-3 border border-gray-200 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <span className="text-lg">{getEmergencyIcon(emergency.type)}</span>
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-1">
                            <h4 className="font-medium text-gray-900 capitalize text-sm">
                              {emergency.type.replace('_', ' ')}
                            </h4>
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getEmergencyLevelColor(emergency.level)}`}>
                              {emergency.level}
                            </span>
                          </div>
                          <p className="text-xs text-gray-600">{emergency.reason}</p>
                          <p className="text-xs text-gray-500 mt-1">
                            {new Date(emergency.timestamp).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Emergency Procedures */}
        <div className="mt-8 bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">Emergency Procedures</h2>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="p-4 border border-gray-200 rounded-lg">
                <h3 className="font-semibold text-gray-900 mb-2">🚨 Emergency Stop</h3>
                <p className="text-sm text-gray-600 mb-3">
                  Immediately halt all drone operations and return to base
                </p>
                <ul className="text-xs text-gray-500 space-y-1">
                  <li>• All drones return to launch point</li>
                  <li>• Mission operations suspended</li>
                  <li>• Personnel notified immediately</li>
                </ul>
              </div>
              
              <div className="p-4 border border-gray-200 rounded-lg">
                <h3 className="font-semibold text-gray-900 mb-2">🔋 Low Battery</h3>
                <p className="text-sm text-gray-600 mb-3">
                  Automatic return to base when battery levels are critical
                </p>
                <ul className="text-xs text-gray-500 space-y-1">
                  <li>• Warning at 30% battery</li>
                  <li>• RTL initiated at 20%</li>
                  <li>• Emergency landing at 10%</li>
                </ul>
              </div>
              
              <div className="p-4 border border-gray-200 rounded-lg">
                <h3 className="font-semibold text-gray-900 mb-2">📡 Communication Loss</h3>
                <p className="text-sm text-gray-600 mb-3">
                  Automatic failsafe procedures when communication is lost
                </p>
                <ul className="text-xs text-gray-500 space-y-1">
                  <li>• Return to launch after 30s</li>
                  <li>• Land safely if RTL fails</li>
                  <li>• Alert ground team</li>
                </ul>
              </div>
              
              <div className="p-4 border border-gray-200 rounded-lg">
                <h3 className="font-semibold text-gray-900 mb-2">⛈️ Weather Emergency</h3>
                <p className="text-sm text-gray-600 mb-3">
                  Weather monitoring and automatic safety responses
                </p>
                <ul className="text-xs text-gray-500 space-y-1">
                  <li>• Monitor wind speed and visibility</li>
                  <li>• Automatic RTL in severe weather</li>
                  <li>• Mission suspension protocols</li>
                </ul>
              </div>
              
              <div className="p-4 border border-gray-200 rounded-lg">
                <h3 className="font-semibold text-gray-900 mb-2">⚠️ Collision Risk</h3>
                <p className="text-sm text-gray-600 mb-3">
                  Obstacle detection and avoidance systems
                </p>
                <ul className="text-xs text-gray-500 space-y-1">
                  <li>• Real-time obstacle detection</li>
                  <li>• Automatic evasive maneuvers</li>
                  <li>• Emergency stop if avoidance fails</li>
                </ul>
              </div>
              
              <div className="p-4 border border-gray-200 rounded-lg">
                <h3 className="font-semibold text-gray-900 mb-2">🔧 System Failure</h3>
                <p className="text-sm text-gray-600 mb-3">
                  Hardware and software failure responses
                </p>
                <ul className="text-xs text-gray-500 space-y-1">
                  <li>• Immediate RTL on critical failures</li>
                  <li>• Backup system activation</li>
                  <li>• Manual override available</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmergencyControl;