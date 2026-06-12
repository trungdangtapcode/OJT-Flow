import type {
  RetrievalHit,
  RetrievalRecommendedAction,
} from "../../../types";

export function correctiveActionReportContext(
  hit: RetrievalHit,
  actions: RetrievalRecommendedAction[],
) {
  return {
    related_to_evidence: actions
      .filter((action) => action.evidence_ids.includes(hit.evidence.evidence_id))
      .slice(0, 6)
      .map(correctiveActionReportItem),
    package_top_actions: actions.slice(0, 6).map(correctiveActionReportItem),
  };
}

function correctiveActionReportItem(action: RetrievalRecommendedAction) {
  return {
    action_id: action.action_id,
    priority: action.priority,
    severity: action.severity,
    action_type: action.action_type,
    title: action.title,
    description: action.description,
    suggested_filter: action.suggested_filter,
    source_signal_codes: action.source_signal_codes,
    evidence_ids: action.evidence_ids,
    metadata: action.metadata,
  };
}
