import { Input, Label } from "../../../components/ui/form";
import type { QueryBuilderContextControlProps } from "./query-builder-context-control-types";

export function QueryBuilderResourceControl({
  actions,
  value,
}: QueryBuilderContextControlProps) {
  return (
    <Label>
      Resource
      <Input
        onChange={(event) => actions.onSetResourceType(event.target.value)}
        placeholder="e.g. Observation"
        value={value.resourceType}
      />
    </Label>
  );
}
