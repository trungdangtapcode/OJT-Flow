import { RetrievalPageChrome } from "./components/retrieval-page-chrome";
import { RetrievalSearchTab } from "./components/retrieval-search-tab";
import { RetrievalAnalysisTab } from "./components/retrieval-analysis-tab";
import { RetrievalSourcesTab } from "./components/retrieval-sources-tab";
import { RetrievalHistoryTab } from "./components/retrieval-history-tab";
import { useRetrievalPageController } from "./hooks/use-retrieval-page-controller";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../components/ui/tabs";
import { Search, BarChart3, Database, History } from "lucide-react";

export function RetrievalPage() {
  const { chrome, queryColumn, resultsColumn } = useRetrievalPageController();

  return (
    <div className="grid gap-3">
      <RetrievalPageChrome {...chrome} />

      <Tabs defaultValue="search">
        <TabsList>
          <TabsTrigger value="search">
            <Search className="mr-1.5 h-3.5 w-3.5" />
            Search
          </TabsTrigger>
          <TabsTrigger value="analysis">
            <BarChart3 className="mr-1.5 h-3.5 w-3.5" />
            Trace
          </TabsTrigger>
          <TabsTrigger value="sources">
            <Database className="mr-1.5 h-3.5 w-3.5" />
            Sources
          </TabsTrigger>
          <TabsTrigger value="history">
            <History className="mr-1.5 h-3.5 w-3.5" />
            Runs
          </TabsTrigger>
        </TabsList>

        <TabsContent value="search">
          <RetrievalSearchTab queryColumn={queryColumn} resultsColumn={resultsColumn} />
        </TabsContent>

        <TabsContent value="analysis">
          <RetrievalAnalysisTab resultsColumn={resultsColumn} />
        </TabsContent>

        <TabsContent value="sources">
          <RetrievalSourcesTab resultsColumn={resultsColumn} />
        </TabsContent>

        <TabsContent value="history">
          <RetrievalHistoryTab queryColumn={queryColumn} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
