import { Badge } from "../../../components/ui/badge";

export type HitEvidenceAuditSummary = {
  aspect_count: number;
  concept_count: number;
  matched_term_count: number;
  provenance_field_count: number;
  ranking_signal_count: number;
};

export function HitEvidenceAuditStrip({
  formatCount,
  summary,
}: {
  formatCount: (count: number, singular: string) => string;
  summary: HitEvidenceAuditSummary;
}) {
  return (
    <div
      aria-label="Evidence support summary"
      className="flex min-w-0 flex-wrap gap-1.5 rounded-md border border-border bg-muted/20 p-2"
    >
      <Badge variant={summary.matched_term_count ? "success" : "warning"}>
        {formatCount(summary.matched_term_count, "matched term")}
      </Badge>
      <Badge variant={summary.provenance_field_count ? "success" : "warning"}>
        {formatCount(summary.provenance_field_count, "provenance field")}
      </Badge>
      <Badge variant={summary.concept_count ? "success" : "muted"}>
        {formatCount(summary.concept_count, "grounded concept")}
      </Badge>
      <Badge variant={summary.aspect_count ? "success" : "muted"}>
        {formatCount(summary.aspect_count, "aspect")}
      </Badge>
      <Badge variant={summary.ranking_signal_count ? "success" : "muted"}>
        {formatCount(summary.ranking_signal_count, "ranking signal")}
      </Badge>
    </div>
  );
}
