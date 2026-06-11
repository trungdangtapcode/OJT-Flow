import * as React from "react";
import { useNavigate } from "@tanstack/react-router";
import { FileCode, FileUp, Loader2, Play } from "lucide-react";

import { PageHeader } from "../../components/layout/page-header";
import { Button } from "../../components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { Input, Label, Select, Textarea } from "../../components/ui/form";
import { GuideGrid, GuideItem, GuidePanel } from "../../components/ui/guide-panel";
import { HelpTooltip } from "../../components/ui/help-tooltip";
import { Notice } from "../../components/ui/notice";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../components/ui/tabs";
import {
  useCreateWorkflowMutation,
  useExtractorInventoryQuery,
  useRuntimeConfigQuery,
  useSchemasQuery,
  useUploadWorkflowMutation,
  workflowErrorMessage,
  workflowErrorWorkflowId,
} from "../../lib/server-state";
import {
  InputExampleSelector,
  ReviewGateControl,
  SharedWorkflowOptions,
  WorkbenchControlPlane,
  WorkbenchExecutionPath,
  WorkbenchPayloadStandards,
  WorkbenchSummaryStrip,
  WorkflowStartError,
} from "./workbench-controls";
import { inputExamples, type InputExample } from "./workbench-examples";
import { OcrEvidencePanel } from "./ocr-evidence-panel";
import { formatBytes, sourceDataStats, validateUploadFile } from "./workbench-utils";

