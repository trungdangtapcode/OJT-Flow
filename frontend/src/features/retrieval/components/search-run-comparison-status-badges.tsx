import { Badge } from "../../../components/ui/badge";

export function SearchRunComparisonStatusBadges({
  qualitySummaryChanged,
  queryProfileChanged,
  rulePackChanged,
  topSourceChanged,
}: {
  qualitySummaryChanged: boolean;
  queryProfileChanged: boolean;
  rulePackChanged: boolean;
  topSourceChanged: boolean;
}) {
  return (
    <>
      <Badge variant={topSourceChanged ? "warning" : "success"}>
        {topSourceChanged ? "top source changed" : "top source stable"}
      </Badge>
      <Badge variant={queryProfileChanged ? "warning" : "success"}>
        {queryProfileChanged ? "profile changed" : "profile stable"}
      </Badge>
      <Badge variant={rulePackChanged ? "warning" : "success"}>
        {rulePackChanged ? "rule packs changed" : "rule packs stable"}
      </Badge>
      <Badge variant={qualitySummaryChanged ? "warning" : "success"}>
        {qualitySummaryChanged ? "quality changed" : "quality stable"}
      </Badge>
    </>
  );
}
