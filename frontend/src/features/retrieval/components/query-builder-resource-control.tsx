import { Input, Label } from "../../../components/ui/form";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import type { QueryBuilderContextControlProps } from "./query-builder-context-control-types";

export function QueryBuilderResourceControl({
  actions,
  value,
}: QueryBuilderContextControlProps) {
  return (
    <Label>
      <span className="inline-flex items-center gap-1.5">
        Resource
        <HelpTooltip label="Resource filter help">
          Optional healthcare resource type, for example Observation. Useful for FHIR-like mapping questions.
        </HelpTooltip>
      </span>
      <Input
        onChange={(event) => actions.onSetResourceType(event.target.value)}
        placeholder="Observation"
        value={value.resourceType}
      />
    </Label>
  );
}
