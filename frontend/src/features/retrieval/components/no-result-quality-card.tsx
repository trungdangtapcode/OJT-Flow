import { NoResultActionCard } from "./no-result-action-card";

export function NoResultQualityCard({ candidateCount }: { candidateCount: number }) {
  return (
    <NoResultActionCard
      text={
        candidateCount
          ? "Candidates were seen, so review readiness, evidence buckets, and strategy recommendations for why none became usable hits."
          : "No candidates were seen. Reindex the trusted corpus or confirm the source inventory contains the domain and standard you need."
      }
      title={candidateCount ? "Inspect quality gaps" : "Check source inventory"}
    />
  );
}
