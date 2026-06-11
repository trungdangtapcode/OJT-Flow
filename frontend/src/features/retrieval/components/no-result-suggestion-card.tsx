import { ListFilter } from "lucide-react";

import { Button } from "../../../components/ui/button";
import { NoResultActionCard } from "./no-result-action-card";
import type {
  NoResultFilterField,
  NoResultSuggestedAction,
} from "./no-result-remediation-types";

export function NoResultSuggestionCard({
  filterFieldLabel,
  isSearchPending,
  onApplyFacet,
  suggestedAction,
}: {
  filterFieldLabel: (field: NoResultFilterField) => string;
  isSearchPending: boolean;
  onApplyFacet: (field: NoResultFilterField, value: string) => void;
  suggestedAction: NoResultSuggestedAction | null;
}) {
  return (
    <NoResultActionCard
      text={
        suggestedAction
          ? "A backend corrective action has a supported filter. Apply it only if it matches the evidence class you need."
          : "No supported corrective filter was returned. Use a preset or adjust schema, format, fields, and source scope."
      }
      title={suggestedAction ? "Apply backend suggestion" : "Use guided presets"}
    >
      {suggestedAction ? (
        <Button
          disabled={isSearchPending}
          onClick={() => onApplyFacet(suggestedAction.field, suggestedAction.value)}
          size="sm"
          type="button"
          variant="outline"
        >
          <ListFilter className="h-4 w-4" />
          Apply {filterFieldLabel(suggestedAction.field)}
        </Button>
      ) : null}
    </NoResultActionCard>
  );
}
