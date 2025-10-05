/**
 * AI Decision Approval Component
 * Handles approval workflow for AI decisions requiring human oversight
 */

import React, { useState, useEffect, useCallback } from 'react';
import { 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  Clock, 
  Brain, 
  Activity,
  Shield,
  Target,
  Users,
  MapPin,
  BarChart3,
  Zap,
  Info,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

interface ApprovalRequest {
  decision_id: string;
  decision_type: string;
  confidence_score: number;
  recommendation: string;
  reasoning: string[];
  risk_assessment: {
    overall_risk_level: string;
    risk_factors: Record<string, any>;
    risk_score: number;
  };
  expected_impact: Record<string, any>;
  alternatives: Array<{
    option_id: string;
    description: string;
    parameters: Record<string, any>;
    expected_outcomes: Record<string, number>;
    risk_factors: string[];
    resource_requirements: Record<string, any>;
    confidence_score: number;
    reasoning: string;
  }>;
  urgency_level: string;
  created_at: string;
  expires_at: string;
}

interface AIDecisionApprovalProps {
  className?: string;
  onDecisionApproved?: (decisionId: string, approved: boolean) => void;
}

const AIDecisionApproval: React.FC<AIDecisionApprovalProps> = ({
  className = '',
  onDecisionApproved
}) => {
  const [approvalRequests, setApprovalRequests] = useState<ApprovalRequest[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedRequest, setSelectedRequest] = useState<ApprovalRequest | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const [approvalReason, setApprovalReason] = useState('');
  const [rejectionReason, setRejectionReason] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  // WebSocket connection for real-time updates
  const [wsConnection, setWsConnection] = useState<WebSocket | null>(null);

  useEffect(() => {
    loadApprovalRequests();
    setupWebSocket();
    
    return () => {
      if (wsConnection) {
        wsConnection.close();
      }
    };
  }, []);

  const setupWebSocket = useCallback(() => {
    const ws = new WebSocket('ws://localhost:8000/api/v1/ai-decisions/ws');
    
    ws.onopen = () => {
      console.log('Connected to AI decision WebSocket');
      ws.send(JSON.stringify({ type: 'subscribe' }));
    };
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'approval_request') {
        setApprovalRequests(prev => [message.request, ...prev]);
      }
    };
    
    ws.onclose = () => {
      console.log('AI decision WebSocket disconnected');
      setTimeout(setupWebSocket, 5000);
    };
    
    ws.onerror = (error) => {
      console.error('AI decision WebSocket error:', error);
    };
    
    setWsConnection(ws);
  }, []);

  const loadApprovalRequests = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch('/api/v1/ai-decisions/approval-requests');
      
      if (response.ok) {
        const data = await response.json();
        setApprovalRequests(data.approval_requests || []);
      } else {
        throw new Error('Failed to load approval requests');
      }

    } catch (err) {
      setError('Failed to load approval requests');
      console.error('Error loading approval requests:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleApproveDecision = useCallback(async (decisionId: string, approved: boolean) => {
    try {
      setIsProcessing(true);
      setError(null);

      const response = await fetch(`/api/v1/ai-decisions/${decisionId}/approve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          approval: approved,
          override_reason: approved ? approvalReason : rejectionReason
        })
      });

      if (response.ok) {
        // Remove from pending requests
        setApprovalRequests(prev => prev.filter(r => r.decision_id !== decisionId));
        
        // Reset form
        setApprovalReason('');
        setRejectionReason('');
        setShowDetails(false);
        setSelectedRequest(null);
        
        // Notify parent
        onDecisionApproved?.(decisionId, approved);
        
        // Reload to get updated data
        loadApprovalRequests();
      } else {
        throw new Error('Failed to approve decision');
      }
    } catch (err) {
      setError('Failed to approve decision');
      console.error('Error approving decision:', err);
    } finally {
      setIsProcessing(false);
    }
  }, [approvalReason, rejectionReason, onDecisionApproved, loadApprovalRequests]);

  const getDecisionIcon = (decisionType: string) => {
    switch (decisionType) {
      case 'mission_planning':
        return <Target className="w-5 h-5" />;
      case 'search_pattern':
        return <MapPin className="w-5 h-5" />;
      case 'drone_deployment':
        return <Users className="w-5 h-5" />;
      case 'emergency_response':
        return <AlertTriangle className="w-5 h-5" />;
      default:
        return <Brain className="w-5 h-5" />;
    }
  };

  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 bg-green-100';
    if (score >= 0.6) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low':
        return 'text-green-600 bg-green-100';
      case 'medium':
        return 'text-yellow-600 bg-yellow-100';
      case 'high':
        return 'text-red-600 bg-red-100';
      case 'critical':
        return 'text-red-800 bg-red-200';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getUrgencyColor = (level: string) => {
    switch (level) {
      case 'low':
        return 'text-green-600 bg-green-100';
      case 'medium':
        return 'text-yellow-600 bg-yellow-100';
      case 'high':
        return 'text-orange-600 bg-orange-100';
      case 'critical':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const getTimeUntilExpiry = (expiresAt: string) => {
    const now = new Date();
    const expiry = new Date(expiresAt);
    const diffMs = expiry.getTime() - now.getTime();
    
    if (diffMs <= 0) return 'Expired';
    
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    
    if (diffHours > 0) return `${diffHours}h ${diffMins % 60}m`;
    return `${diffMins}m`;
  };

  const ApprovalRequestCard: React.FC<{ request: ApprovalRequest }> = ({ request }) => {
    const isExpired = new Date(request.expires_at) < new Date();
    const timeUntilExpiry = getTimeUntilExpiry(request.expires_at);

    return (
      <div className={`bg-white border rounded-lg p-4 hover:shadow-md transition-shadow ${
        isExpired ? 'border-red-200 bg-red-50' : 'border-gray-200'
      }`}>
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center space-x-2">
            {getDecisionIcon(request.decision_type)}
            <h3 className="font-semibold text-gray-900 capitalize">
              {request.decision_type.replace('_', ' ')}
            </h3>
          </div>
          <div className="flex items-center space-x-2">
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getUrgencyColor(request.urgency_level)}`}>
              {request.urgency_level.toUpperCase()}
            </span>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
              isExpired ? 'text-red-600 bg-red-100' : 'text-gray-600 bg-gray-100'
            }`}>
              {isExpired ? 'EXPIRED' : `Expires in ${timeUntilExpiry}`}
            </span>
          </div>
        </div>

        <p className="text-gray-700 text-sm mb-3">{request.recommendation}</p>

        <div className="flex items-center justify-between text-sm mb-3">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-1">
              <Activity className="w-4 h-4 text-gray-400" />
              <span className={`px-2 py-1 rounded text-xs font-medium ${getConfidenceColor(request.confidence_score)}`}>
                {Math.round(request.confidence_score * 100)}% confidence
              </span>
            </div>
            <div className="flex items-center space-x-1">
              <Shield className="w-4 h-4 text-gray-400" />
              <span className={`px-2 py-1 rounded text-xs ${getRiskColor(request.risk_assessment.overall_risk_level)}`}>
                {request.risk_assessment.overall_risk_level} risk
              </span>
            </div>
          </div>
          <button
            onClick={() => {
              setSelectedRequest(request);
              setShowDetails(true);
            }}
            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            {showDetails && selectedRequest?.decision_id === request.decision_id ? 'Hide Details' : 'View Details'}
          </button>
        </div>

        {!isExpired && (
          <div className="flex space-x-2">
            <button
              onClick={() => handleApproveDecision(request.decision_id, true)}
              disabled={isProcessing}
              className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white px-3 py-2 rounded text-sm font-medium flex items-center justify-center space-x-1"
            >
              <CheckCircle className="w-4 h-4" />
              <span>Approve</span>
            </button>
            <button
              onClick={() => handleApproveDecision(request.decision_id, false)}
              disabled={isProcessing}
              className="flex-1 bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white px-3 py-2 rounded text-sm font-medium flex items-center justify-center space-x-1"
            >
              <XCircle className="w-4 h-4" />
              <span>Reject</span>
            </button>
          </div>
        )}
      </div>
    );
  };

  const DecisionDetailsModal: React.FC<{ request: ApprovalRequest; onClose: () => void }> = ({ request, onClose }) => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Decision Details</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <XCircle className="w-6 h-6" />
            </button>
          </div>

          <div className="space-y-6">
            {/* Recommendation */}
            <div>
              <h3 className="font-medium text-gray-900 mb-2">AI Recommendation</h3>
              <p className="text-gray-700 bg-gray-50 rounded-lg p-3">{request.recommendation}</p>
            </div>

            {/* Reasoning Chain */}
            <div>
              <h3 className="font-medium text-gray-900 mb-2">AI Reasoning</h3>
              <div className="bg-gray-50 rounded-lg p-3">
                <ol className="list-decimal list-inside space-y-1 text-sm text-gray-700">
                  {request.reasoning.map((reason, index) => (
                    <li key={index}>{reason}</li>
                  ))}
                </ol>
              </div>
            </div>

            {/* Risk Assessment */}
            <div>
              <h3 className="font-medium text-gray-900 mb-2">Risk Assessment</h3>
              <div className="bg-gray-50 rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-600">Overall Risk Level</span>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getRiskColor(request.risk_assessment.overall_risk_level)}`}>
                    {request.risk_assessment.overall_risk_level.toUpperCase()}
                  </span>
                </div>
                <div className="text-sm text-gray-600">
                  Risk Score: {Math.round(request.risk_assessment.risk_score * 100)}%
                </div>
                {Object.keys(request.risk_assessment.risk_factors).length > 0 && (
                  <div className="mt-2">
                    <p className="text-sm font-medium text-gray-700 mb-1">Risk Factors:</p>
                    <div className="space-y-1">
                      {Object.entries(request.risk_assessment.risk_factors).map(([factor, details]) => (
                        <div key={factor} className="text-xs text-gray-600">
                          <span className="font-medium capitalize">{factor.replace('_', ' ')}:</span> {details.description || details}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Expected Impact */}
            <div>
              <h3 className="font-medium text-gray-900 mb-2">Expected Impact</h3>
              <div className="bg-gray-50 rounded-lg p-3">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  {Object.entries(request.expected_impact).map(([key, value]) => (
                    <div key={key}>
                      <span className="text-gray-600 capitalize">{key.replace('_', ' ')}:</span>
                      <span className="ml-2 font-medium">{typeof value === 'number' ? value.toFixed(2) : String(value)}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Alternative Options */}
            {request.alternatives.length > 0 && (
              <div>
                <h3 className="font-medium text-gray-900 mb-2">Alternative Options</h3>
                <div className="space-y-3">
                  {request.alternatives.map((alternative, index) => (
                    <div key={alternative.option_id} className="bg-gray-50 rounded-lg p-3">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium text-gray-900">Option {index + 1}</h4>
                        <span className={`px-2 py-1 rounded text-xs font-medium ${getConfidenceColor(alternative.confidence_score)}`}>
                          {Math.round(alternative.confidence_score * 100)}% confidence
                        </span>
                      </div>
                      <p className="text-sm text-gray-700 mb-2">{alternative.description}</p>
                      <div className="text-xs text-gray-600">
                        <div className="grid grid-cols-2 gap-2">
                          <div>
                            <span className="font-medium">Success Rate:</span> {Math.round(alternative.expected_outcomes.success_rate * 100)}%
                          </div>
                          <div>
                            <span className="font-medium">Resource Cost:</span> {alternative.resource_requirements.cost || 'N/A'}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Approval Form */}
            <div className="border-t pt-6">
              <h3 className="font-medium text-gray-900 mb-4">Your Decision</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Reason for Approval (Optional)
                  </label>
                  <textarea
                    value={approvalReason}
                    onChange={(e) => setApprovalReason(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows={3}
                    placeholder="Explain why you're approving this decision..."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Reason for Rejection (Optional)
                  </label>
                  <textarea
                    value={rejectionReason}
                    onChange={(e) => setRejectionReason(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows={3}
                    placeholder="Explain why you're rejecting this decision..."
                  />
                </div>
                <div className="flex space-x-3">
                  <button
                    onClick={() => handleApproveDecision(request.decision_id, true)}
                    disabled={isProcessing}
                    className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg font-medium flex items-center justify-center space-x-2"
                  >
                    <CheckCircle className="w-4 h-4" />
                    <span>Approve Decision</span>
                  </button>
                  <button
                    onClick={() => handleApproveDecision(request.decision_id, false)}
                    disabled={isProcessing}
                    className="flex-1 bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg font-medium flex items-center justify-center space-x-2"
                  >
                    <XCircle className="w-4 h-4" />
                    <span>Reject Decision</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className={`bg-white rounded-lg shadow ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <AlertTriangle className="w-8 h-8 text-orange-600" />
            <div>
              <h1 className="text-xl font-semibold text-gray-900">AI Decision Approval</h1>
              <p className="text-sm text-gray-600">Review and approve AI decisions requiring human oversight</p>
            </div>
          </div>
          <button
            onClick={loadApprovalRequests}
            disabled={isLoading}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg text-sm font-medium"
          >
            {isLoading ? 'Loading...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
            {error}
          </div>
        )}

        {approvalRequests.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <CheckCircle className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No pending approval requests</p>
            <p className="text-sm">All AI decisions are currently autonomous</p>
          </div>
        ) : (
          <div className="space-y-4">
            {approvalRequests.map((request) => (
              <ApprovalRequestCard key={request.decision_id} request={request} />
            ))}
          </div>
        )}
      </div>

      {/* Decision Details Modal */}
      {showDetails && selectedRequest && (
        <DecisionDetailsModal
          request={selectedRequest}
          onClose={() => {
            setShowDetails(false);
            setSelectedRequest(null);
            setApprovalReason('');
            setRejectionReason('');
          }}
        />
      )}
    </div>
  );
};

export default AIDecisionApproval;