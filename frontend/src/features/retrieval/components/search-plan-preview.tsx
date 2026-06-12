import { Card } from "../../../components/ui/card";
import { SearchPlanPreviewContent } from "./search-plan-preview-content";
import { SearchPlanPreviewEmpty } from "./search-plan-preview-empty";
import { SearchPlanPreviewHeader } from "./search-plan-preview-header";
import type { SearchPlanPreviewProps } from "./search-plan-preview-types";

export function SearchPlanPreview({
  onCopyPlan,
  useCopyFeedback,
  view,
  ...contentProps
}: SearchPlanPreviewProps) {
  const { copiedKey, markCopied } = useCopyFeedback();
  const copyKey = "retrieval-search-plan-preview";

  if (!view) {
    return <SearchPlanPreviewEmpty planError={contentProps.planError} />;
  }

  const copied = copiedKey === copyKey;
  const copyPlan = async () => {
    await onCopyPlan();
    markCopied(copyKey);
  };

  return (
    <Card className="min-w-0 overflow-hidden">
      <SearchPlanPreviewHeader
        copied={copied}
        onCopyPlan={() => void copyPlan()}
      />
      <SearchPlanPreviewContent
        {...contentProps}
        useCopyFeedback={useCopyFeedback}
        view={view}
      />
    </Card>
  );
}
