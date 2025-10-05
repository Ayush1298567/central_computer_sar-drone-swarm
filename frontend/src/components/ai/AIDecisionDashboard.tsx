/**
 * AI Decision Dashboard Component
 * Real-time dashboard for AI decision monitoring and management
 */

import React, { useState, useEffect, useCallback } from 'react';
import { 
  Brain, 
  Activity, 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  Zap,
  Shield,
  Target,
  Users,
  MapPin,
  BarChart3,
  RefreshCw
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

interface AIPerformanceMetrics {
  total_decisions: number;
  approved_decisions: number;
  executed_decisions: number;
  approval_rate: number;
  execution_rate: number;
  pending_decisions: number;
  pending_approvals: number;
}

interface AIDecisionDashboardProps {
  className?: string;
  onDecisionSelect?: (decision: AIDecision) => void;
}

const AIDecisionDashboard: React.FC<AIDecisionDashboardProps> = ({
  className = '',
  onDecisionSelect
}) => {
  const [decisions, setDecisions] = useState<AIDecision[]>([]);
  const [performanceMetrics, setPerformanceMetrics] = useState<AIPerformanceMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedTimeRange, setSelectedTimeRange] = useState<'1h' | '24h' | '7d' | '30d'>('24h');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(5000); // 5 seconds

  // WebSocket connection for real-time updates
  const [wsConnection, setWsConnection] = useState<WebSocket | null>(null);

  useEffect(() => {
    loadData();
    if (autoRefresh) {
      setupWebSocket();
    }
    
    return () => {
      if (wsConnection) {
        wsConnection.close();
      }
    };
  }, [autoRefresh, selectedTimeRange]);

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
      if (autoRefresh) {
        setTimeout(setupWebSocket, 5000);
      }
    };
    
    ws.onerror = (error) => {
      console.error('AI decision WebSocket error:', error);
    };
    
    setWsConnection(ws);
  }, [autoRefresh]);

  const handleWebSocketMessage = useCallback((message: any) => {
    switch (message.type) {
      case 'ai_decision':
        setDecisions(prev => [message.decision, ...prev.slice(0, 49)]); // Keep last 50
        break;
      case 'decision_update':
        setDecisions(prev => 
          prev.map(d => d.decision_id === message.decision.decision_id ? message.decision : d)
        );
        break;
    }
  }, []);

  const loadData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const [decisionsRes, metricsRes] = await Promise.all([
        fetch('/api/v1/ai-decisions/pending'),
        fetch('/api/v1/ai-decisions/performance')
      ]);

      if (decisionsRes.ok) {
        const decisionsData = await decisionsRes.json();
        setDecisions(decisionsData.decisions || []);
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

  const getDecisionIcon = (decisionType: string) => {
    switch (decisionType) {
      case 'mission_planning':
        return <Target className="w-4 h-4" />;
      case 'search_pattern':
        return <MapPin className="w-4 h-4" />;
      case 'drone_deployment':
        return <Users className="w-4 h-4" />;
      case 'emergency_response':
        return <AlertTriangle className="w-4 h-4" />;
      default:
        return <Brain className="w-4 h-4" />;
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
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return date.toLocaleDateString();
  };

  const getDecisionTypeStats = () => {
    const stats: Record<string, number> = {};
    decisions.forEach(decision => {
      stats[decision.decision_type] = (stats[decision.decision_type] || 0) + 1;
    });
    return stats;
  };

  const getStatusStats = () => {
    const stats: Record<string, number> = {};
    decisions.forEach(decision => {
      stats[decision.status] = (stats[decision.status] || 0) + 1;
    });
    return stats;
  };

  return (
    <div className={`bg-white rounded-lg shadow ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Brain className="w-8 h-8 text-blue-600" />
            <div>
              <h1 className="text-xl font-semibold text-gray-900">AI Decision Dashboard</h1>
              <p className="text-sm text-gray-600">Real-time AI decision monitoring</p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <select
              value={selectedTimeRange}
              onChange={(e) => setSelectedTimeRange(e.target.value as any)}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="1h">Last Hour</option>
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
            </select>
            <button
              onClick={loadData}
              disabled={isLoading}
              className="p-2 text-gray-400 hover:text-gray-600 disabled:opacity-50"
            >
              <RefreshCw className={`w-5 h-5 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
            <label className="flex items-center space-x-2 text-sm">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="rounded"
              />
              <span>Auto-refresh</span>
            </label>
          </div>
        </div>
      </div>

      {/* Performance Metrics */}
      {performanceMetrics && (
        <div className="p-6 border-b border-gray-200">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg p-4 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-blue-100 text-sm">Total Decisions</p>
                  <p className="text-2xl font-bold">{performanceMetrics.total_decisions}</p>
                </div>
                <BarChart3 className="w-8 h-8 text-blue-200" />
              </div>
            </div>
            <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-lg p-4 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-green-100 text-sm">Approval Rate</p>
                  <p className="text-2xl font-bold">{Math.round(performanceMetrics.approval_rate * 100)}%</p>
                </div>
                <CheckCircle className="w-8 h-8 text-green-200" />
              </div>
            </div>
            <div className="bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg p-4 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-purple-100 text-sm">Execution Rate</p>
                  <p className="text-2xl font-bold">{Math.round(performanceMetrics.execution_rate * 100)}%</p>
                </div>
                <Activity className="w-8 h-8 text-purple-200" />
              </div>
            </div>
            <div className="bg-gradient-to-r from-orange-500 to-orange-600 rounded-lg p-4 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-orange-100 text-sm">Pending</p>
                  <p className="text-2xl font-bold">{performanceMetrics.pending_decisions}</p>
                </div>
                <Clock className="w-8 h-8 text-orange-200" />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Charts and Stats */}
      <div className="p-6 border-b border-gray-200">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Decision Types Chart */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Decision Types</h3>
            <div className="space-y-3">
              {Object.entries(getDecisionTypeStats()).map(([type, count]) => (
                <div key={type} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {getDecisionIcon(type)}
                    <span className="text-sm font-medium text-gray-700 capitalize">
                      {type.replace('_', ' ')}
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-20 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full" 
                        style={{ width: `${(count / decisions.length) * 100}%` }}
                      ></div>
                    </div>
                    <span className="text-sm font-medium text-gray-900">{count}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Status Distribution */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Status Distribution</h3>
            <div className="space-y-3">
              {Object.entries(getStatusStats()).map(([status, count]) => (
                <div key={status} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className={`w-3 h-3 rounded-full ${getStatusColor(status).split(' ')[1]}`}></span>
                    <span className="text-sm font-medium text-gray-700 capitalize">{status}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-20 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full" 
                        style={{ width: `${(count / decisions.length) * 100}%` }}
                      ></div>
                    </div>
                    <span className="text-sm font-medium text-gray-900">{count}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Recent Decisions */}
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Recent Decisions</h3>
          <span className="text-sm text-gray-500">{decisions.length} decisions</span>
        </div>

        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
            {error}
          </div>
        )}

        {decisions.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Brain className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No recent decisions</p>
          </div>
        ) : (
          <div className="space-y-3">
            {decisions.slice(0, 10).map((decision) => (
              <div
                key={decision.decision_id}
                className="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors cursor-pointer"
                onClick={() => onDecisionSelect?.(decision)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    {getDecisionIcon(decision.decision_type)}
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        <h4 className="font-medium text-gray-900 capitalize">
                          {decision.decision_type.replace('_', ' ')}
                        </h4>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(decision.status)}`}>
                          {decision.status}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">{decision.recommendation}</p>
                      <div className="flex items-center space-x-4 text-xs text-gray-500">
                        <div className="flex items-center space-x-1">
                          <Activity className="w-3 h-3" />
                          <span className={`font-medium ${getConfidenceColor(decision.confidence_score)}`}>
                            {Math.round(decision.confidence_score * 100)}%
                          </span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <Shield className="w-3 h-3" />
                          <span className={`px-2 py-1 rounded text-xs ${getRiskColor(decision.risk_assessment.overall_risk_level)}`}>
                            {decision.risk_assessment.overall_risk_level}
                          </span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <Clock className="w-3 h-3" />
                          <span>{formatTimestamp(decision.created_at)}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  {decision.human_approval_required && decision.status === 'pending' && (
                    <div className="flex items-center space-x-1 text-orange-600">
                      <AlertTriangle className="w-4 h-4" />
                      <span className="text-xs font-medium">Approval Required</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AIDecisionDashboard;