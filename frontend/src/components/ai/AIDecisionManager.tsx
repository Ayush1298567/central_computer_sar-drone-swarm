/**
 * AI Decision Manager Component
 * Manages AI decisions, approvals, and real-time updates
 */

import React, { useState, useEffect, useCallback } from 'react';
import { 
  Brain, 
  CheckCircle, 
  XCircle, 
  Clock, 
  AlertTriangle, 
  TrendingUp,
  Activity,
  Zap,
  Shield,
  Target,
  Users,
  MapPin
} from 'lucide-react';

interface AIDecision {
  decision_id: string;
  decision_type: string;
  status: string;
  confidence_score: number;
  authority_level: string;
  human_approval_required: boolean;
  recommendation: string;
  reasoning_chain: string[];
  risk_assessment: {
    overall_risk_level: string;
    risk_factors: Record<string, any>;
    risk_score: number;
  };
  expected_impact: Record<string, any>;
  created_at: string;
  approved_at?: string;
  approved_by?: string;
  execution_result?: Record<string, any>;
}

interface ApprovalRequest {
  decision_id: string;
  decision_type: string;
  confidence_score: number;
  recommendation: string;
  reasoning: string[];
  risk_assessment: Record<string, any>;
  expected_impact: Record<string, any>;
  alternatives: any[];
  urgency_level: string;
  created_at: string;
  expires_at: string;
}

interface AIPerformanceMetrics {
  total_decisions: number;
  approved_decisions: number;
  executed_decisions: number;
  approval_rate: number;
  execution_rate: number;
  pending_decisions: number;
  pending_approvals: number;
}

interface AIDecisionManagerProps {
  className?: string;
  onDecisionUpdate?: (decision: AIDecision) => void;
}

