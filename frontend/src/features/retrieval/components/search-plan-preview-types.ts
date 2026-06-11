import type {
  RetrievalQualitySummary,
  RetrievalSearchTask,
} from "../../../types";
import type { SearchPlanPreviewView } from "../model/search-plan-preview-types";
import type { FilterSuggestionStack } from "./search-plan-detail-panels";

export type SearchPlanBadgeVariant =
  | "default"
  | "success"
  | "warning"
  | "destructive"
  | "muted";

export type SupportedPlanFilterField =
  | "clinical_domain"
  | "standard_system"
  | "source_type"
  | "trust_level"
  | "source_id";

export type SearchPlanCopyFeedbackHook = () => {
  copiedKey: string | null;
  markCopied: (key: string) => void;
};

export type SearchPlanPreviewProps = {
  copyTextToClipboard: (text: string) => Promise<void>;
  formatCount: (count: number, singular: string) => string;
  formatFilterValue: (field: SupportedPlanFilterField, value: string) => string;
  isPlanLoading: boolean;
  isSearchPending: boolean;
  isSupportedFilterField: (field: string) => field is SupportedPlanFilterField;
  onApplyFilterSuggestion: (suggestion: FilterSuggestionStack) => void;
  onCopyPlan: () => Promise<void>;
  onRunTask: (task: RetrievalSearchTask) => void;
  planError: string | null;
  qualitySummaryBadgeVariant: (
    summary: RetrievalQualitySummary,
  ) => SearchPlanBadgeVariant;
  useCopyFeedback: SearchPlanCopyFeedbackHook;
  view: SearchPlanPreviewView | null;
};
