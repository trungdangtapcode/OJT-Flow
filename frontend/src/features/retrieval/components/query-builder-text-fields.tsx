import { Search } from "lucide-react";

import { Textarea } from "../../../components/ui/form";
import type {
  RetrievalQueryBuilderActions,
  RetrievalQueryBuilderValue,
} from "./query-builder-panel-types";

export function QueryBuilderTextFields({
  actions,
  value,
}: {
  actions: RetrievalQueryBuilderActions;
  value: RetrievalQueryBuilderValue;
}) {
  return (
    <>
      <div className="relative w-full">
        <Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
        <Textarea
          className="w-full min-h-[2.75rem] resize-y pl-9 text-sm"
          onChange={(event) => {
            actions.onSetQuery(event.target.value);
            if (value.formError) actions.onClearFieldError();
          }}
          placeholder="Search evidence... e.g. missing units for lab_result glucose"
          value={value.query}
        />
      </div>

      <Textarea
        className="w-full min-h-[2.25rem] resize-y text-xs"
        onChange={(event) => actions.onSetFields(event.target.value)}
        placeholder="Fields (optional): date, patient_id, lab_name, value, unit"
        value={value.fields}
      />
    </>
  );
}
