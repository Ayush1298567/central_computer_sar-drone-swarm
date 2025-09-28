/**
 * Investigation Panel Component
 * Tools for investigating and analyzing discoveries
 */

import React, { useState, useEffect } from 'react';
import { Discovery, Evidence } from '../../types';

interface InvestigationPanelProps {
  discovery: Discovery | null;
  evidence: Evidence[];
  onStatusUpdate?: (discoveryId: string, status: Discovery['status'], notes?: string) => void;
  onEvidenceAnalyze?: (evidenceId: string) => void;
  onCreateReport?: (discoveryId: string, reportData: any) => void;
  className?: string;
}

export const InvestigationPanel: React.FC<InvestigationPanelProps> = ({
  discovery,
  evidence,
  onStatusUpdate,
  onEvidenceAnalyze,
  onCreateReport,
  className = ''
}) => {
  const [investigationNotes, setInvestigationNotes] = useState('');
  const [analysisMode, setAnalysisMode] = useState<'manual' | 'automated'>('manual');
  const [selectedEvidence, setSelectedEvidence] = useState<string[]>([]);
  const [investigationStatus, setInvestigationStatus] = useState<Discovery['status']>('new');
  const [reportData, setReportData] = useState({
    title: '',
    summary: '',
    findings: '',
    recommendations: '',
    priority: 'medium' as Discovery['priority']
  });

  // Initialize with discovery data
  useEffect(() => {
    if (discovery) {
      setInvestigationStatus(discovery.status);
      setReportData(prev => ({
        ...prev,
        priority: discovery.priority
      }));
    }
  }, [discovery]);

  const handleStatusUpdate = (newStatus: Discovery['status']) => {
    setInvestigationStatus(newStatus);
    if (discovery) {
      onStatusUpdate?.(discovery.id, newStatus, investigationNotes);
    }
  };

  const handleEvidenceSelection = (evidenceId: string) => {
    setSelectedEvidence(prev =>
      prev.includes(evidenceId)
        ? prev.filter(id => id !== evidenceId)
        : [...prev, evidenceId]
    );
  };

  const handleAnalyzeSelected = () => {
    selectedEvidence.forEach(evidenceId => {
      onEvidenceAnalyze?.(evidenceId);
    });
  };

  const handleCreateReport = () => {
    if (!discovery) return;

    onCreateReport?.(discovery.id, {
      ...reportData,
      discoveryId: discovery.id,
      timestamp: new Date(),
      evidenceIds: selectedEvidence,
      notes: investigationNotes
    });

    // Reset form
    setReportData({
      title: '',
      summary: '',
      findings: '',
      recommendations: '',
      priority: 'medium'
    });
    setInvestigationNotes('');
  };

  const getStatusColor = (status: string): string => {
    const colors = {
      new: 'bg-green-100 text-green-800 border-green-200',
      investigating: 'bg-blue-100 text-blue-800 border-blue-200',
      confirmed: 'bg-purple-100 text-purple-800 border-purple-200',
      false_positive: 'bg-gray-100 text-gray-800 border-gray-200'
    };
    return colors[status as keyof typeof colors] || colors.new;
  };

  const getPriorityIcon = (priority: string): string => {
    const icons = {
      critical: '🚨',
      high: '⚠️',
      medium: 'ℹ️',
      low: '📍'
    };
    return icons[priority as keyof typeof icons] || icons.medium;
  };

  if (!discovery) {
    return (
      <div className={`flex items-center justify-center h-64 bg-gray-50 rounded-lg ${className}`}>
        <div className="text-center text-gray-500">
          <div className="text-4xl mb-2">🔍</div>
          <div className="text-sm">Select a discovery to investigate</div>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Discovery header */}
      <div className="bg-white border rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold">Investigation Panel</h3>
          <div className={`px-3 py-1 text-sm rounded-full border ${getStatusColor(investigationStatus)}`}>
            {investigationStatus.replace('_', ' ').toUpperCase()}
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-gray-600">Type:</span>
            <div className="font-medium capitalize">{discovery.type}</div>
          </div>
          <div>
            <span className="text-gray-600">Priority:</span>
            <div className="font-medium flex items-center">
              <span className="mr-1">{getPriorityIcon(discovery.priority)}</span>
              {discovery.priority}
            </div>
          </div>
          <div>
            <span className="text-gray-600">Confidence:</span>
            <div className="font-medium">{Math.round(discovery.confidence * 100)}%</div>
          </div>
          <div>
            <span className="text-gray-600">Timestamp:</span>
            <div className="font-medium">{discovery.timestamp.toLocaleString()}</div>
          </div>
        </div>

        {discovery.description && (
          <div className="mt-3">
            <span className="text-gray-600 text-sm">Description:</span>
            <div className="text-sm mt-1">{discovery.description}</div>
          </div>
        )}
      </div>

      {/* Investigation controls */}
      <div className="bg-white border rounded-lg p-4">
        <h4 className="font-medium mb-3">Investigation Status</h4>
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Update Status
            </label>
            <select
              value={investigationStatus}
              onChange={(e) => handleStatusUpdate(e.target.value as Discovery['status'])}
              className="w-full border rounded-lg px-3 py-2 text-sm"
            >
              <option value="new">New</option>
              <option value="investigating">Investigating</option>
              <option value="confirmed">Confirmed</option>
              <option value="false_positive">False Positive</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Investigation Notes
            </label>
            <textarea
              value={investigationNotes}
              onChange={(e) => setInvestigationNotes(e.target.value)}
              placeholder="Add investigation notes, observations, or findings..."
              className="w-full border rounded-lg px-3 py-2 text-sm h-24 resize-none"
            />
          </div>
        </div>
      </div>

      {/* Evidence analysis */}
      {evidence.length > 0 && (
        <div className="bg-white border rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-medium">Evidence Analysis</h4>
            <div className="flex space-x-2">
              <button
                onClick={() => setAnalysisMode(analysisMode === 'manual' ? 'automated' : 'manual')}
                className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded"
              >
                {analysisMode === 'manual' ? 'Auto' : 'Manual'}
              </button>
              {selectedEvidence.length > 0 && (
                <button
                  onClick={handleAnalyzeSelected}
                  className="px-3 py-1 text-xs bg-blue-600 text-white hover:bg-blue-700 rounded"
                >
                  Analyze Selected ({selectedEvidence.length})
                </button>
              )}
            </div>
          </div>

          <div className="space-y-2 max-h-48 overflow-y-auto">
            {evidence.map((item) => (
              <div
                key={item.id}
                className={`flex items-center space-x-3 p-2 border rounded cursor-pointer hover:bg-gray-50 ${
                  selectedEvidence.includes(item.id) ? 'border-blue-500 bg-blue-50' : ''
                }`}
                onClick={() => handleEvidenceSelection(item.id)}
              >
                <input
                  type="checkbox"
                  checked={selectedEvidence.includes(item.id)}
                  onChange={() => handleEvidenceSelection(item.id)}
                  className="rounded"
                />
                <div className="flex-1 text-sm">
                  <div className="font-medium capitalize">{item.type}</div>
                  <div className="text-gray-600">
                    {item.metadata?.fileSize && `${Math.round(item.metadata.fileSize / 1024)}KB`}
                    {item.metadata?.duration && ` • ${Math.floor(item.metadata.duration)}s`}
                  </div>
                </div>
                <div className="text-xs text-gray-500">
                  {item.timestamp.toLocaleTimeString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Investigation report */}
      <div className="bg-white border rounded-lg p-4">
        <h4 className="font-medium mb-3">Investigation Report</h4>
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Report Title
            </label>
            <input
              type="text"
              value={reportData.title}
              onChange={(e) => setReportData(prev => ({ ...prev, title: e.target.value }))}
              placeholder="Investigation report title..."
              className="w-full border rounded-lg px-3 py-2 text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Summary
            </label>
            <textarea
              value={reportData.summary}
              onChange={(e) => setReportData(prev => ({ ...prev, summary: e.target.value }))}
              placeholder="Brief summary of the investigation..."
              className="w-full border rounded-lg px-3 py-2 text-sm h-20 resize-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Findings
            </label>
            <textarea
              value={reportData.findings}
              onChange={(e) => setReportData(prev => ({ ...prev, findings: e.target.value }))}
              placeholder="Detailed findings from the investigation..."
              className="w-full border rounded-lg px-3 py-2 text-sm h-24 resize-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Recommendations
            </label>
            <textarea
              value={reportData.recommendations}
              onChange={(e) => setReportData(prev => ({ ...prev, recommendations: e.target.value }))}
              placeholder="Recommended actions or next steps..."
              className="w-full border rounded-lg px-3 py-2 text-sm h-20 resize-none"
            />
          </div>

          <div className="flex justify-end">
            <button
              onClick={handleCreateReport}
              disabled={!reportData.title.trim()}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400"
            >
              Create Report
            </button>
          </div>
        </div>
      </div>

      {/* Quick actions */}
      <div className="bg-white border rounded-lg p-4">
        <h4 className="font-medium mb-3">Quick Actions</h4>
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => handleStatusUpdate('investigating')}
            className="px-3 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Start Investigation
          </button>
          <button
            onClick={() => handleStatusUpdate('confirmed')}
            className="px-3 py-2 text-sm bg-green-600 text-white rounded hover:bg-green-700"
          >
            Mark Confirmed
          </button>
          <button
            onClick={() => handleStatusUpdate('false_positive')}
            className="px-3 py-2 text-sm bg-gray-600 text-white rounded hover:bg-gray-700"
          >
            Mark False Positive
          </button>
          <button
            onClick={() => {
              // Export investigation data
              const data = {
                discovery,
                evidence: evidence.filter(e => selectedEvidence.includes(e.id)),
                notes: investigationNotes,
                timestamp: new Date()
              };
              const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = `investigation-${discovery.id}.json`;
              a.click();
              URL.revokeObjectURL(url);
            }}
            className="px-3 py-2 text-sm bg-purple-600 text-white rounded hover:bg-purple-700"
          >
            Export Data
          </button>
        </div>
      </div>
    </div>
  );
};