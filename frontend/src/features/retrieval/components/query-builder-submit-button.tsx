import { FileSearch, Loader2 } from "lucide-react";

import { Button } from "../../../components/ui/button";

export function QueryBuilderSubmitButton({ isSearchPending }: { isSearchPending: boolean }) {
  return (
    <Button disabled={isSearchPending} size="sm" type="submit">
      {isSearchPending ? (
        <Loader2 className="h-3.5 w-3.5 animate-spin" />
      ) : (
        <FileSearch className="h-3.5 w-3.5" />
      )}
      Search
    </Button>
  );
}
