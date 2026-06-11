import { humanize } from "../../../lib/utils";
import type {
  RetrievalHit,
  RetrievalScoreComponent,
} from "../../../types";
import {
  numberValue,
  recordValue,
  stringValue,
} from "./retrieval-evidence-utils";

export function scoreComponentsFromHit(hit: RetrievalHit): RetrievalScoreComponent[] {
  return (hit.score_components ?? [])
    .map((component) => ({
      component: stringValue(component.component, ""),
      description: stringValue(
        component.description,
        "Score component contribution.",
      ),
      label: stringValue(component.label, humanize(component.component)),
      metadata: recordValue(component.metadata),
      rank: typeof component.rank === "number" ? component.rank : null,
      value: numberValue(component.value) ?? 0,
    }))
    .filter((component) => component.component);
}
