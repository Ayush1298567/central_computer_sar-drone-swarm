import React, { useState, useEffect } from 'react';
import { FileText, Download, Calendar, BarChart3, Users, Clock, MapPin, CheckCircle, Loader } from 'lucide-react';
import { Mission, Drone } from '../../types';
import { apiService } from '../../utils/api';

interface ReportGeneratorProps {
  missions: Mission[];
  drones: Drone[];
  onClose?: () => void;
}

interface ReportTemplate {
  id: string;
  name: string;
  description: string;
  sections: string[];
  format: 'pdf' | 'excel' | 'json';
}

const ReportGenerator: React.FC<ReportGeneratorProps> = ({ missions, drones, onClose }) => {
  const [selectedMissions, setSelectedMissions] = useState<string[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [dateRange, setDateRange] = useState({
    start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0],
  });
  const [includeCharts, setIncludeCharts] = useState(true);
  const [includeRawData, setIncludeRawData] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedReports, setGeneratedReports] = useState<any[]>([]);

  const reportTemplates: ReportTemplate[] = [
    {
      id: 'summary',
      name: 'Mission Summary Report',
      description: 'High-level overview of mission performance and key metrics',
      sections: ['Overview', 'Key Metrics', 'Performance Summary', 'Recommendations'],
      format: 'pdf',
    },
    {
      id: 'detailed',
      name: 'Detailed Mission Analysis',
      description: 'Comprehensive analysis with detailed breakdowns and trends',
      sections: ['Executive Summary', 'Mission Details', 'Performance Metrics', 'Timeline Analysis', 'Recommendations'],
      format: 'pdf',
    },
    {
      id: 'performance',
      name: 'Performance Analysis Report',
      description: 'Focus on system performance, efficiency, and optimization opportunities',
      sections: ['Performance Overview', 'Efficiency Metrics', 'Trend Analysis', 'Improvement Areas'],
      format: 'pdf',
    },
    {
      id: 'technical',
      name: 'Technical Report',
      description: 'Technical details, system logs, and raw data export',
      sections: ['System Overview', 'Technical Metrics', 'Raw Data', 'System Health'],
      format: 'excel',
    },
    {
      id: 'data_export',
      name: 'Data Export',
      description: 'Raw data export for external analysis',
      sections: ['Raw Mission Data', 'Telemetry Data', 'Analytics Data'],
      format: 'json',
    },
  ];

  const handleMissionToggle = (missionId: string) => {
    setSelectedMissions(prev =>
      prev.includes(missionId)
        ? prev.filter(id => id !== missionId)
        : [...prev, missionId]
    );
  };

  const handleSelectAllMissions = () => {
    const filteredMissions = getFilteredMissions();
    setSelectedMissions(filteredMissions.map(m => m.id));
  };

  const handleDeselectAllMissions = () => {
    setSelectedMissions([]);
  };

  const getFilteredMissions = () => {
    return missions.filter(mission => {
      const missionDate = new Date(mission.created_at);
      const startDate = new Date(dateRange.start);
      const endDate = new Date(dateRange.end);
      return missionDate >= startDate && missionDate <= endDate;
    });
  };

  const handleGenerateReport = async () => {
    if (!selectedTemplate || selectedMissions.length === 0) {
      alert('Please select a report template and at least one mission.');
      return;
    }

    setIsGenerating(true);

    try {
      const template = reportTemplates.find(t => t.id === selectedTemplate)!;

      for (const missionId of selectedMissions) {
        const result = await apiService.generateReport(missionId, selectedTemplate);

        // Simulate report generation
        await new Promise(resolve => setTimeout(resolve, 2000));

        setGeneratedReports(prev => [...prev, {
          id: `report-${Date.now()}-${missionId}`,
          missionId,
          template: template.name,
          format: template.format,
          generatedAt: new Date().toISOString(),
          downloadUrl: result.downloadUrl || '#',
          size: Math.floor(Math.random() * 5) + 1, // Mock size in MB
        }]);
      }
    } catch (error) {
      console.error('Failed to generate report:', error);
      alert('Failed to generate report. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  const downloadReport = (report: any) => {
    // In a real implementation, this would trigger the actual download
    const link = document.createElement('a');
    link.href = report.downloadUrl;
    link.download = `${report.template}_${report.missionId}.${report.format}`;
    link.click();
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const filteredMissions = getFilteredMissions();
  const selectedTemplateData = reportTemplates.find(t => t.id === selectedTemplate);

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <FileText className="h-6 w-6 text-green-600 mr-2" />
          <h2 className="text-xl font-bold text-gray-800">Report Generator</h2>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600"
          >
            ×
          </button>
        )}
      </div>

      {/* Configuration */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Mission Selection */}
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Select Missions</h3>

          {/* Date Range */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Date Range
            </label>
            <div className="flex space-x-2">
              <input
                type="date"
                value={dateRange.start}
                onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
                className="flex-1 p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              <input
                type="date"
                value={dateRange.end}
                onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
                className="flex-1 p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          {/* Mission List */}
          <div className="border border-gray-200 rounded-lg max-h-48 overflow-y-auto">
            <div className="p-3 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">
                {filteredMissions.length} missions found
              </span>
              <div className="flex space-x-2">
                <button
                  onClick={handleSelectAllMissions}
                  className="text-xs text-blue-600 hover:text-blue-800"
                >
                  Select All
                </button>
                <button
                  onClick={handleDeselectAllMissions}
                  className="text-xs text-gray-600 hover:text-gray-800"
                >
                  Deselect All
                </button>
              </div>
            </div>
            <div className="divide-y divide-gray-100">
              {filteredMissions.map(mission => (
                <label key={mission.id} className="flex items-center p-3 hover:bg-gray-50 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedMissions.includes(mission.id)}
                    onChange={() => handleMissionToggle(mission.id)}
                    className="mr-3"
                  />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-800">{mission.name}</p>
                    <p className="text-xs text-gray-500">
                      {new Date(mission.created_at).toLocaleDateString()} • {mission.status}
                    </p>
                  </div>
                </label>
              ))}
            </div>
          </div>
        </div>

        {/* Report Template Selection */}
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Report Template</h3>
          <div className="space-y-3">
            {reportTemplates.map(template => (
              <div
                key={template.id}
                className={`border rounded-lg p-3 cursor-pointer transition-colors ${
                  selectedTemplate === template.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:bg-gray-50'
                }`}
                onClick={() => setSelectedTemplate(template.id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-800">{template.name}</h4>
                    <p className="text-sm text-gray-600 mt-1">{template.description}</p>
                    <div className="flex items-center mt-2 space-x-4">
                      <span className="text-xs text-gray-500">Format: {template.format.toUpperCase()}</span>
                      <span className="text-xs text-gray-500">{template.sections.length} sections</span>
                    </div>
                  </div>
                  <div className={`w-4 h-4 rounded-full border-2 ${
                    selectedTemplate === template.id ? 'border-blue-500 bg-blue-500' : 'border-gray-300'
                  }`}>
                    {selectedTemplate === template.id && (
                      <div className="w-full h-full rounded-full bg-white scale-50" />
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Report Options */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-3">Report Options</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={includeCharts}
              onChange={(e) => setIncludeCharts(e.target.checked)}
              className="mr-2"
            />
            <span className="text-sm text-gray-700">Include charts and visualizations</span>
          </label>
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={includeRawData}
              onChange={(e) => setIncludeRawData(e.target.checked)}
              className="mr-2"
            />
            <span className="text-sm text-gray-700">Include raw data exports</span>
          </label>
        </div>
      </div>

      {/* Generate Button */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <p className="text-sm text-gray-600">
            Selected: {selectedMissions.length} missions • Template: {selectedTemplateData?.name || 'None'}
          </p>
        </div>
        <button
          onClick={handleGenerateReport}
          disabled={!selectedTemplate || selectedMissions.length === 0 || isGenerating}
          className="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white py-2 px-6 rounded-md font-medium flex items-center"
        >
          {isGenerating ? (
            <>
              <Loader className="h-4 w-4 mr-2 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <Download className="h-4 w-4 mr-2" />
              Generate Reports
            </>
          )}
        </button>
      </div>

      {/* Generated Reports */}
      {generatedReports.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Generated Reports</h3>
          <div className="space-y-3">
            {generatedReports.map(report => (
              <div key={report.id} className="border border-green-200 bg-green-50 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <CheckCircle className="h-5 w-5 text-green-600" />
                    <div>
                      <p className="font-medium text-gray-800">{report.template}</p>
                      <p className="text-sm text-gray-600">
                        Generated {formatDate(report.generatedAt)} • {formatFileSize(report.size * 1024 * 1024)}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => downloadReport(report)}
                    className="bg-green-600 hover:bg-green-700 text-white py-2 px-4 rounded-md text-sm font-medium flex items-center"
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Download
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Report Preview */}
      {selectedTemplateData && (
        <div className="mt-6 pt-6 border-t border-gray-200">
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Report Preview</h3>
          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="font-medium text-gray-800 mb-2">{selectedTemplateData.name}</h4>
            <p className="text-sm text-gray-600 mb-4">{selectedTemplateData.description}</p>

            <div className="space-y-2">
              <p className="text-sm font-medium text-gray-700">Report Sections:</p>
              <ul className="text-sm text-gray-600 space-y-1">
                {selectedTemplateData.sections.map((section, index) => (
                  <li key={index} className="flex items-center">
                    <div className="w-2 h-2 bg-blue-500 rounded-full mr-2" />
                    {section}
                  </li>
                ))}
              </ul>
            </div>

            <div className="mt-4 flex items-center space-x-4 text-xs text-gray-500">
              <span>Format: {selectedTemplateData.format.toUpperCase()}</span>
              <span>•</span>
              <span>Estimated size: ~{Math.floor(Math.random() * 10) + 1} MB</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReportGenerator;