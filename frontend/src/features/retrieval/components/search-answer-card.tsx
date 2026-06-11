import type { RetrievalPackage, RetrievalSearchPayload } from "../../../types";
import { SearchAnswerHeader } from "./search-answer-header";
import { SearchAnswerMetrics } from "./search-answer-metrics";
import { SearchAnswerWarningPanel } from "./search-answer-warning-panel";
import { useSearchAnswerCardState } from "./use-search-answer-card-state";

export function SearchAnswerCard({
  packageData,
  submittedSearchPayload,
}: {
  packageData: RetrievalPackage;
  submittedSearchPayload: RetrievalSearchPayload | null;
}) {
  const { answer, copied, copyReport } = useSearchAnswerCardState(
    packageData,
    submittedSearchPayload,
  );

  return (
    <section
      aria-label="Search answer"
      className="grid gap-3 rounded-md border border-primary/25 bg-primary/5 p-3"
    >
      <SearchAnswerHeader
        answer={answer}
        copied={copied}
        hitCount={packageData.hits.length}
        onCopyReport={() => void copyReport()}
      />
      <SearchAnswerMetrics metrics={answer.metrics} />
      <SearchAnswerWarningPanel warnings={answer.warnings} />
    </section>
  );
}
