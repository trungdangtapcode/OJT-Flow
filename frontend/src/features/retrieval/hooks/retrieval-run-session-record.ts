import type {
  RetrievalPackage,
  RetrievalSearchPayload,
} from "../../../types";
import {
  retrievalRunSummary,
  serverSearchSignatureFromPackage,
  type RetrievalSearchRun,
} from "../model/retrieval-run-summary";
import { retrievalSearchSignature } from "../model/retrieval-search-payload";
import { createSearchRun } from "../model/search-run-presentation";

export function createRetrievalRunRecord({
  createRunId,
  now,
  packageData,
  payload,
}: {
  createRunId: () => string;
  now: () => string;
  packageData: RetrievalPackage;
  payload: RetrievalSearchPayload;
}): {
  run: RetrievalSearchRun;
  signature: string;
} {
  const signature =
    serverSearchSignatureFromPackage(packageData) ?? retrievalSearchSignature(payload);
  return {
    run: createSearchRun({
      createRunId,
      now,
      packageData,
      payload,
      signature,
      summary: retrievalRunSummary(packageData),
    }),
    signature,
  };
}
