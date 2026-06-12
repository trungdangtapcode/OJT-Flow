import { ListFilter } from "lucide-react";

import { Button } from "../../../components/ui/button";
import type { RetrievalSearchCockpitView } from "../model/retrieval-cockpit-view-model";
import type { SearchPlanFilterField } from "./strategy-standard-panels";

export function SearchCockpitApplyAction({
  filterFieldLabel,
  isSearchPending,
  onApplyFilter,
  view,
}: {
  filterFieldLabel: (field: SearchPlanFilterField) => string;
  isSearchPending: boolean;
  onApplyFilter: (field: SearchPlanFilterField, value: string) => void;
  view: RetrievalSearchCockpitView;
}) {
  if (!view.topFilterAction) return null;
  return (
    <Button
      disabled={isSearchPending}
      onClick={() => onApplyFilter(view.topFilterAction!.field, view.topFilterAction!.value)}
      size="sm"
      type="button"
      variant="outline"
    >
      <ListFilter className="h-4 w-4" />
      Apply {filterFieldLabel(view.topFilterAction.field)}
    </Button>
  );
}
