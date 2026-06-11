import type { RetrievalSearchPayload } from "../../../types";

export const missingRetrievalQueryMessage = "Enter a retrieval query before searching.";

export function retrievalRunPayloadValidationError(
  payload: RetrievalSearchPayload,
): string | null {
  return payload.query ? null : missingRetrievalQueryMessage;
}
