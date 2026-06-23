import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import type { RetrievalRuntimeStatusView } from "../model/retrieval-runtime-status-model";

export function RetrievalRuntimeStatusStrip({
  view,
}: {
  view: RetrievalRuntimeStatusView;
}) {
  return (
    <div
      aria-label="Runtime status"
      className="flex min-w-0 flex-wrap items-center gap-1.5 text-xs"
    >
      <Badge variant={view.sourceDiversityEnabled ? "success" : "muted"}>{view.retrievalMode}</Badge>
      <Badge variant={view.rerankerEnabled ? "success" : "muted"}>
        reranker {view.rerankerEnabled ? "on" : "off"}
      </Badge>
      <Badge variant={view.graphNodeCount === null ? "muted" : "success"}>
        graph {view.graphNodeCount === null ? "n/a" : view.graphNodeCount}
      </Badge>
      <Badge variant={view.integrityStatus === "ok" ? "success" : "warning"}>
        {humanize(view.integrityStatus)}
      </Badge>
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
