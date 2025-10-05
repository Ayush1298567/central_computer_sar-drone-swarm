import React, { useState } from 'react';
import { Discovery } from '../../types/api';
import { Investigation, InvestigationAction } from '../../types/discovery';

interface InvestigationPanelProps {
  discovery: Discovery;
  investigation?: Investigation;
  onInvestigationUpdate?: (investigation: Partial<Investigation>) => void;
  onActionAdd?: (action: Omit<InvestigationAction, 'id'>) => void;
  onActionComplete?: (actionId: string) => void;
  onEscalate?: (priority: Discovery['priority']) => void;
  availableInvestigators?: string[];
}

const InvestigationPanel: React.FC<InvestigationPanelProps> = ({
  discovery,
  investigation,
  onInvestigationUpdate,
  onActionAdd,
  onActionComplete,
  onEscalate,
  availableInvestigators = [],
}) => {
  const [newNote, setNewNote] = useState('');
  const [newAction, setNewAction] = useState({
    type: 'analysis' as InvestigationAction['type'],
    description: '',
  });

  const handleStatusChange = (status: Investigation['status']) => {
    onInvestigationUpdate?.({ status });
  };

  const handleInvestigatorAssign = (investigatorId: string) => {
    onInvestigationUpdate?.({
      assigned_investigator: investigatorId,
      status: investigatorId ? 'in_progress' : 'pending'
    });
  };

  const handleAddNote = () => {
    if (!newNote.trim()) return;

    const note = `${new Date().toLocaleString()}: ${newNote}`;
    const currentNotes = investigation?.notes || discovery.investigation_notes || '';
    const updatedNotes = currentNotes ? `${currentNotes}\n\n${note}` : note;

    onInvestigationUpdate?.({ notes: updatedNotes });
    setNewNote('');
  };

  const handleAddAction = () => {
    if (!newAction.description.trim()) return;

    onActionAdd?.({
      type: newAction.type,
      description: newAction.description,
      timestamp: Date.now(),
      completed: false,
    });

    setNewAction({ type: 'analysis', description: '' });
  };

  const handleCompleteAction = (actionId: string) => {
    onActionComplete?.(actionId);
  };

  const handleEscalate = () => {
    const priorityLevels: Discovery['priority'][] = ['low', 'medium', 'high', 'critical'];
    const currentIndex = priorityLevels.indexOf(discovery.priority);
    const nextPriority = priorityLevels[Math.min(currentIndex + 1, priorityLevels.length - 1)];

    if (nextPriority !== discovery.priority) {
      onEscalate?.(nextPriority);
    }
  };

  const getActionIcon = (type: InvestigationAction['type']) => {
    switch (type) {
      case 'analysis': return '🔍';
      case 'verification': return '✅';
      case 'coordination': return '🤝';
      case 'escalation': return '🚨';
      default: return '📝';
    }
  };

  const getPriorityColor = (priority: Discovery['priority']) => {
    switch (priority) {
      case 'critical': return 'text-red-400';
      case 'high': return 'text-orange-400';
      case 'medium': return 'text-yellow-400';
      case 'low': return 'text-green-400';
      default: return 'text-gray-400';
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-xl font-bold mb-2">Investigation Panel</h2>
          <div className="flex items-center gap-2">
            <span className="capitalize font-medium">{discovery.type} Discovery</span>
            <span className={`px-2 py-1 rounded text-sm ${getPriorityColor(discovery.priority)}`}>
              {discovery.priority}
            </span>
          </div>
        </div>

        <button
          onClick={handleEscalate}
          disabled={discovery.priority === 'critical'}
          className="px-3 py-1 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 rounded text-sm"
        >
          Escalate
        </button>
      </div>

      {/* Investigation Status */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-2">Investigation Status</label>
          <select
            value={investigation?.status || 'pending'}
            onChange={(e) => handleStatusChange(e.target.value as Investigation['status'])}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded"
          >
            <option value="pending">Pending</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="escalated">Escalated</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Assigned Investigator</label>
          <select
            value={investigation?.assigned_investigator || ''}
            onChange={(e) => handleInvestigatorAssign(e.target.value)}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded"
          >
            <option value="">Unassigned</option>
            {availableInvestigators.map(investigator => (
              <option key={investigator} value={investigator}>
                {investigator}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Investigation Notes */}
      <div>
        <label className="block text-sm font-medium mb-2">Investigation Notes</label>
        <textarea
          value={investigation?.notes || discovery.investigation_notes || ''}
          onChange={(e) => onInvestigationUpdate?.({ notes: e.target.value })}
          placeholder="Add investigation notes..."
          className="w-full h-32 px-3 py-2 bg-gray-700 border border-gray-600 rounded resize-none"
        />
      </div>

      {/* Quick Notes */}
      <div>
        <label className="block text-sm font-medium mb-2">Add Quick Note</label>
        <div className="flex gap-2">
          <textarea
            value={newNote}
            onChange={(e) => setNewNote(e.target.value)}
            placeholder="Add a quick note..."
            className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded resize-none"
            rows={2}
          />
          <button
            onClick={handleAddNote}
            disabled={!newNote.trim()}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded"
          >
            Add
          </button>
        </div>
      </div>

      {/* Investigation Actions */}
      <div>
        <h3 className="text-lg font-semibold mb-3">Investigation Actions</h3>

        {/* Add New Action */}
        <div className="mb-4 p-3 bg-gray-700 rounded">
          <div className="grid grid-cols-2 gap-2 mb-2">
            <select
              value={newAction.type}
              onChange={(e) => setNewAction(prev => ({ ...prev, type: e.target.value as InvestigationAction['type'] }))}
              className="px-2 py-1 bg-gray-600 border border-gray-500 rounded text-sm"
            >
              <option value="analysis">Analysis</option>
              <option value="verification">Verification</option>
              <option value="coordination">Coordination</option>
              <option value="escalation">Escalation</option>
            </select>

            <input
              type="text"
              value={newAction.description}
              onChange={(e) => setNewAction(prev => ({ ...prev, description: e.target.value }))}
              placeholder="Action description..."
              className="px-2 py-1 bg-gray-600 border border-gray-500 rounded text-sm"
            />
          </div>

          <button
            onClick={handleAddAction}
            disabled={!newAction.description.trim()}
            className="w-full px-3 py-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 rounded text-sm"
          >
            Add Action
          </button>
        </div>

        {/* Existing Actions */}
        <div className="space-y-2">
          {investigation?.actions?.map((action) => (
            <div
              key={action.id}
              className="flex items-center gap-3 p-3 bg-gray-700 rounded"
            >
              <span className="text-lg">{getActionIcon(action.type)}</span>

              <div className="flex-1">
                <div className="font-medium capitalize">{action.type}</div>
                <div className="text-sm text-gray-400">{action.description}</div>
                <div className="text-xs text-gray-500">
                  {new Date(action.timestamp).toLocaleString()}
                </div>
              </div>

              <button
                onClick={() => handleCompleteAction(action.id)}
                disabled={action.completed}
                className={`
                  px-3 py-1 rounded text-sm transition-colors
                  ${action.completed
                    ? 'bg-green-600 cursor-default'
                    : 'bg-blue-600 hover:bg-blue-700'
                  }
                `}
              >
                {action.completed ? '✓ Done' : 'Complete'}
              </button>
            </div>
          ))}

          {!investigation?.actions?.length && (
            <div className="text-center text-gray-500 py-4">
              <div className="text-2xl mb-2">📋</div>
              <p>No investigation actions yet</p>
            </div>
          )}
        </div>
      </div>

      {/* Investigation Timeline */}
      <div>
        <h3 className="text-lg font-semibold mb-3">Investigation Timeline</h3>
        <div className="space-y-3">
          {/* Discovery Time */}
          <div className="flex gap-3">
            <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
            <div>
              <div className="font-medium">Discovery Made</div>
              <div className="text-sm text-gray-400">
                {new Date(discovery.timestamp).toLocaleString()}
              </div>
            </div>
          </div>

          {/* Investigation Start */}
          {investigation?.start_time && (
            <div className="flex gap-3">
              <div className="w-2 h-2 bg-yellow-500 rounded-full mt-2"></div>
              <div>
                <div className="font-medium">Investigation Started</div>
                <div className="text-sm text-gray-400">
                  {new Date(investigation.start_time).toLocaleString()}
                </div>
              </div>
            </div>
          )}

          {/* Investigation End */}
          {investigation?.end_time && (
            <div className="flex gap-3">
              <div className="w-2 h-2 bg-green-500 rounded-full mt-2"></div>
              <div>
                <div className="font-medium">Investigation Completed</div>
                <div className="text-sm text-gray-400">
                  {new Date(investigation.end_time).toLocaleString()}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default InvestigationPanel;