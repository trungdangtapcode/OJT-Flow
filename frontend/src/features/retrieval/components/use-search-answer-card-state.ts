import type { RetrievalPackage, RetrievalSearchPayload } from "../../../types";
import { buildSearchAnswerViewModel } from "../model/search-answer";
import { copyTextToClipboard, useCopyFeedback } from "./copy-feedback";

const SEARCH_ANSWER_COPY_KEY = "search-answer-report";

export function useSearchAnswerCardState(
  packageData: RetrievalPackage,
  submittedSearchPayload: RetrievalSearchPayload | null,
) {
  const answer = buildSearchAnswerViewModel(packageData, submittedSearchPayload);
  const { copiedKey, markCopied } = useCopyFeedback(1600);

  const copyReport = async () => {
    await copyTextToClipboard(JSON.stringify(answer.report, null, 2));
    markCopied(SEARCH_ANSWER_COPY_KEY);
  };

  return {
    answer,
    copyReport,
    copied: copiedKey === SEARCH_ANSWER_COPY_KEY,
  };
}
