import { SectionHelpText } from "./section-help-text";

export function JudgmentEvaluationHelp() {
  return (
    <SectionHelpText>
      Label top hits as relevant, partial, or not relevant. Coverage shows how much of the result set has labels; Precision@k and nDCG@k become meaningful only after enough judgments exist.
    </SectionHelpText>
  );
}
