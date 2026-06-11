import * as React from "react";

import {
  useRetrievalPlanQuery,
  workflowErrorMessage,
} from "../../../lib/server-state";
import type { RetrievalPackage, RetrievalSearchPayload } from "../../../types";
import {
  retrievalPayloadFromForm,
  retrievalSearchSignature,
  type RetrievalFormState,
} from "../model/retrieval-search-payload";

const defaultPlanDebounceMs = 400;

type UseRetrievalPlanSessionArgs = {
  currentSearchSignature: string;
  debounceMs?: number;
  formState: RetrievalFormState;
  packageData?: RetrievalPackage;
  submittedSearchPayload: RetrievalSearchPayload | null;
};

export function useRetrievalPlanSession({
  currentSearchSignature,
  debounceMs = defaultPlanDebounceMs,
  formState,
  packageData,
  submittedSearchPayload,
}: UseRetrievalPlanSessionArgs) {
  const [planPayload, setPlanPayload] = React.useState<RetrievalSearchPayload | null>(
    null,
  );

  React.useEffect(() => {
    const payload = retrievalPayloadFromForm(formState);
    if (!payload.query) {
      setPlanPayload(null);
      return;
    }
    const timeoutId = window.setTimeout(() => {
      setPlanPayload(payload);
    }, debounceMs);
    return () => window.clearTimeout(timeoutId);
  }, [currentSearchSignature, debounceMs]);

  const submittedSearchSignature = submittedSearchPayload
    ? retrievalSearchSignature(submittedSearchPayload)
    : null;
  const planQuery = useRetrievalPlanQuery(planPayload);
  const isSearchResultStale = Boolean(
    packageData &&
      submittedSearchSignature &&
      currentSearchSignature !== submittedSearchSignature,
  );
  const isPlanForCurrentSearch = Boolean(
    planPayload && retrievalSearchSignature(planPayload) === currentSearchSignature,
  );

  return {
    currentPlanData: isPlanForCurrentSearch ? planQuery.data : undefined,
    currentPlanPayload: isPlanForCurrentSearch ? planPayload : null,
    isPlanLoading: planQuery.isFetching,
    isSearchResultStale,
    packageDataForPlanPreview: isSearchResultStale ? undefined : packageData,
    planError: planQuery.isError ? workflowErrorMessage(planQuery.error) : null,
    planPayload,
    submittedSearchSignature,
  };
}
