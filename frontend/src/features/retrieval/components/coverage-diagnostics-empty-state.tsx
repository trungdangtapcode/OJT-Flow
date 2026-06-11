import { TokenList } from "./token-list";

export function CoverageDiagnosticsEmptyState() {
  return (
    <TokenList
      description="No missing standard or search-aspect coverage was reported."
      items={[]}
      title="Coverage diagnostics"
    />
  );
}
