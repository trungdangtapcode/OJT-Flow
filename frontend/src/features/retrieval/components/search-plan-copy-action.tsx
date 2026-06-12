import { CheckCircle2, Clipboard } from "lucide-react";

import { Button } from "../../../components/ui/button";

export function SearchPlanCopyAction({
  copied,
  onCopyPlan,
}: {
  copied: boolean;
  onCopyPlan: () => void;
}) {
  return (
    <Button
      aria-label="Copy search plan JSON"
      onClick={onCopyPlan}
      size="sm"
      type="button"
      variant="outline"
    >
      {copied ? <CheckCircle2 className="h-4 w-4" /> : <Clipboard className="h-4 w-4" />}
      {copied ? "Copied" : "Copy plan"}
    </Button>
  );
}
