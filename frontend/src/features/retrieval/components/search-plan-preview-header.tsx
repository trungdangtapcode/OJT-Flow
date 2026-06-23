import { BrainCircuit } from "lucide-react";

import {
  CardHeader,
  CardTitle,
} from "../../../components/ui/card";
import { SearchPlanCopyAction } from "./search-plan-copy-action";

export function SearchPlanPreviewHeader({
  copied,
  onCopyPlan,
}: {
  copied: boolean;
  onCopyPlan: () => void;
}) {
  return (
    <CardHeader className="flex-row items-center justify-between gap-2 border-b border-border/40 bg-muted/20 py-3">
      <CardTitle className="flex items-center gap-2 text-sm">
        <BrainCircuit className="h-4 w-4 text-primary" />
        Search plan
      </CardTitle>
      <SearchPlanCopyAction copied={copied} onCopyPlan={onCopyPlan} />
    </CardHeader>
  );
}
