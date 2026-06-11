import { useCopyFeedback } from "./copy-feedback";

const JUDGMENT_EVALUATION_COPY_KEY = "judgment-evaluation-report";

export function useJudgmentEvaluationReportCopy({
  copyTextToClipboard,
  evaluationReportJson,
}: {
  copyTextToClipboard: (text: string) => Promise<void>;
  evaluationReportJson: string | null;
}) {
  const { copiedKey, markCopied } = useCopyFeedback();
  const evaluationCopied = copiedKey === JUDGMENT_EVALUATION_COPY_KEY;

  const copyEvaluationReport = async () => {
    if (!evaluationReportJson) return;
    await copyTextToClipboard(evaluationReportJson);
    markCopied(JUDGMENT_EVALUATION_COPY_KEY);
  };

  return { copyEvaluationReport, evaluationCopied };
}
