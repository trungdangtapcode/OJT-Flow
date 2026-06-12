import { SearchHintCapabilityWarning } from "./search-hint-capability-warning";
import { SearchHintEndpointScopeSection } from "./search-hint-endpoint-scope-section";
import { SearchHintLineageFollowupSection } from "./search-hint-lineage-followup-section";
import type { SearchHintMetadataView } from "./search-hint-metadata";
import { SearchHintParameterExamplesSection } from "./search-hint-parameter-examples-section";
import { SearchHintSelectedCandidatesSection } from "./search-hint-selected-candidates-section";

export function SearchHintMetadataSectionList({
  view,
}: {
  view: SearchHintMetadataView;
}) {
  return (
    <div className="grid gap-2 border-t border-border p-2">
      <SearchHintEndpointScopeSection endpoints={view.scopeEndpoints} />
      <SearchHintSelectedCandidatesSection
        candidates={view.selectedCandidates}
        title={view.selectedCandidateTitle}
      />
      <SearchHintParameterExamplesSection examples={view.parameterExamples} />
      <SearchHintLineageFollowupSection items={view.lineageFollowup} />
      <SearchHintCapabilityWarning warning={view.capabilityWarning} />
    </div>
  );
}
