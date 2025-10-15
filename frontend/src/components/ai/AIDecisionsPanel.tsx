import React, { useEffect, useState } from 'react';
import { wsService } from '../../services/websocket';

interface AIDecision {
  decision_id: string;
  type: string;
  reasoning: string;
  confidence_score: number;
  severity: string;
  mission_id?: string;
  drone_id?: string;
  recommended_action?: string;
}

interface ApplyState {
  [decisionId: string]: 'idle' | 'loading' | 'error' | 'applied';
}

export const AIDecisionsPanel: React.FC = () => {
  const [decisions, setDecisions] = useState<AIDecision[]>([]);
  const [applyState, setApplyState] = useState<ApplyState>({});
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    const unsub = wsService.on('ai_decisions', (payload) => {
      setDecisions((prev) => [payload as AIDecision, ...prev].slice(0, 20));
    });
    return () => {
      unsub();
    };
  }, []);

  const applyDecision = async (d: AIDecision) => {
    setErrorMsg(null);
    setApplyState((s) => ({ ...s, [d.decision_id]: 'loading' }));
    try {
      const res = await fetch(`/api/v1/ai/decisions/${d.decision_id}/apply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          decision_id: d.decision_id,
          decision_type: d.type,
          mission_id: d.mission_id,
          drone_id: d.drone_id,
          payload: { action: d.recommended_action }
        })
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setApplyState((s) => ({ ...s, [d.decision_id]: 'applied' }));
    } catch (e: any) {
      setApplyState((s) => ({ ...s, [d.decision_id]: 'error' }));
      setErrorMsg(e?.message || 'Apply failed');
    }
  };

  const badge = (severity: string) => {
    const cls = severity === 'critical' ? 'bg-red-100 text-red-800' : severity === 'high' ? 'bg-orange-100 text-orange-800' : 'bg-gray-100 text-gray-800';
    return <span className={`px-2 py-1 rounded-full text-xs font-medium ${cls}`}>{severity}</span>;
  };

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900">AI Decisions</h2>
      </div>
      <div className="p-6">
        {errorMsg && (
          <div className="mb-3 text-sm text-red-600">{errorMsg}</div>
        )}
        {decisions.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No AI decisions yet</p>
        ) : (
          <div className="space-y-3">
            {decisions.map((d) => (
              <div key={d.decision_id} className="p-3 border border-gray-200 rounded-lg">
                <div className="flex justify-between items-start">
                  <div className="font-medium text-gray-900">{d.type}</div>
                  {badge(d.severity)}
                </div>
                <div className="text-sm text-gray-700 mt-1">{d.reasoning}</div>
                <div className="text-xs text-gray-500 mt-1">Confidence: {(d.confidence_score * 100).toFixed(0)}%</div>
                <div className="flex items-center gap-3 mt-3">
                  <button
                    className="px-3 py-1 rounded bg-blue-600 text-white disabled:opacity-50"
                    disabled={!d.recommended_action || applyState[d.decision_id] === 'loading' || applyState[d.decision_id] === 'applied'}
                    onClick={() => applyDecision(d)}
                  >
                    {applyState[d.decision_id] === 'loading' ? 'Applying...' : applyState[d.decision_id] === 'applied' ? 'Applied' : 'Apply'}
                  </button>
                  {applyState[d.decision_id] === 'error' && (
                    <span className="text-xs text-red-600">Failed</span>
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

export default AIDecisionsPanel;