export function WorkbenchPage() {
  const navigate = useNavigate();
  const schemasQuery = useSchemasQuery();
  const extractorsQuery = useExtractorInventoryQuery();
  const runtimeConfigQuery = useRuntimeConfigQuery();
  const createWorkflow = useCreateWorkflowMutation();
  const uploadWorkflow = useUploadWorkflowMutation();
  const [instruction, setInstruction] = React.useState(
    "Clean this CSV, convert it to JSON, and explain anomalies.",
  );
  const [uploadInstruction, setUploadInstruction] = React.useState(
    "Extract this file, convert relevant healthcare data to JSON, and explain anomalies.",
  );
  const [data, setData] = React.useState("");
  const [inputFormat, setInputFormat] = React.useState("csv");
  const [targetFormat, setTargetFormat] = React.useState("json");
  const [schemaId, setSchemaId] = React.useState("lab_result_v1");
  const [selectedExampleId, setSelectedExampleId] = React.useState("");
  const [intakeMode, setIntakeMode] = React.useState("paste");
  const [requireReview, setRequireReview] = React.useState(true);
  const [extractor, setExtractor] = React.useState("auto");
  const [file, setFile] = React.useState<File | null>(null);
  const [createFormError, setCreateFormError] = React.useState<string | null>(null);
  const [fileError, setFileError] = React.useState<string | null>(null);
  const [uploadFormError, setUploadFormError] = React.useState<string | null>(null);

  const runtimeUpload = runtimeConfigQuery.data?.upload;
  const uploadExtensions =
    runtimeUpload?.allowed_extensions ?? extractorsQuery.data?.supported_extensions ?? [];
  const uploadExtensionKey = uploadExtensions.join(",");
  const acceptedUploadExtensions = uploadExtensions.join(",");
  const maxUploadBytes = runtimeUpload?.max_upload_bytes ?? null;
  const availableExtractors = extractorsQuery.data?.available ?? [];
  const noMockData = Boolean(runtimeConfigQuery.data?.policy.effective_no_mock_data);
  const availableInputExamples = noMockData ? [] : inputExamples;
  const selectedExample =
    availableInputExamples.find((example) => example.id === selectedExampleId) ??
    availableInputExamples[0] ??
    null;
  const failedCreateWorkflowId = workflowErrorWorkflowId(createWorkflow.error);
  const failedUploadWorkflowId = workflowErrorWorkflowId(uploadWorkflow.error);
  const dataStats = sourceDataStats(data);
  const activeSourceFormat = intakeMode === "upload" ? "auto" : inputFormat;
  const activeSchema =
    schemaId || (selectedExample?.standard ? `${selectedExample.standard} profile` : "none");
  const activeContractSchema = schemaId || selectedExample?.standard || "no schema";

  React.useEffect(() => {
    if (!file) return;
    setFileError(validateUploadFile(file, uploadExtensions, maxUploadBytes));
  }, [file, maxUploadBytes, uploadExtensionKey]);

  React.useEffect(() => {
    if (!noMockData) return;
    setSelectedExampleId("");
    setData((current) =>
      inputExamples.some((example) => example.data === current) ? "" : current,
    );
  }, [noMockData]);

  const applyInputExample = (example: InputExample) => {
    setSelectedExampleId(example.id);
    setInstruction(example.instruction);
    setData(example.data);
    setInputFormat(example.inputFormat);
    setTargetFormat(example.targetFormat);
    setSchemaId(example.schemaId);
  };

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    const normalizedInstruction = instruction.trim();
    if (!normalizedInstruction) {
      setCreateFormError("Enter a workflow instruction before starting.");
      return;
    }
    if (!data.trim()) {
      setCreateFormError("Enter source data before starting a workflow.");
      return;
    }
    setCreateFormError(null);
    try {
      const workflow = await createWorkflow.mutateAsync({
        instruction: normalizedInstruction,
        data,
        input_format: inputFormat === "auto" ? null : inputFormat,
        target_format: targetFormat,
        schema_id: schemaId || null,
        require_human_review: requireReview,
      });
      await navigate({ to: "/workflows/$workflowId", params: { workflowId: workflow.workflow_id } });
    } catch {
      // Mutation state renders the structured error.
    }
  };

  const submitUpload = async (event: React.FormEvent) => {
    event.preventDefault();
    const normalizedInstruction = uploadInstruction.trim();
    if (!normalizedInstruction) {
      setUploadFormError("Enter an upload instruction before starting a workflow.");
      return;
    }
    if (!file) {
      setUploadFormError(null);
      setFileError("Select a file before starting an upload workflow.");
      return;
    }
    const validationError = validateUploadFile(file, uploadExtensions, maxUploadBytes);
    if (validationError) {
      setUploadFormError(null);
      setFileError(validationError);
      return;
    }
    setFileError(null);
    setUploadFormError(null);
    try {
      const workflow = await uploadWorkflow.mutateAsync({
        file,
        options: {
          instruction: normalizedInstruction,
          targetFormat,
          schemaId: schemaId || null,
          requireHumanReview: requireReview,
          extractor,
        },
      });
      await navigate({ to: "/workflows/$workflowId", params: { workflowId: workflow.workflow_id } });
    } catch {
      // Mutation state renders the structured error.
    }
  };

  return (
    <div className="grid gap-5">
      <PageHeader
        title="Workbench"
        description="Create governed workflows from pasted data or uploaded healthcare files."
      />
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
      <WorkbenchSummaryStrip
        intakeMode={intakeMode}
        requireReview={requireReview}
        schemaId={activeSchema}
        sourceFormat={activeSourceFormat}
        targetFormat={targetFormat}
      />
      <div className="grid gap-5 xl:grid-cols-[minmax(420px,0.95fr)_minmax(0,1.05fr)]">
        <Card className="overflow-hidden">
          <CardHeader className="border-b border-border bg-card/70 p-4">
            <CardTitle className="flex items-center gap-2">
              <FileCode className="h-5 w-5" />
              Data intake
            </CardTitle>
            <CardDescription>Start with deterministic parsing, validation, retrieval, and review gates.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 pt-4">
            {schemasQuery.isError ? (
              <Notice title="Schemas could not be loaded" tone="danger">
                {workflowErrorMessage(schemasQuery.error)}
              </Notice>
            ) : null}
            {extractorsQuery.isError ? (
              <Notice title="Extractor inventory could not be loaded" tone="danger">
                {workflowErrorMessage(extractorsQuery.error)}
              </Notice>
            ) : null}
            <Tabs value={intakeMode} onValueChange={setIntakeMode}>
              <TabsList className="grid w-full grid-cols-2 sm:inline-flex sm:w-auto">
                <TabsTrigger value="paste">Paste Data</TabsTrigger>
                <TabsTrigger value="upload">Upload File</TabsTrigger>
              </TabsList>
              <TabsContent value="paste">
                <form className="grid gap-4" onSubmit={(event) => void submit(event)}>
                  {createWorkflow.isError ? (
                    <Notice title="Workflow could not be started" tone="danger">
                      <WorkflowStartError
                        message={workflowErrorMessage(createWorkflow.error)}
                        workflowId={failedCreateWorkflowId}
                        onOpenWorkflow={(workflowId) =>
                          void navigate({
                            to: "/workflows/$workflowId",
                            params: { workflowId },
                          })
                        }
                      />
                    </Notice>
                  ) : null}
                  {createFormError ? (
                    <Notice title="Workflow request blocked" tone="danger">
                      {createFormError}
                    </Notice>
                  ) : null}
                  {noMockData ? (
                    <Notice title="Sample data is disabled" tone="neutral">
                      This environment blocks demo fixtures. Paste real permitted data or upload an
                      approved file to start a workflow.
                    </Notice>
                  ) : (
                    <InputExampleSelector
                      examples={availableInputExamples}
                      selectedExampleId={selectedExampleId}
                      onSelect={applyInputExample}
                    />
                  )}
                  <Label>
                    <span className="inline-flex items-center gap-1.5">
                      Instruction
                      <HelpTooltip label="Workflow instruction help">
                        Describe the operational task, not a clinical decision. Example: validate this lab CSV, convert it to JSON, and explain missing units with trusted evidence.
                      </HelpTooltip>
                    </span>
                    <Textarea
                      className="min-h-20 resize-y"
                      value={instruction}
                      onChange={(event) => {
                        setInstruction(event.target.value);
                        if (createFormError) setCreateFormError(null);
                      }}
                    />
                  </Label>
                  <SharedWorkflowOptions
                    inputFormat={inputFormat}
                    schemaId={schemaId}
                    schemas={schemasQuery.data ?? []}
                    setInputFormat={setInputFormat}
                    setSchemaId={setSchemaId}
                    setTargetFormat={setTargetFormat}
                    targetFormat={targetFormat}
                  />
                  <ReviewGateControl checked={requireReview} onCheckedChange={setRequireReview} />
                  <div className="grid gap-2">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="text-sm font-extrabold">Source data</div>
                      <HelpTooltip label="Source data help">
                        Paste CSV, JSON, or YAML here. Keep patient identifiers only when required for the workflow and keep the review gate on for sensitive data.
                      </HelpTooltip>
                      <div className="flex flex-wrap gap-2 text-[11px] font-bold uppercase text-muted-foreground">
                        <span className="rounded-full bg-muted px-2 py-0.5">{dataStats.lines} lines</span>
                        <span className="rounded-full bg-muted px-2 py-0.5">{formatBytes(dataStats.bytes)}</span>
                      </div>
                    </div>
                    <Label className="gap-1">
                      <Textarea
                        aria-label="Source data"
                        className="min-h-[220px] resize-y font-mono text-xs md:min-h-[260px]"
                        value={data}
                        onChange={(event) => {
                          setData(event.target.value);
                          if (createFormError) setCreateFormError(null);
                        }}
                      />
                    </Label>
                  </div>
                  <Button disabled={createWorkflow.isPending} type="submit">
                    {createWorkflow.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Play className="h-4 w-4" />
                    )}
                    Start workflow
                  </Button>
                </form>
              </TabsContent>
              <TabsContent value="upload">
                <form className="grid gap-4" onSubmit={(event) => void submitUpload(event)}>
                  {uploadWorkflow.isError ? (
                    <Notice title="Upload workflow could not be started" tone="danger">
                      <WorkflowStartError
                        message={workflowErrorMessage(uploadWorkflow.error)}
                        workflowId={failedUploadWorkflowId}
                        onOpenWorkflow={(workflowId) =>
                          void navigate({
                            to: "/workflows/$workflowId",
                            params: { workflowId },
                          })
                        }
                      />
                    </Notice>
                  ) : null}
                  {fileError ? (
                    <Notice title="Upload file blocked" tone="danger">
                      {fileError}
                    </Notice>
                  ) : null}
                  {uploadFormError ? (
                    <Notice title="Upload request blocked" tone="danger">
                      {uploadFormError}
                    </Notice>
                  ) : null}
                  <Label>
                    <span className="inline-flex items-center gap-1.5">
                      Instruction
                      <HelpTooltip label="Upload instruction help">
                        Tell the backend what to extract and how to validate it. Extraction warnings mean the file text may be incomplete.
                      </HelpTooltip>
                    </span>
                    <Textarea
                      className="min-h-20 resize-y"
                      value={uploadInstruction}
                      onChange={(event) => {
                        setUploadInstruction(event.target.value);
                        if (uploadFormError) setUploadFormError(null);
                      }}
                    />
                  </Label>
                  <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_180px]">
                    <Label>
                      <span className="inline-flex items-center gap-1.5">
                        File
                        <HelpTooltip label="Upload file help">
                          Supported extensions come from runtime config. Scanned PDFs and images may need OCR fallback and human review before trusting extracted text.
                        </HelpTooltip>
                      </span>
                      <Input
                        accept={acceptedUploadExtensions}
                        onChange={(event) => {
                          const nextFile = event.target.files?.[0] ?? null;
                          setFile(nextFile);
                          setFileError(
                            nextFile
                              ? validateUploadFile(nextFile, uploadExtensions, maxUploadBytes)
                              : null,
                          );
                        }}
                        type="file"
                      />
                    </Label>
                    <Label>
                      <span className="inline-flex items-center gap-1.5">
                        Extractor
                        <HelpTooltip label="Extractor help">
                          Auto lets the backend choose the best available extractor. Pick a specific extractor only when comparing document parsing behavior.
                        </HelpTooltip>
                      </span>
                      <Select value={extractor} onChange={(event) => setExtractor(event.target.value)}>
                        <option value="auto">Auto</option>
                        <option disabled={!availableExtractors.includes("markitdown")} value="markitdown">
                          MarkItDown
                        </option>
                        <option disabled={!availableExtractors.includes("mineru")} value="mineru">
                          MinerU
                        </option>
                      </Select>
                    </Label>
                  </div>
                  {file ? (
                    <div className="rounded-md border border-border bg-muted/40 p-3 text-sm">
                      <div className="font-bold">{file.name}</div>
                      <div className="text-muted-foreground">
                        {formatBytes(file.size)}
                        {maxUploadBytes ? ` / ${formatBytes(maxUploadBytes)} max` : ""}
                      </div>
                    </div>
                  ) : null}
                  <SharedWorkflowOptions
                    inputFormat="auto"
                    schemaId={schemaId}
                    schemas={schemasQuery.data ?? []}
                    sourceDisabled
                    setInputFormat={() => undefined}
                    setSchemaId={setSchemaId}
                    setTargetFormat={setTargetFormat}
                    targetFormat={targetFormat}
                  />
                  <ReviewGateControl checked={requireReview} onCheckedChange={setRequireReview} />
                  <Button disabled={uploadWorkflow.isPending || Boolean(fileError)} type="submit">
                    {uploadWorkflow.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <FileUp className="h-4 w-4" />
                    )}
                    Upload and start workflow
                  </Button>
                </form>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
        <div className="grid content-start gap-4">
          <WorkbenchControlPlane
            activeContractSchema={activeContractSchema}
            fields={selectedExample.fields}
            intakeMode={intakeMode}
            requireReview={requireReview}
            sourceFormat={activeSourceFormat}
            targetFormat={targetFormat}
          />
          <WorkbenchExecutionPath />
          <OcrEvidencePanel />
          <WorkbenchPayloadStandards />
        </div>
      </div>
    </div>
  );
}
