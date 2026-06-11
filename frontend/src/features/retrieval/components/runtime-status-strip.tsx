import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import type { RetrievalRuntimeStatusView } from "../model/retrieval-runtime-status-model";
import { graphStatusSupporting } from "./runtime-graph-status";
import { RuntimeStatusFact } from "./runtime-status-fact";

export function RetrievalRuntimeStatusStrip({
  view,
}: {
  view: RetrievalRuntimeStatusView;
}) {
  return (
    <div
      aria-label="Retrieval runtime status"
      className="grid gap-2 rounded-md border border-border bg-card/80 p-3 text-xs sm:grid-cols-2 xl:grid-cols-4"
    >
      <RuntimeStatusFact
        label="Retrieval mode"
        supporting={view.sourceDiversityEnabled ? "diverse source selection" : "score order"}
        value={view.retrievalMode}
        variant={view.sourceDiversityEnabled ? "success" : "muted"}
      />
      <RuntimeStatusFact
        label="Reranker"
        supporting={view.rerankerEnabled ? "second-stage ranking active" : "first-stage ranking only"}
        value={view.rerankerEnabled ? "enabled" : "off"}
        variant={view.rerankerEnabled ? "success" : "muted"}
      />
      <RuntimeStatusFact
        label="Graph handoff"
        supporting={graphStatusSupporting(view)}
        value={view.graphNodeCount === null ? "not ready" : `${view.graphNodeCount} nodes`}
        variant={view.graphNodeCount === null ? "muted" : "success"}
      />
      <RuntimeStatusFact
        label="Index integrity"
        supporting={view.sourceCoverageLabel}
        value={humanize(view.integrityStatus)}
        variant={view.integrityStatus === "ok" ? "success" : "warning"}
      />
    </div>
  );
}

export function RuntimeDiversityBadge({
  enabled,
  sourceCoverageLabel,
}: {
  enabled: boolean;
  sourceCoverageLabel: string;
}) {
  if (!enabled) {
    return <Badge variant="muted">score order</Badge>;
  }
  return <Badge variant="success">{sourceCoverageLabel} sources</Badge>;
}

export function RuntimeRerankBadge({ enabled }: { enabled: boolean }) {
  if (!enabled) {
    return <Badge variant="muted">first stage only</Badge>;
  }
  return <Badge variant="success">reranked</Badge>;
}
