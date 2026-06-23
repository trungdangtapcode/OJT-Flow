import { CardContent } from "../../../components/ui/card";
import { SearchAnswerCard } from "./search-answer-card";
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
      <SearchAnswerCard
        packageData={sharedProps.packageData}
        submittedSearchPayload={sharedProps.submittedSearchPayload}
      />
      <SearchResultsHitList {...hitsProps} />

      <details className="rounded-xl border border-border/50 bg-muted/20 px-4 py-3">
        <summary className="cursor-pointer list-none text-sm font-semibold">
          Review signals and diagnostics
        </summary>
        <div className="mt-4 grid gap-3">
          <SearchResultsOverviewSection
            {...sharedProps}
            onRestoreSubmittedSearch={onRestoreSubmittedSearch}
          />
          <SearchResultsEvidenceSection {...sharedProps} />
          <SearchResultsJudgmentSection {...judgmentProps} />
        </div>
      </details>
    </CardContent>
  );
}
