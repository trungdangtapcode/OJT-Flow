import { Search } from "lucide-react";

import {
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../../components/ui/card";

export function QueryBuilderHeader() {
  return (
    <CardHeader className="border-b border-border bg-card/70">
      <CardTitle className="flex items-center gap-2">
        <Search className="h-5 w-5 text-primary" />
        Query builder
      </CardTitle>
      <CardDescription>Search approved schema, terminology, and corpus evidence.</CardDescription>
    </CardHeader>
  );
}
