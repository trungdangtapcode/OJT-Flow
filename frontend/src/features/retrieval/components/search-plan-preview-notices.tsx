import { Notice } from "../../../components/ui/notice";

export function SearchPlanPreviewNotices({
  isPlanLoading,
  isSearchPending,
  planError,
  showPlanningNotice,
}: {
  isPlanLoading: boolean;
  isSearchPending: boolean;
  planError: string | null;
  showPlanningNotice: boolean;
}) {
  return (
    <>
      {isPlanLoading && showPlanningNotice ? (
        <Notice title="Planning search">
          Updating route, aspects, and medical search hints from the current query.
        </Notice>
      ) : null}
      {planError ? (
        <Notice title="Search plan unavailable" tone="danger">
          {planError}
        </Notice>
      ) : null}
      {isSearchPending ? (
        <Notice title="Search running">
          The current results may be updating. Wait for completion before using this plan for review notes.
        </Notice>
      ) : null}
    </>
  );
}
