import { qualityTone } from "./ranked-evidence-triage-guidance";
import { RankedEvidenceTriageFact } from "./ranked-evidence-triage-fact";
import type { RankedEvidenceTriageView } from "./ranked-evidence-triage-types";

export function RankedEvidenceTriageFacts({ view }: { view: RankedEvidenceTriageView }) {
  return (
    <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
      <RankedEvidenceTriageFact
        label="Ranked hits"
        value={`${view.hitCount}/${view.candidateCount}`}
      />
      <RankedEvidenceTriageFact
        label="Required buckets"
        tone={
          view.requiredBucketCount &&
          view.coveredRequiredBucketCount < view.requiredBucketCount
            ? "warning"
            : "success"
        }
        value={
          view.requiredBucketCount
            ? `${view.coveredRequiredBucketCount}/${view.requiredBucketCount}`
            : "none"
        }
      />
      <RankedEvidenceTriageFact
        label="Judgments"
        tone={view.judgedCount ? "success" : "warning"}
        value={view.judgedCount ? `${view.judgedCount} labeled` : "unlabeled"}
      />
      <RankedEvidenceTriageFact
        label="Readiness"
        tone={qualityTone(view.qualitySummary)}
        value={
          view.qualitySummary
            ? `${view.qualitySummary.status} ${view.qualitySummary.score}/100`
            : "unavailable"
        }
      />
    </div>
  );
}
