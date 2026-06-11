import type { RetrievalSource } from "../../../types";

export type SourceScopePickerProps = {
  isSearchPending: boolean;
  onClear: () => void;
  onSelect: (sourceId: string) => void;
  selectedSource: RetrievalSource | null;
  sourceId: string;
  sources: RetrievalSource[];
};

export type SourceScopeSelectionProps = {
  selectedSource: RetrievalSource | null;
  sourceId: string;
};
