import type {
  RetrievalSearchCockpitView,
} from "../model/retrieval-cockpit-view-model";
import {
  QueryHealthPanel,
  SearchReadinessChecklist,
} from "./search-cockpit-panels";
import {
  SearchCockpitMetricGrid,
  SearchCockpitNextBestAction,
  SearchCockpitQueryTransformation,
} from "./search-cockpit-insights";
import { SourceDiversityPanel } from "./source-diversity-panel";
import {
  StandardSearchPlanPanel,
  StrategyRecommendationsPanel,
  type SearchPlanFilterAction,
  type SearchPlanFilterField,
} from "./strategy-standard-panels";

export type SearchCockpitSectionStackProps = {
  filterFieldLabel: (field: SearchPlanFilterField) => string;
  getSuggestedFilterAction: (value: unknown) => SearchPlanFilterAction | null;
  isSearchPending: boolean;
  onApplyFilter: (field: SearchPlanFilterField, value: string) => void;
  onClearAllFilters: () => void;
  onClearSourceScope: () => void;
  view: RetrievalSearchCockpitView;
};

export function SearchCockpitSectionStack({
  filterFieldLabel,
  getSuggestedFilterAction,
  isSearchPending,
  onApplyFilter,
  onClearAllFilters,
  onClearSourceScope,
  view,
}: SearchCockpitSectionStackProps) {
  return (
    <>
      <QueryHealthPanel
        activeFilters={view.activeFilters}
        isSearchPending={isSearchPending}
        items={view.queryHealth}
        onClearAllFilters={onClearAllFilters}
        onClearSourceScope={onClearSourceScope}
      />

      <SearchReadinessChecklist items={view.readinessChecklist} />

      <SearchCockpitMetricGrid view={view} />

      <StrategyRecommendationsPanel
        getSuggestedFilterAction={getSuggestedFilterAction}
        isSearchPending={isSearchPending}
        onApplyFilter={onApplyFilter}
        recommendations={view.strategyRecommendations}
      />

      <StandardSearchPlanPanel
        getSuggestedFilterAction={getSuggestedFilterAction}
        isSearchPending={isSearchPending}
        onApplyFilter={onApplyFilter}
        plan={view.standardSearchPlan}
      />

      <SourceDiversityPanel diversity={view.diversity} isSearchPending={isSearchPending} />

      <div className="grid gap-3 xl:grid-cols-[minmax(0,1fr)_minmax(320px,0.75fr)]">
        <SearchCockpitQueryTransformation view={view} />
        <SearchCockpitNextBestAction
          filterFieldLabel={filterFieldLabel}
          isSearchPending={isSearchPending}
          onApplyFilter={onApplyFilter}
          onClearAllFilters={onClearAllFilters}
          onClearSourceScope={onClearSourceScope}
          view={view}
        />
      </div>
    </>
  );
}
