/**
 * AI Decision Management Page
 * Main page for managing AI decisions and approvals
 */

import React, { useState } from 'react';
import { Brain, Activity, CheckCircle, AlertTriangle, BarChart3 } from 'lucide-react';
import AIDecisionDashboard from '../components/ai/AIDecisionDashboard';
import AIDecisionManager from '../components/ai/AIDecisionManager';
import AIDecisionApproval from '../components/ai/AIDecisionApproval';

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

const AIDecisionManagement: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'manager' | 'approvals'>('dashboard');
  const [selectedDecision, setSelectedDecision] = useState<AIDecision | null>(null);

  const handleDecisionSelect = (decision: AIDecision) => {
    setSelectedDecision(decision);
    setActiveTab('manager');
  };

  const handleDecisionApproved = (decisionId: string, approved: boolean) => {
    console.log(`Decision ${decisionId} ${approved ? 'approved' : 'rejected'}`);
    // You could add toast notifications or other feedback here
  };

  const tabs = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: BarChart3,
      description: 'Real-time AI decision monitoring'
    },
    {
      id: 'manager',
      label: 'Decision Manager',
      icon: Brain,
      description: 'Manage and track AI decisions'
    },
    {
      id: 'approvals',
      label: 'Approvals',
      icon: CheckCircle,
      description: 'Review and approve AI decisions'
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <Brain className="w-8 h-8 text-blue-600" />
              <div>
                <h1 className="text-xl font-semibold text-gray-900">AI Decision Management</h1>
                <p className="text-sm text-gray-600">Intelligent decision making and approval workflow</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span>AI System Online</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'dashboard' && (
          <AIDecisionDashboard
            onDecisionSelect={handleDecisionSelect}
            className="mb-8"
          />
        )}

        {activeTab === 'manager' && (
          <AIDecisionManager
            onDecisionUpdate={(decision) => {
              console.log('Decision updated:', decision);
            }}
            className="mb-8"
          />
        )}

        {activeTab === 'approvals' && (
          <AIDecisionApproval
            onDecisionApproved={handleDecisionApproved}
            className="mb-8"
          />
        )}
      </div>

      {/* Quick Stats Footer */}
      <div className="bg-white border-t border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">24/7</div>
              <div className="text-sm text-gray-600">AI Monitoring</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">99.9%</div>
              <div className="text-sm text-gray-600">Uptime</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">&lt;100ms</div>
              <div className="text-sm text-gray-600">Response Time</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">Real-time</div>
              <div className="text-sm text-gray-600">Decision Updates</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIDecisionManagement;