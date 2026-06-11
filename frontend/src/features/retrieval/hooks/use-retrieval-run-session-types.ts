import type { RetrievalPackage, RetrievalSearchPayload } from "../../../types";
import type { RetrievalFormState } from "../model/retrieval-search-payload";

export type UseRetrievalRunSessionArgs = {
  createRunId?: () => string;
  formState: RetrievalFormState;
  historyLimit?: number;
  latestPackageData?: RetrievalPackage;
  now?: () => string;
  onValidationError: (message: string) => void;
  restoreSearchPayload: (payload: RetrievalSearchPayload) => void;
  submitSearch: (payload: RetrievalSearchPayload) => Promise<RetrievalPackage>;
};
