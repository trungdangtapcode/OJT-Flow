import { humanize } from "../../../lib/utils";
import type {
  RetrievalQueryBuilderActions,
  RetrievalQueryBuilderOptions,
  RetrievalQueryBuilderValue,
} from "./query-builder-panel-types";
import { QueryBuilderScopeSelect } from "./query-builder-scope-select";

export function QueryBuilderScopeFields({
  actions,
  options,
  value,
}: {
  actions: RetrievalQueryBuilderActions;
  options: RetrievalQueryBuilderOptions;
  value: RetrievalQueryBuilderValue;
}) {
  const fields = [
    {
      help: "Filter by clinical area",
      helpLabel: "Domain help",
      label: "Domain",
      onChange: actions.onSetClinicalDomain,
      options: options.domainOptions.map((domain) => ({
        label: humanize(domain),
        value: domain,
      })),
      placeholder: "Any domain",
      value: value.clinicalDomain,
    },
    {
      help: "Filter by standard (UCUM, LOINC, etc.)",
      helpLabel: "Standard help",
      label: "Standard",
      onChange: actions.onSetStandardSystem,
      options: options.standardOptions.map((standard) => ({
        label: standard,
        value: standard,
      })),
      placeholder: "Any standard",
      value: value.standardSystem,
    },
    {
      help: "Filter by source trust level",
      helpLabel: "Trust help",
      label: "Trust",
      onChange: actions.onSetTrustLevel,
      options: options.trustOptions.map((trust) => ({
        label: humanize(trust),
        value: trust,
      })),
      placeholder: "Any trust",
      value: value.trustLevel,
    },
    {
      help: "Filter by source type",
      helpLabel: "Source type help",
      label: "Source type",
      onChange: actions.onSetSourceType,
      options: options.sourceTypeOptions.map((type) => ({
        label: humanize(type),
        value: type,
      })),
      placeholder: "Any source",
      value: value.sourceType,
    },
  ];

  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {fields.map((field) => (
        <QueryBuilderScopeSelect key={field.label} {...field} />
      ))}
    </div>
  );
}
