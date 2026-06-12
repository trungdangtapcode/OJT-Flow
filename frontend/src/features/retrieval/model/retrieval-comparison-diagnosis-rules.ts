import type {
  RetrievalComparisonDiagnosis,
  RetrievalComparisonDiagnosticInput,
} from "./retrieval-comparison-types";
import { comparisonProfileDiagnosis } from "./retrieval-comparison-diagnosis-profile-rules";
import { comparisonQualityDiagnosis } from "./retrieval-comparison-diagnosis-quality-rules";
import { comparisonSourceDiagnosis } from "./retrieval-comparison-diagnosis-source-rules";
import { comparisonStableDiagnosis } from "./retrieval-comparison-diagnosis-stability";

export function comparisonDiagnosisFromComparison(
  comparison: RetrievalComparisonDiagnosticInput,
): RetrievalComparisonDiagnosis[] {
  return comparisonStableDiagnosis([
    ...comparisonProfileDiagnosis(comparison),
    ...comparisonQualityDiagnosis(comparison),
    ...comparisonSourceDiagnosis(comparison),
  ]);
}
