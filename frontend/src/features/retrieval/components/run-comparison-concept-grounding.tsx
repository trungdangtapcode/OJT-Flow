import { Badge } from "../../../components/ui/badge";
import type {
  BadgeVariant,
  ConceptGroundingSummaryView,
  RetrievalConceptGroundingComparisonView,
} from "./run-comparison-detail-types";

export function RunComparisonConceptGrounding({
  comparison,
}: {
  comparison: RetrievalConceptGroundingComparisonView;
}) {
  const changed = comparison.added.length || comparison.removed.length;
  return (
    <div className="grid gap-2 rounded-md border border-border bg-card px-3 py-2 text-xs">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="font-bold text-muted-foreground">Concept grounding</span>
        <Badge variant={changed ? "warning" : "success"}>
          {changed ? "changed" : "stable"}
        </Badge>
      </div>
      <ConceptGroundingChangeList
        concepts={comparison.added}
        emptyLabel="No newly grounded concepts."
        label="Added"
        variant="success"
      />
      <ConceptGroundingChangeList
        concepts={comparison.removed}
        emptyLabel="No lost grounded concepts."
        label="Removed"
        variant="warning"
      />
      <ConceptGroundingChangeList
        concepts={comparison.retained}
        emptyLabel="No retained grounded concepts."
        label="Retained"
        variant="muted"
      />
    </div>
  );
}

function ConceptGroundingChangeList({
  concepts,
  emptyLabel,
  label,
  variant,
}: {
  concepts: ConceptGroundingSummaryView[];
  emptyLabel: string;
  label: string;
  variant: BadgeVariant;
}) {
  return (
    <div className="grid gap-1">
      <span className="font-bold text-muted-foreground">{label}</span>
      {concepts.length ? (
        <div className="flex min-w-0 flex-wrap gap-1">
          {concepts.map((concept) => (
            <Badge
              className="max-w-full break-words"
              key={conceptGroundingKey(concept)}
              variant={variant}
            >
              {concept.standardSystem}
              {concept.code ? ` ${concept.code}` : ""}: {concept.displayName} (
              {concept.evidenceCount})
            </Badge>
          ))}
        </div>
      ) : (
        <span className="text-muted-foreground">{emptyLabel}</span>
      )}
    </div>
  );
}

function conceptGroundingKey(concept: ConceptGroundingSummaryView) {
  return `${concept.standardSystem}:${concept.code ?? concept.conceptId}`;
}
