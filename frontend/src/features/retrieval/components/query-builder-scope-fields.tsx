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
      help: "Narrows evidence to a clinical data area such as laboratory, medication, or observation.",
      helpLabel: "Clinical domain help",
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
      help: "Narrows evidence to a terminology or data standard such as UCUM, LOINC, SNOMED, or FHIR when available.",
      helpLabel: "Standard filter help",
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
      help: "Controls source trust level. Approved is safer for governed workflows; broader trust may help exploration.",
      helpLabel: "Trust filter help",
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
      help: "Narrows evidence by source class, such as schema, terminology, policy, corpus document, or locator.",
      helpLabel: "Source type filter help",
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
