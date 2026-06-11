import { CardContent } from "../../../components/ui/card";
import { SearchResultsEvidenceSection } from "./search-results-evidence-section";
import { SearchResultsHitList } from "./search-results-hit-list";
import { SearchResultsJudgmentSection } from "./search-results-judgment-section";
import { SearchResultsOverviewSection } from "./search-results-overview-section";
import type { SearchResultsContentProps } from "./search-results-content-props";

export function SearchResultsContent({
  hitsProps,
  judgmentProps,
  onRestoreSubmittedSearch,
  sharedProps,
}: SearchResultsContentProps) {
  return (
    <CardContent className="grid gap-3 pt-4">
      <SearchResultsOverviewSection
        {...sharedProps}
        onRestoreSubmittedSearch={onRestoreSubmittedSearch}
      />
      <SearchResultsJudgmentSection {...judgmentProps} />
      <SearchResultsEvidenceSection {...sharedProps} />
      <SearchResultsHitList {...hitsProps} />
    </CardContent>
  );
}
