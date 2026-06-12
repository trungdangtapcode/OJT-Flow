import { Notice } from "../../../components/ui/notice";

export function QueryBuilderNotices({
  formError,
  planControlNotice,
  presetsError,
  searchError,
  searchOptionsError,
  isSearchResultStale,
}: {
  formError: string | null;
  planControlNotice: string | null;
  presetsError: string | null;
  searchError: string | null;
  searchOptionsError: string | null;
  isSearchResultStale: boolean;
}) {
  return (
    <>
      {formError ? (
        <Notice title="Search blocked" tone="danger">
          {formError}
        </Notice>
      ) : null}
      {searchError ? (
        <Notice title="Search request failed" tone="danger">
          {searchError}
        </Notice>
      ) : null}
      {presetsError ? (
        <Notice title="Search presets unavailable">{presetsError}</Notice>
      ) : null}
      {searchOptionsError ? (
        <Notice title="Search options unavailable">{searchOptionsError}</Notice>
      ) : null}
      {planControlNotice ? (
        <Notice title="Plan filter applied">{planControlNotice}</Notice>
      ) : null}
      {isSearchResultStale ? (
        <Notice title="Search settings changed">
          Run search to refresh ranked evidence with the current query builder state.
        </Notice>
      ) : null}
    </>
  );
}
