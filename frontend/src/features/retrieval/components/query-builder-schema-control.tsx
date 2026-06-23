import { Label, Select } from "../../../components/ui/form";
import type { QueryBuilderContextControlProps } from "./query-builder-context-control-types";

export function QueryBuilderSchemaControl({
  actions,
  options,
  value,
}: QueryBuilderContextControlProps) {
  return (
    <Label>
      Schema
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
