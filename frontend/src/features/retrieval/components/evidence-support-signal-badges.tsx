import { Badge } from "../../../components/ui/badge";
import type { EvidenceSupportMatrixRowView } from "./evidence-support-matrix-types";

export function EvidenceSupportSignalBadges({
  row,
}: {
  row: EvidenceSupportMatrixRowView;
}) {
  return (
    <div className="flex min-w-0 flex-wrap gap-1">
      <Badge variant={row.matchedTermCount ? "success" : "warning"}>
        {row.matchedTermCount} terms
      </Badge>
      <Badge variant={row.provenanceCount ? "success" : "warning"}>
        {row.provenanceCount} provenance
      </Badge>
      <Badge variant={row.conceptCount ? "success" : "muted"}>
        {row.conceptCount} concepts
      </Badge>
      <Badge variant={row.aspectCount ? "success" : "muted"}>
        {row.aspectCount} aspects
      </Badge>
    </div>
  );
}
