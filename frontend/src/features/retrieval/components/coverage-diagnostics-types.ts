import type { RetrievalCoverageItem } from "../../../types";

export type CoverageDiagnosticsFilterField =
  | "clinical_domain"
  | "standard_system"
  | "source_type"
  | "trust_level"
  | "source_id";

export type CoverageDiagnosticsFilterAction = {
  field: CoverageDiagnosticsFilterField;
  value: string;
};

export type CoverageDiagnosticsActionHelpers = {
  filterFieldLabel: (field: CoverageDiagnosticsFilterField) => string;
  formatFilterValue: (field: CoverageDiagnosticsFilterField, value: string) => string;
  getCoverageSuggestedAction: (item: RetrievalCoverageItem) => string;
  getCoverageSuggestedFilter: (
    item: RetrievalCoverageItem,
  ) => CoverageDiagnosticsFilterAction | null;
  isSearchPending: boolean;
  onApplyCoverageFilter: (field: CoverageDiagnosticsFilterField, value: string) => void;
};
