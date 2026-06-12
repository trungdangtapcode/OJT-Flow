import { RetrievalPageChrome } from "./components/retrieval-page-chrome";
import { RetrievalQueryColumn } from "./components/retrieval-query-column";
import { RetrievalResultsColumn } from "./components/retrieval-results-column";
import { useRetrievalPageController } from "./hooks/use-retrieval-page-controller";

export function RetrievalPage() {
  const { chrome, queryColumn, resultsColumn } = useRetrievalPageController();

  return (
    <div className="grid gap-5">
      <RetrievalPageChrome {...chrome} />

      <div className="grid gap-5 xl:grid-cols-[minmax(360px,0.72fr)_minmax(0,1.28fr)]">
        <RetrievalQueryColumn {...queryColumn} />
        <RetrievalResultsColumn {...resultsColumn} />
      </div>
    </div>
  );
}
