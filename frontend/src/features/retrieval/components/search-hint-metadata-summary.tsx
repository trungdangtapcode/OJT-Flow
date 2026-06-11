import { Badge } from "../../../components/ui/badge";
import type { SearchHintMetadataView } from "./search-hint-metadata";
import { formatSearchHintMetadataCount } from "./search-hint-metadata-format";

export function SearchHintMetadataSummary({
  view,
}: {
  view: SearchHintMetadataView;
}) {
  return (
    <summary className="flex cursor-pointer list-none flex-wrap items-center gap-1.5 px-2 py-1.5 font-black">
      Route details
      {view.parameterExamples.length ? (
        <Badge variant="muted">
          {formatSearchHintMetadataCount(view.parameterExamples.length, "parameter")}
        </Badge>
      ) : null}
      {view.scopeEndpoints.length ? <Badge variant="muted">scoped API</Badge> : null}
      {view.selectedCandidates.length ? (
        <Badge variant="success">
          {formatSearchHintMetadataCount(view.selectedCandidates.length, "candidate")}
        </Badge>
      ) : null}
      {view.lineageFollowup.length ? <Badge variant="warning">lineage</Badge> : null}
    </summary>
  );
}