const AIDecisionManager: React.FC<AIDecisionManagerProps> = ({
  className = '',
  onDecisionUpdate
}) => {
  const [activeTab, setActiveTab] = useState<'pending' | 'approvals' | 'history' | 'performance'>('pending');
  const [decisions, setDecisions] = useState<AIDecision[]>([]);
  const [approvalRequests, setApprovalRequests] = useState<ApprovalRequest[]>([]);
  const [performanceMetrics, setPerformanceMetrics] = useState<AIPerformanceMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedDecision, setSelectedDecision] = useState<AIDecision | null>(null);
  const [showDecisionDetails, setShowDecisionDetails] = useState(false);

  // WebSocket connection for real-time updates
  const [wsConnection, setWsConnection] = useState<WebSocket | null>(null);

  useEffect(() => {
    loadInitialData();
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
      handleWebSocketMessage(message);
    };
    
    ws.onclose = () => {
      console.log('AI decision WebSocket disconnected');
      // Attempt to reconnect after 5 seconds
      setTimeout(setupWebSocket, 5000);
    };
    
    ws.onerror = (error) => {
      console.error('AI decision WebSocket error:', error);
    };
    
    setWsConnection(ws);
  }, []);

  const handleWebSocketMessage = useCallback((message: any) => {
    switch (message.type) {
      case 'ai_decision':
        setDecisions(prev => [message.decision, ...prev]);
        break;
      case 'approval_request':
        setApprovalRequests(prev => [message.request, ...prev]);
        break;
      case 'decision_update':
        setDecisions(prev => 
          prev.map(d => d.decision_id === message.decision.decision_id ? message.decision : d)
        );
        break;
    }
  }, []);

  const loadInitialData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const [decisionsRes, approvalsRes, metricsRes] = await Promise.all([
        fetch('/api/v1/ai-decisions/pending'),
        fetch('/api/v1/ai-decisions/approval-requests'),
        fetch('/api/v1/ai-decisions/performance')
      ]);

      if (decisionsRes.ok) {
        const decisionsData = await decisionsRes.json();
        setDecisions(decisionsData.decisions || []);
      }

      if (approvalsRes.ok) {
        const approvalsData = await approvalsRes.json();
        setApprovalRequests(approvalsData.approval_requests || []);
      }

      if (metricsRes.ok) {
        const metricsData = await metricsRes.json();
        setPerformanceMetrics(metricsData.metrics);
      }

    } catch (err) {
      setError('Failed to load AI decision data');
      console.error('Error loading data:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleApproveDecision = useCallback(async (decisionId: string, approval: boolean, overrideReason?: string) => {
    try {
      const response = await fetch(`/api/v1/ai-decisions/${decisionId}/approve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          approval,
          override_reason: overrideReason
        })
      });

      if (response.ok) {
        // Remove from pending lists
        setDecisions(prev => prev.filter(d => d.decision_id !== decisionId));
        setApprovalRequests(prev => prev.filter(r => r.decision_id !== decisionId));
        
        // Reload data to get updated state
        loadInitialData();
      } else {
        throw new Error('Failed to approve decision');
      }
    } catch (err) {
      setError('Failed to approve decision');
      console.error('Error approving decision:', err);
    }
  }, [loadInitialData]);

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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'text-yellow-600 bg-yellow-100';
      case 'approved':
        return 'text-green-600 bg-green-100';
      case 'rejected':
        return 'text-red-600 bg-red-100';
      case 'executing':
        return 'text-blue-600 bg-blue-100';
      case 'completed':
        return 'text-green-600 bg-green-100';
      case 'failed':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
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

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const DecisionCard: React.FC<{ decision: AIDecision }> = ({ decision }) => (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-2">
          {getDecisionIcon(decision.decision_type)}
          <h3 className="font-semibold text-gray-900 capitalize">
            {decision.decision_type.replace('_', ' ')}
          </h3>
        </div>
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(decision.status)}`}>
          {decision.status}
        </span>
      </div>

      <p className="text-gray-700 text-sm mb-3">{decision.recommendation}</p>

      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-1">
            <Activity className="w-4 h-4 text-gray-400" />
            <span className={`font-medium ${getConfidenceColor(decision.confidence_score)}`}>
              {Math.round(decision.confidence_score * 100)}%
            </span>
          </div>
          <div className="flex items-center space-x-1">
            <Shield className="w-4 h-4 text-gray-400" />
            <span className={`px-2 py-1 rounded text-xs ${getRiskColor(decision.risk_assessment.overall_risk_level)}`}>
              {decision.risk_assessment.overall_risk_level}
            </span>
          </div>
        </div>
        <button
          onClick={() => {
            setSelectedDecision(decision);
            setShowDecisionDetails(true);
          }}
          className="text-blue-600 hover:text-blue-800 text-sm font-medium"
        >
          View Details
        </button>
      </div>

      {decision.human_approval_required && decision.status === 'pending' && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <div className="flex space-x-2">
            <button
              onClick={() => handleApproveDecision(decision.decision_id, true)}
              className="flex-1 bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded text-sm font-medium flex items-center justify-center space-x-1"
            >
              <CheckCircle className="w-4 h-4" />
              <span>Approve</span>
            </button>
            <button
              onClick={() => handleApproveDecision(decision.decision_id, false)}
              className="flex-1 bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded text-sm font-medium flex items-center justify-center space-x-1"
            >
              <XCircle className="w-4 h-4" />
              <span>Reject</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );

  const ApprovalRequestCard: React.FC<{ request: ApprovalRequest }> = ({ request }) => (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-2">
          <Clock className="w-5 h-5 text-orange-500" />
          <h3 className="font-semibold text-gray-900 capitalize">
            {request.decision_type.replace('_', ' ')} - Approval Required
          </h3>
        </div>
        <span className="text-xs text-gray-500">
          Expires: {formatTimestamp(request.expires_at)}
        </span>
      </div>

      <p className="text-gray-700 text-sm mb-3">{request.recommendation}</p>

      <div className="flex items-center justify-between text-sm mb-3">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-1">
            <Activity className="w-4 h-4 text-gray-400" />
            <span className={`font-medium ${getConfidenceColor(request.confidence_score)}`}>
              {Math.round(request.confidence_score * 100)}%
            </span>
          </div>
          <div className="flex items-center space-x-1">
            <Zap className="w-4 h-4 text-gray-400" />
            <span className="text-gray-600 capitalize">{request.urgency_level}</span>
          </div>
        </div>
      </div>

      <div className="mt-3 pt-3 border-t border-gray-200">
        <div className="flex space-x-2">
          <button
            onClick={() => handleApproveDecision(request.decision_id, true)}
            className="flex-1 bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded text-sm font-medium flex items-center justify-center space-x-1"
          >
            <CheckCircle className="w-4 h-4" />
            <span>Approve</span>
          </button>
          <button
            onClick={() => handleApproveDecision(request.decision_id, false)}
            className="flex-1 bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded text-sm font-medium flex items-center justify-center space-x-1"
          >
            <XCircle className="w-4 h-4" />
            <span>Reject</span>
          </button>
        </div>
      </div>
    </div>
  );

  const DecisionDetailsModal: React.FC<{ decision: AIDecision; onClose: () => void }> = ({ decision, onClose }) => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
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

          <div className="space-y-4">
            <div>
              <h3 className="font-medium text-gray-900 mb-2">Recommendation</h3>
              <p className="text-gray-700">{decision.recommendation}</p>
            </div>

            <div>
              <h3 className="font-medium text-gray-900 mb-2">Reasoning Chain</h3>
              <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
                {decision.reasoning_chain.map((reason, index) => (
                  <li key={index}>{reason}</li>
                ))}
              </ul>
            </div>

            <div>
              <h3 className="font-medium text-gray-900 mb-2">Risk Assessment</h3>
              <div className="bg-gray-50 rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-600">Overall Risk Level</span>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getRiskColor(decision.risk_assessment.overall_risk_level)}`}>
                    {decision.risk_assessment.overall_risk_level.toUpperCase()}
                  </span>
                </div>
                <div className="text-sm text-gray-600">
                  Risk Score: {Math.round(decision.risk_assessment.risk_score * 100)}%
                </div>
              </div>
            </div>

            <div>
              <h3 className="font-medium text-gray-900 mb-2">Expected Impact</h3>
              <div className="bg-gray-50 rounded-lg p-3">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  {Object.entries(decision.expected_impact).map(([key, value]) => (
                    <div key={key}>
                      <span className="text-gray-600 capitalize">{key.replace('_', ' ')}:</span>
                      <span className="ml-2 font-medium">{typeof value === 'number' ? value.toFixed(2) : String(value)}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {decision.execution_result && (
              <div>
                <h3 className="font-medium text-gray-900 mb-2">Execution Result</h3>
                <div className="bg-gray-50 rounded-lg p-3">
                  <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                    {JSON.stringify(decision.execution_result, null, 2)}
                  </pre>
                </div>
              </div>
            )}
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
            <Brain className="w-8 h-8 text-blue-600" />
            <div>
              <h1 className="text-xl font-semibold text-gray-900">AI Decision Manager</h1>
              <p className="text-sm text-gray-600">Manage AI decisions and approvals</p>
            </div>
          </div>
          <button
            onClick={loadInitialData}
            disabled={isLoading}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg text-sm font-medium"
          >
            {isLoading ? 'Loading...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8 px-6">
          {[
            { id: 'pending', label: 'Pending Decisions', count: decisions.length },
            { id: 'approvals', label: 'Approval Requests', count: approvalRequests.length },
            { id: 'history', label: 'History', count: 0 },
            { id: 'performance', label: 'Performance', count: 0 }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
              {tab.count > 0 && (
                <span className="ml-2 bg-gray-100 text-gray-600 py-1 px-2 rounded-full text-xs">
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      <div className="p-6">
        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
            {error}
          </div>
        )}

        {activeTab === 'pending' && (
          <div className="space-y-4">
            {decisions.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Brain className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No pending decisions</p>
              </div>
            ) : (
              decisions.map((decision) => (
                <DecisionCard key={decision.decision_id} decision={decision} />
              ))
            )}
          </div>
        )}

        {activeTab === 'approvals' && (
          <div className="space-y-4">
            {approvalRequests.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Clock className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No pending approval requests</p>
              </div>
            ) : (
              approvalRequests.map((request) => (
                <ApprovalRequestCard key={request.decision_id} request={request} />
              ))
            )}
          </div>
        )}

        {activeTab === 'performance' && performanceMetrics && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-2">
                <TrendingUp className="w-5 h-5 text-blue-600" />
                <span className="text-sm font-medium text-gray-600">Total Decisions</span>
              </div>
              <p className="text-2xl font-bold text-gray-900">{performanceMetrics.total_decisions}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-2">
                <CheckCircle className="w-5 h-5 text-green-600" />
                <span className="text-sm font-medium text-gray-600">Approval Rate</span>
              </div>
              <p className="text-2xl font-bold text-gray-900">
                {Math.round(performanceMetrics.approval_rate * 100)}%
              </p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-2">
                <Activity className="w-5 h-5 text-blue-600" />
                <span className="text-sm font-medium text-gray-600">Execution Rate</span>
              </div>
              <p className="text-2xl font-bold text-gray-900">
                {Math.round(performanceMetrics.execution_rate * 100)}%
              </p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-2">
                <Clock className="w-5 h-5 text-orange-600" />
                <span className="text-sm font-medium text-gray-600">Pending</span>
              </div>
              <p className="text-2xl font-bold text-gray-900">{performanceMetrics.pending_decisions}</p>
            </div>
          </div>
        )}
      </div>

      {/* Decision Details Modal */}
      {showDecisionDetails && selectedDecision && (
        <DecisionDetailsModal
          decision={selectedDecision}
          onClose={() => {
            setShowDecisionDetails(false);
            setSelectedDecision(null);
          }}
        />
      )}
    </div>
  );
};

export default AIDecisionManager;