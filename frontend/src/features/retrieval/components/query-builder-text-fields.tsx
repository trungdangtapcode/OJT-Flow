import { Label, Textarea } from "../../../components/ui/form";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
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
      <Label>
        <span className="inline-flex items-center gap-1.5">
          Query
          <HelpTooltip label="Retrieval query help">
            Ask for the evidence you need, not a diagnosis. Include the data operation, field names, standard, or validation issue when known.
          </HelpTooltip>
        </span>
        <Textarea
          className="min-h-24 resize-y"
          onChange={(event) => {
            actions.onSetQuery(event.target.value);
            if (value.formError) actions.onClearFieldError();
          }}
          placeholder="Example: explain missing units for lab_result_v1 glucose CSV fields"
          value={value.query}
        />
      </Label>

      <Label>
        <span className="inline-flex items-center gap-1.5">
          Fields
          <HelpTooltip label="Retrieval fields help">
            Optional comma-separated dataset fields. Field names help retrieval match schema rules and PHI-sensitive columns.
          </HelpTooltip>
        </span>
        <Textarea
          className="min-h-16 resize-y"
          onChange={(event) => actions.onSetFields(event.target.value)}
          placeholder="date, patient_id, lab_name, value, unit"
          value={value.fields}
        />
      </Label>
    </>
  );
}
