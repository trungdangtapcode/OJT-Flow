import { humanize } from "../../../lib/utils";
import { TokenList } from "./token-list";

export function QueryAnalysisTokenSections({
  detectedConcepts,
  expandedTerms,
  standards,
}: {
  detectedConcepts: string[];
  expandedTerms: string[];
  standards: string[];
}) {
  return (
    <>
      <TokenList items={detectedConcepts.map(humanize)} title="Detected concepts" />
      <TokenList items={standards} title="Standard cues" />
      <TokenList items={expandedTerms} title="Expanded terms" />
    </>
  );
}
