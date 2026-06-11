import type {
  RetrievalPackage,
  RetrievalSearchPayload,
  RetrievalSearchPreset,
} from "../../../types";

export type SearchMutationState = {
  data?: RetrievalPackage;
  error: unknown;
  isError: boolean;
  isPending: boolean;
  mutateAsync: (payload: RetrievalSearchPayload) => Promise<RetrievalPackage>;
};

export type UseRetrievalPageWorkspaceArgs = {
  presets: RetrievalSearchPreset[];
  searchMutation: SearchMutationState;
};
