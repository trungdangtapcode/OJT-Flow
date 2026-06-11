import { FileSearch, Loader2 } from "lucide-react";

import { Button } from "../../../components/ui/button";

export function QueryBuilderSubmitButton({ isSearchPending }: { isSearchPending: boolean }) {
  return (
    <Button disabled={isSearchPending} type="submit">
      {isSearchPending ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : (
        <FileSearch className="h-4 w-4" />
      )}
      Search evidence
    </Button>
  );
}
