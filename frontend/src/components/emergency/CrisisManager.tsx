import React, { useState, useEffect } from 'react';
import { AlertTriangle, Clock, MapPin, Users, Phone, CheckCircle, XCircle } from 'lucide-react';
import { EmergencySituation } from '../../types';
import { apiService } from '../../utils/api';

interface CrisisManagerProps {
  onEmergencyResponse: (situation: EmergencySituation, action: string) => void;
}

const CrisisManager: React.FC<CrisisManagerProps> = ({ onEmergencyResponse }) => {
  const [emergencies, setEmergencies] = useState<EmergencySituation[]>([]);
  const [selectedEmergency, setSelectedEmergency] = useState<EmergencySituation | null>(null);
  const [responseNotes, setResponseNotes] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadEmergencies();
    const interval = setInterval(loadEmergencies, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadEmergencies = async () => {
    try {
      const situations = await apiService.getEmergencySituations();
      setEmergencies(situations);
    } catch (error) {
      console.error('Failed to load emergencies:', error);
    }
  };

  const handleResolveEmergency = async (emergency: EmergencySituation) => {
    if (!responseNotes.trim()) {
      alert('Please provide resolution notes before resolving the emergency.');
      return;
    }

    setIsLoading(true);

    try {
      const result = await apiService.resolveEmergency(emergency.id, responseNotes);

      if (result.success) {
        onEmergencyResponse(emergency, 'resolved');
        setEmergencies(prev => prev.filter(e => e.id !== emergency.id));
        setSelectedEmergency(null);
        setResponseNotes('');
      }
    } catch (error) {
      console.error('Failed to resolve emergency:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleEscalateEmergency = (emergency: EmergencySituation) => {
    onEmergencyResponse(emergency, 'escalated');
    // Here you would typically call an external emergency service or notification system
    alert(`Emergency escalated to external services. Situation ID: ${emergency.id}`);
  };

  const handleContactEmergencyServices = (emergency: EmergencySituation) => {
    onEmergencyResponse(emergency, 'contacted_services');
    // Here you would integrate with actual emergency services
    alert(`Emergency services contacted for situation: ${emergency.description}`);
  };

  const getSeverityColor = (severity: EmergencySituation['severity']) => {
    switch (severity) {
      case 'critical': return 'border-red-500 bg-red-50';
      case 'high': return 'border-orange-500 bg-orange-50';
      case 'medium': return 'border-yellow-500 bg-yellow-50';
      case 'low': return 'border-blue-500 bg-blue-50';
      default: return 'border-gray-500 bg-gray-50';
    }
  };

  const getSeverityTextColor = (severity: EmergencySituation['severity']) => {
    switch (severity) {
      case 'critical': return 'text-red-800';
      case 'high': return 'text-orange-800';
      case 'medium': return 'text-yellow-800';
      case 'low': return 'text-blue-800';
      default: return 'text-gray-800';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const activeEmergencies = emergencies.filter(e => e.status === 'active');
  const resolvedEmergencies = emergencies.filter(e => e.status === 'resolved');

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <div className="flex items-center mb-4">
        <AlertTriangle className="h-6 w-6 text-red-600 mr-2" />
        <h2 className="text-xl font-bold text-gray-800">Crisis Management Center</h2>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-red-50 border border-red-200 rounded p-3 text-center">
          <div className="text-2xl font-bold text-red-600">{activeEmergencies.length}</div>
          <div className="text-sm text-red-700">Active</div>
        </div>
        <div className="bg-orange-50 border border-orange-200 rounded p-3 text-center">
          <div className="text-2xl font-bold text-orange-600">
            {activeEmergencies.filter(e => e.severity === 'critical' || e.severity === 'high').length}
          </div>
          <div className="text-sm text-orange-700">High Priority</div>
        </div>
        <div className="bg-green-50 border border-green-200 rounded p-3 text-center">
          <div className="text-2xl font-bold text-green-600">{resolvedEmergencies.length}</div>
          <div className="text-sm text-green-700">Resolved</div>
        </div>
        <div className="bg-blue-50 border border-blue-200 rounded p-3 text-center">
          <div className="text-2xl font-bold text-blue-600">{emergencies.length}</div>
          <div className="text-sm text-blue-700">Total</div>
        </div>
      </div>

      {/* Active Emergencies */}
      {activeEmergencies.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-red-700 mb-3 flex items-center">
            <AlertTriangle className="h-5 w-5 mr-2" />
            Active Emergency Situations
          </h3>
          <div className="space-y-3">
            {activeEmergencies.map(emergency => (
              <div
                key={emergency.id}
                className={`border rounded-lg p-4 cursor-pointer transition-colors ${getSeverityColor(emergency.severity)} ${
                  selectedEmergency?.id === emergency.id ? 'ring-2 ring-purple-500' : ''
                }`}
                onClick={() => setSelectedEmergency(emergency)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center mb-2">
                      <h4 className={`font-semibold ${getSeverityTextColor(emergency.severity)}`}>
                        {emergency.type.replace('_', ' ').toUpperCase()}
                      </h4>
                      <span className={`ml-2 px-2 py-1 rounded text-xs font-medium ${
                        emergency.severity === 'critical' ? 'bg-red-600 text-white' :
                        emergency.severity === 'high' ? 'bg-orange-600 text-white' :
                        emergency.severity === 'medium' ? 'bg-yellow-600 text-white' :
                        'bg-blue-600 text-white'
                      }`}>
                        {emergency.severity.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-gray-700 mb-2">{emergency.description}</p>
                    <div className="flex items-center text-sm text-gray-600 space-x-4">
                      <div className="flex items-center">
                        <Clock className="h-4 w-4 mr-1" />
                        {formatTimestamp(emergency.timestamp)}
                      </div>
                      <div className="flex items-center">
                        <Users className="h-4 w-4 mr-1" />
                        Affected: {emergency.affected_drones.join(', ')}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Emergency Response Panel */}
      {selectedEmergency && (
        <div className="border-t border-gray-200 pt-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Emergency Response</h3>

          <div className={`border rounded-lg p-4 mb-4 ${getSeverityColor(selectedEmergency.severity)}`}>
            <h4 className={`font-semibold mb-2 ${getSeverityTextColor(selectedEmergency.severity)}`}>
              {selectedEmergency.type.replace('_', ' ').toUpperCase()}
            </h4>
            <p className="text-gray-700 mb-3">{selectedEmergency.description}</p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <h5 className="font-medium text-gray-800 mb-2">Affected Drones</h5>
                <div className="space-y-1">
                  {selectedEmergency.affected_drones.map(droneId => (
                    <div key={droneId} className="text-sm text-gray-600 bg-white px-2 py-1 rounded border">
                      {droneId}
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <h5 className="font-medium text-gray-800 mb-2">Actions Taken</h5>
                <div className="space-y-1">
                  {selectedEmergency.actions_taken.map((action, index) => (
                    <div key={index} className="text-sm text-gray-600 bg-white px-2 py-1 rounded border">
                      {action}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Response Actions */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
              <button
                onClick={() => handleEscalateEmergency(selectedEmergency)}
                className="bg-orange-600 hover:bg-orange-700 text-white py-2 px-4 rounded-md font-medium flex items-center justify-center"
              >
                <AlertTriangle className="h-4 w-4 mr-2" />
                Escalate
              </button>
              <button
                onClick={() => handleContactEmergencyServices(selectedEmergency)}
                className="bg-red-600 hover:bg-red-700 text-white py-2 px-4 rounded-md font-medium flex items-center justify-center"
              >
                <Phone className="h-4 w-4 mr-2" />
                Contact Services
              </button>
              <button
                onClick={() => handleResolveEmergency(selectedEmergency)}
                disabled={isLoading}
                className="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white py-2 px-4 rounded-md font-medium flex items-center justify-center"
              >
                <CheckCircle className="h-4 w-4 mr-2" />
                {isLoading ? 'Resolving...' : 'Resolve'}
              </button>
            </div>

            {/* Resolution Notes */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Resolution Notes
              </label>
              <textarea
                value={responseNotes}
                onChange={(e) => setResponseNotes(e.target.value)}
                placeholder="Describe the actions taken and resolution details..."
                className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-green-500"
                rows={3}
              />
            </div>
          </div>
        </div>
      )}

      {/* Emergency Response Checklist */}
      <div className="border-t border-gray-200 pt-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Emergency Response Checklist</h3>
        <div className="space-y-3">
          {[
            { id: 'assess_situation', label: 'Assess the emergency situation', completed: activeEmergencies.length > 0 },
            { id: 'notify_team', label: 'Notify response team', completed: false },
            { id: 'activate_protocols', label: 'Activate emergency protocols', completed: false },
            { id: 'coordinate_response', label: 'Coordinate with external services', completed: false },
            { id: 'document_actions', label: 'Document all actions taken', completed: false },
          ].map(checklist => (
            <div key={checklist.id} className="flex items-center space-x-3">
              {checklist.completed ? (
                <CheckCircle className="h-5 w-5 text-green-600" />
              ) : (
                <div className="h-5 w-5 border-2 border-gray-300 rounded-full" />
              )}
              <span className={`text-sm ${checklist.completed ? 'text-green-800' : 'text-gray-700'}`}>
                {checklist.label}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* No Active Emergencies */}
      {activeEmergencies.length === 0 && (
        <div className="text-center py-8">
          <CheckCircle className="h-12 w-12 text-green-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-800 mb-2">All Systems Normal</h3>
          <p className="text-gray-600">No active emergency situations detected.</p>
        </div>
      )}
    </div>
  );
};

export default CrisisManager;
