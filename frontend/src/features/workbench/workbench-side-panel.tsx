import { GuideGrid, GuideItem, GuidePanel } from "../../components/ui/guide-panel";
import {
  WorkbenchControlPlane,
  WorkbenchExecutionPath,
  WorkbenchPayloadStandards,
} from "./workbench-controls";
import { OcrEvidencePanel } from "./ocr-evidence-panel";

export function WorkbenchQuickGuide() {
  return (
    <GuidePanel title="How to create a workflow">
      <GuideGrid>
        <GuideItem title="1. Choose intake">
          Paste structured data for quick validation, or upload a file when extraction is needed first.
        </GuideItem>
        <GuideItem title="2. Pick the contract">
          Set input format, target format, schema, and review gate before starting the run.
        </GuideItem>
        <GuideItem title="3. Inspect the result">
          After start, open Workflow detail to read validation issues, evidence, output, and audit events.
        </GuideItem>
      </GuideGrid>
    </GuidePanel>
  );
}

export function WorkbenchSidePanel({
  activeContractSchema,
  fields,
  intakeMode,
  requireReview,
  sourceFormat,
  targetFormat,
}: {
  activeContractSchema: string;
  fields: string[];
  intakeMode: string;
  requireReview: boolean;
  sourceFormat: string;
  targetFormat: string;
}) {
  return (
    <div className="grid content-start gap-4">
      <WorkbenchControlPlane
        activeContractSchema={activeContractSchema}
        fields={fields}
        intakeMode={intakeMode}
        requireReview={requireReview}
        sourceFormat={sourceFormat}
        targetFormat={targetFormat}
      />
      <WorkbenchExecutionPath />
      <OcrEvidencePanel />
      <WorkbenchPayloadStandards />
    </div>
  );
}
