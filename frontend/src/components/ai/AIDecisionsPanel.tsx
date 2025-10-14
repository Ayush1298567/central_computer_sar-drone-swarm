import React, { useEffect, useState } from 'react';
import wsService from '../../services/websocket';
import { aiDecisionStore, subscribeAIDecisions, addAIDecision, applyDecisionLocal, rejectDecisionLocal } from '../../stores/aiDecisions';
import api from '../../services/api';

const AIDecisionsPanel: React.FC = () => {
  const [_, setTick] = useState(0);

  useEffect(() => {
    // Subscribe to WebSocket ai_decisions
    const off = wsService.on('ai_decisions', (payload: any) => {
      addAIDecision(payload);
    });

    // Subscribe to store updates to rerender
    const unsubStore = subscribeAIDecisions(() => setTick((t) => t + 1));

    return () => { off(); unsubStore(); };
  }, []);

  const handleApply = async (decisionId: string) => {
    try {
      const decision = aiDecisionStore.recent.find(d => d.decision_id === decisionId);
      if (!decision) return;
      await api.post(`/v1/ai/decisions/${decisionId}/apply`, { decision });
      applyDecisionLocal(decisionId);
    } catch (e) {
      console.error('Apply decision failed', e);
    }
  };

  const handleReject = (decisionId: string) => {
    rejectDecisionLocal(decisionId);
    // TODO: optionally notify backend
  };

  const items = aiDecisionStore.recent;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">AI Decisions</h2>
      {items.length === 0 ? (
        <p className="text-sm text-gray-500">No AI suggestions yet</p>
      ) : (
        <div className="space-y-3">
          {items.map((d) => (
            <div key={d.decision_id} className="p-4 border border-gray-200 rounded-lg">
              <div className="flex items-center justify-between mb-1">
                <div className="text-sm text-gray-600">{d.decision_type}</div>
                <div className="text-xs text-gray-500">{new Date(d.created_at).toLocaleTimeString()}</div>
              </div>
              <div className="text-gray-900 font-medium">{d.selected_option?.description || 'Suggestion'}</div>
              <div className="text-xs text-gray-500 mt-1">Confidence: {(d.confidence_level * 100).toFixed(0)}%</div>
              {d.reasoning_chain?.length ? (
                <ul className="mt-2 list-disc list-inside text-xs text-gray-600">
                  {d.reasoning_chain.slice(0, 3).map((r, idx) => (
                    <li key={idx}>{r}</li>
                  ))}
                </ul>
              ) : null}
              <div className="mt-3 flex gap-2">
                <button className="px-3 py-1 bg-green-600 text-white rounded" onClick={() => handleApply(d.decision_id)}>Apply</button>
                <button className="px-3 py-1 bg-gray-200 text-gray-800 rounded" onClick={() => handleReject(d.decision_id)}>Reject</button>
                <span className="ml-auto text-xs text-gray-500 capitalize">{d.status}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AIDecisionsPanel;
