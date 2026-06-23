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
      {formError ? <Notice title="Blocked" tone="danger">{formError}</Notice> : null}
      {searchError ? <Notice title="Error" tone="danger">{searchError}</Notice> : null}
      {presetsError ? <Notice title="Presets unavailable">{presetsError}</Notice> : null}
      {searchOptionsError ? <Notice title="Options unavailable">{searchOptionsError}</Notice> : null}
      {planControlNotice ? <Notice title="Filter applied">{planControlNotice}</Notice> : null}
      {isSearchResultStale ? <Notice title="Stale results">Re-run search to refresh.</Notice> : null}
    </>
  );
}
