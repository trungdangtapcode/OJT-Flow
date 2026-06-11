import { humanize } from "../../../lib/utils";
import type { RetrievalFacets } from "../../../types";
import type { ResultFacetSection } from "./result-facet-types";

export function resultFacetSections(
  facets: RetrievalFacets | null | undefined,
): ResultFacetSection[] {
  if (!facets) return [];
  const sections: ResultFacetSection[] = [
    { field: "source_type", label: "Source type", values: facets.source_type, formatter: humanize },
    { field: "clinical_domain", label: "Domain", values: facets.clinical_domain, formatter: humanize },
    { field: "standard_system", label: "Standard", values: facets.standard_system, formatter: (value: string) => value },
    { field: "trust_level", label: "Trust", values: facets.trust_level, formatter: humanize },
  ];
  return sections.filter((section) => section.values.length > 0);
}
