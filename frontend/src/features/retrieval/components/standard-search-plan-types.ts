import type {
  RetrievalStandardSearchStep,
} from "../../../types";
import type {
  SearchPlanFilterAction,
  SearchPlanFilterField,
} from "./strategy-standard-types";

export type StandardSearchPlanActionProps = {
  getSuggestedFilterAction: (value: unknown) => SearchPlanFilterAction | null;
  isSearchPending: boolean;
  onApplyFilter: (field: SearchPlanFilterField, value: string) => void;
};

export type StandardSearchStepCardProps = StandardSearchPlanActionProps & {
  step: RetrievalStandardSearchStep;
};
