import { Search } from "lucide-react";

import {
  CardHeader,
  CardTitle,
} from "../../../components/ui/card";

export function QueryBuilderHeader() {
  return (
    <CardHeader className="border-b border-border/40 bg-muted/20 py-3">
      <CardTitle className="flex items-center gap-2 text-sm">
        <Search className="h-4 w-4 text-primary" />
        Evidence search
      </CardTitle>
    </CardHeader>
  );
}
