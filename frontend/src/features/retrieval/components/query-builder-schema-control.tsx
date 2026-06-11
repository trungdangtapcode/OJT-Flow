import { Label, Select } from "../../../components/ui/form";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import type { QueryBuilderContextControlProps } from "./query-builder-context-control-types";

export function QueryBuilderSchemaControl({
  actions,
  options,
  value,
}: QueryBuilderContextControlProps) {
  return (
    <Label>
      <span className="inline-flex items-center gap-1.5">
        Schema
        <HelpTooltip label="Schema filter help">
          Limits retrieval to evidence related to a known OJTFlow schema. Leave blank for broad discovery.
        </HelpTooltip>
      </span>
      <Select
        onChange={(event) => actions.onSetSchemaId(event.target.value)}
        value={value.schemaId}
      >
        <option value="">Any schema</option>
        {options.schemas.map((schema) => (
          <option key={schema.schema_id} value={schema.schema_id}>
            {schema.schema_id}
          </option>
        ))}
      </Select>
    </Label>
  );
}
