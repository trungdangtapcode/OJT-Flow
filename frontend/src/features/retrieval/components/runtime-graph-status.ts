import type { RetrievalRuntimeStatusView } from "../model/retrieval-runtime-status-model";

export function graphStatusSupporting(view: RetrievalRuntimeStatusView) {
  if (view.graphNodeCount === null) {
    return "run search to prepare graph context";
  }
  return `${view.graphEdgeCount ?? 0} edges / ${view.graphTripleCount ?? 0} triples`;
}
