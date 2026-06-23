import {
  hasSearchHintMetadataDetails,
  searchHintMetadataView,
} from "./search-hint-metadata";
import { SearchHintMetadataSectionList } from "./search-hint-metadata-section-list";
import { SearchHintMetadataSummary } from "./search-hint-metadata-summary";

export function SearchHintMetadata({ metadata }: { metadata: Record<string, unknown> }) {
  const view = searchHintMetadataView(metadata);
  if (!hasSearchHintMetadataDetails(view)) return null;
  return (
    <details className="rounded-lg border border-border/60 bg-muted/20">
      <SearchHintMetadataSummary view={view} />
      <SearchHintMetadataSectionList view={view} />
    </details>
  );
}
