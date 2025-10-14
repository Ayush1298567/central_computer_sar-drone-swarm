export interface AIDecision {
  decision_id: string;
  decision_type: string;
  mission_id?: string | null;
  drone_id?: string | null;
  selected_option: any;
  alternative_options?: any[];
  confidence_level: number;
  reasoning_chain: string[];
  risk_assessment: any;
  expected_impact: any;
  authority_level: string;
  created_at: string;
  trigger?: any;
  status?: 'suggested' | 'applied' | 'rejected';
}

export type AIDecisionState = {
  recent: AIDecision[];
  listeners: Set<() => void>;
};

export const aiDecisionStore: AIDecisionState = {
  recent: [],
  listeners: new Set(),
};

function notify() {
  aiDecisionStore.listeners.forEach((fn) => {
    try { fn(); } catch {}
  });
}

export function subscribeAIDecisions(listener: () => void) {
  aiDecisionStore.listeners.add(listener);
  return () => aiDecisionStore.listeners.delete(listener);
}

export function addAIDecision(d: AIDecision) {
  const exists = aiDecisionStore.recent.find((x) => x.decision_id === d.decision_id);
  if (!exists) {
    aiDecisionStore.recent.unshift({ ...d, status: 'suggested' });
    if (aiDecisionStore.recent.length > 50) aiDecisionStore.recent.pop();
    notify();
  }
}

export function applyDecisionLocal(decisionId: string) {
  const item = aiDecisionStore.recent.find((d) => d.decision_id === decisionId);
  if (item) { item.status = 'applied'; notify(); }
}

export function rejectDecisionLocal(decisionId: string) {
  const item = aiDecisionStore.recent.find((d) => d.decision_id === decisionId);
  if (item) { item.status = 'rejected'; notify(); }
}
