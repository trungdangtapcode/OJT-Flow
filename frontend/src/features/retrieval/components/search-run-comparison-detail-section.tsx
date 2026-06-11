import {
  RunComparisonConceptGrounding,
  RunComparisonCoverage,
  RunComparisonEvidenceChange,
  RunComparisonFacetCoverage,
  RunComparisonQualitySignals,
  RunComparisonQueryAspects,
  RunComparisonQueryProfile,
  RunComparisonRankChanges,
  RunComparisonRulePacks,
} from "./run-comparison-detail-panels";
import type { SearchRunComparisonDetailProps } from "./search-run-comparison-types";

export function SearchRunComparisonDetailSection({
  comparison,
  formatCount,
  rulePackChanges,
}: SearchRunComparisonDetailProps) {
  return (
    <div className="grid gap-2">
      <RunComparisonQueryProfile comparison={comparison} />
      <RunComparisonConceptGrounding comparison={comparison.conceptGroundingComparison} />
      <RunComparisonQueryAspects
        comparison={comparison.queryAspectComparison}
        formatCount={formatCount}
      />
      <RunComparisonCoverage
        comparison={comparison.coverageComparison}
        formatCount={formatCount}
      />
      <RunComparisonQualitySignals
        comparison={comparison.qualitySignalComparison}
        formatCount={formatCount}
      />
      <RunComparisonFacetCoverage
        facetComparisons={comparison.facetComparisons}
        formatCount={formatCount}
      />
      <RunComparisonRulePacks
        formatCount={formatCount}
        rulePackChanges={rulePackChanges}
      />
      <RunComparisonRankChanges
        formatCount={formatCount}
        rankChanges={comparison.rankChanges}
      />
      <RunComparisonEvidenceChange
        evidenceIds={comparison.addedEvidenceIds}
        label="Added evidence"
        variant="success"
      />
      <RunComparisonEvidenceChange
        evidenceIds={comparison.removedEvidenceIds}
        label="Removed evidence"
        variant="warning"
      />
      <RunComparisonEvidenceChange
        evidenceIds={comparison.retainedEvidenceIds}
        label="Retained evidence"
        variant="muted"
      />
    </div>
  );
}
