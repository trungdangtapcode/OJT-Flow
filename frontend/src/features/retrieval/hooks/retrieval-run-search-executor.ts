import type { RetrievalSearchPayload } from "../../../types";
import {
  retrievalPayloadFromForm,
  type RetrievalFormState,
} from "../model/retrieval-search-payload";
import {
  commitCompletedSearchRun,
  type CompletedRunSessionSetters,
} from "./retrieval-run-session-completion";
import { createRetrievalRunRecord } from "./retrieval-run-session-record";
import { retrievalRunPayloadValidationError } from "./retrieval-run-session-validation";
import type { UseRetrievalRunSessionArgs } from "./use-retrieval-run-session-types";

export type ExecuteRetrievalRunSearchArgs = Pick<
  UseRetrievalRunSessionArgs,
  "onValidationError" | "submitSearch"
> & {
  createRunId: () => string;
  formState: RetrievalFormState;
  historyLimit: number;
  now: () => string;
  overrides?: Partial<RetrievalSearchPayload>;
  sessionState: CompletedRunSessionSetters;
};

export async function executeRetrievalRunSearch({
  createRunId,
  formState,
  historyLimit,
  now,
  onValidationError,
  overrides = {},
  sessionState,
  submitSearch,
}: ExecuteRetrievalRunSearchArgs) {
  const payload = retrievalPayloadFromForm(formState, overrides);
  const validationError = retrievalRunPayloadValidationError(payload);
  if (validationError) {
    onValidationError(validationError);
    return;
  }

  const packageResult = await submitSearch(payload);
  const { run, signature } = createRetrievalRunRecord({
    createRunId,
    now,
    packageData: packageResult,
    payload,
  });
  commitCompletedSearchRun({
    historyLimit,
    payload,
    run,
    sessionState,
    signature,
  });
}
