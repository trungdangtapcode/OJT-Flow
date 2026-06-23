import {
  ClipboardCheck,
  Database,
  FileCode,
  FileJson,
  FileUp,
  Rows3,
  ShieldCheck,
  type LucideIcon,
} from "lucide-react";

import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { Label, Select } from "../../components/ui/form";
import { SummaryStrip, SummaryStripItem } from "../../components/ui/summary-strip";
import type { InputExample } from "./workbench-examples";
import { humanizeWorkbenchValue } from "./workbench-utils";

const operatingModelSteps: Array<{ body: string; icon: LucideIcon; title: string }> = [
  {
    icon: FileCode,
    title: "Parse",
    body: "Detect CSV, JSON, YAML, or uploaded document text and preserve source references.",
  },
  {
    icon: Database,
    title: "Ground",
    body: "Attach trusted schema, terminology, and retrieval evidence before validation.",
  },
  {
    icon: ShieldCheck,
    title: "Validate",
    body: "Flag missing fields, PHI-like data, malformed rows, units, and date issues.",
  },
  {
    icon: ClipboardCheck,
    title: "Review",
    body: "Gate meaning-changing transformations before output is generated.",
  },
];

export function WorkbenchControlPlane({
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
    <section className="rounded-lg border border-border/60 bg-card shadow-[0_1px_2px_rgba(16,24,40,0.045)]">
      <div className="flex items-start justify-between gap-3 border-b border-border p-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2 font-extrabold">
            <ShieldCheck className="h-4 w-4 text-primary" />
            Intake control plane
          </div>
          <p className="mt-1 text-sm leading-5 text-muted-foreground">
            Contract, evidence, and review controls for the next workflow run.
          </p>
        </div>
        <Badge variant={requireReview ? "warning" : "muted"}>
          {requireReview ? "review gated" : "auto when safe"}
        </Badge>
      </div>
      <div className="grid gap-px bg-border text-sm sm:grid-cols-2">
        <ControlFact label="Mode" value={humanizeWorkbenchValue(intakeMode)} />
        <ControlFact label="Route" value={`${sourceFormat} to ${targetFormat}`} />
        <ControlFact label="Schema profile" value={activeContractSchema} />
        <ControlFact label="Evidence policy" value="retrieval before validation" />
      </div>
      <div className="grid gap-4 p-4">
        <div>
          <div className="text-xs font-bold uppercase text-muted-foreground">Active contract</div>
          <div className="mt-2 flex flex-wrap gap-2">
            <Badge variant="default">source {sourceFormat}</Badge>
            <Badge variant="default">target {targetFormat}</Badge>
            <Badge variant="success">profile {activeContractSchema}</Badge>
          </div>
        </div>
        <div>
          <div className="text-xs font-bold uppercase text-muted-foreground">Expected fields</div>
          <div className="mt-2 flex flex-wrap gap-2">
            {fields.map((field) => (
              <Badge key={field} variant="warning">
                {field}
              </Badge>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

export function WorkbenchExecutionPath() {
  return (
    <section className="rounded-lg border border-border/60 bg-card p-4 shadow-[0_1px_2px_rgba(16,24,40,0.045)]">
      <div className="flex items-center gap-2 font-extrabold">
        <FileUp className="h-4 w-4 text-primary" />
        Execution path
      </div>
      <ol className="mt-4 grid gap-3 sm:grid-cols-2">
        {operatingModelSteps.map(({ body, icon: Icon, title }, index) => (
          <li className="grid grid-cols-[32px_minmax(0,1fr)] gap-3" key={title}>
            <span className="flex h-8 w-8 items-center justify-center rounded-md bg-muted text-primary">
              <Icon className="h-4 w-4" />
            </span>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] font-bold text-muted-foreground">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <h3 className="text-sm font-extrabold">{title}</h3>
              </div>
              <p className="mt-1 text-xs leading-5 text-muted-foreground">{body}</p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}

export function WorkbenchPayloadStandards() {
  return (
    <section className="rounded-md border border-blue-200 bg-blue-50 p-4 text-blue-950 shadow-[0_1px_2px_rgba(16,24,40,0.04)]">
      <div className="flex items-center gap-2 font-extrabold">
        <FileJson className="h-4 w-4" />
        Standard payloads
      </div>
      <div className="mt-3 grid gap-3 text-sm sm:grid-cols-2">
        <PayloadStandard label="Structured intake" value="CSV, JSON arrays, YAML lists, FHIR-like JSON" />
        <PayloadStandard label="Document intake" value="Plain text, Markdown, and supported file uploads" />
      </div>
    </section>
  );
}

export function WorkbenchSummaryStrip({
  intakeMode,
  requireReview,
  schemaId,
  sourceFormat,
  targetFormat,
}: {
  intakeMode: string;
  requireReview: boolean;
  schemaId: string;
  sourceFormat: string;
  targetFormat: string;
}) {
  return (
    <SummaryStrip>
      <SummaryStripItem
        icon={FileCode}
        label="Intake mode"
        supporting="Current workflow entry"
        tone="neutral"
        value={humanizeWorkbenchValue(intakeMode)}
      />
      <SummaryStripItem
        icon={Rows3}
        label="Format route"
        supporting={`from ${sourceFormat}`}
        tone="info"
        value={`to ${targetFormat}`}
      />
      <SummaryStripItem
        icon={Database}
        label="Schema"
        supporting="Validation profile"
        tone={schemaId === "none" ? "warning" : "success"}
        value={schemaId}
      />
      <SummaryStripItem
        icon={ShieldCheck}
        label="Review gate"
        supporting="Meaning-changing actions"
        tone={requireReview ? "warning" : "neutral"}
        value={requireReview ? "enabled" : "off"}
      />
    </SummaryStrip>
  );
}

export function ReviewGateControl({
  checked,
  onCheckedChange,
}: {
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
}) {
  return (
    <label className="grid cursor-pointer gap-2 rounded-lg border border-border/60 bg-card p-3 transition-colors hover:border-primary/40">
      <div className="flex min-w-0 items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="font-extrabold">Human review</div>
          <p className="mt-1 text-sm leading-5 text-muted-foreground">
            Require approval before meaning-changing transformations create output.
          </p>
        </div>
        <input
          checked={checked}
          className="mt-1 h-4 w-4 shrink-0 accent-primary"
          onChange={(event) => onCheckedChange(event.target.checked)}
          type="checkbox"
        />
      </div>
      <div className="flex flex-wrap gap-2">
        <Badge variant={checked ? "warning" : "muted"}>
          {checked ? "review required" : "automatic when safe"}
        </Badge>
        <Badge variant="muted">audit logged</Badge>
      </div>
    </label>
  );
}

export function WorkflowStartError({
  message,
  onOpenWorkflow,
  workflowId,
}: {
  message: string;
  onOpenWorkflow: (workflowId: string) => void;
  workflowId: string | null;
}) {
  return (
    <div className="grid gap-3" data-testid="workflow-start-error">
      <p>{message}</p>
      {workflowId ? (
        <div>
          <Button
            data-testid="open-failed-workflow"
            onClick={() => onOpenWorkflow(workflowId)}
            size="sm"
            type="button"
            variant="outline"
          >
            Open failed workflow
          </Button>
        </div>
      ) : null}
    </div>
  );
}

export function InputExampleSelector({
  examples,
  onSelect,
  selectedExampleId,
}: {
  examples: InputExample[];
  onSelect: (example: InputExample) => void;
  selectedExampleId: string;
}) {
  return (
    <div className="grid gap-2">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <div className="text-sm font-extrabold">Standard examples</div>
          <div className="text-xs text-muted-foreground">
            Schema-aligned records for the healthcare workflow scope.
          </div>
        </div>
        <Badge variant="muted">lab_result_v1</Badge>
      </div>
      <div className="grid gap-2 sm:grid-cols-2">
        {examples.map((example) => (
          <button
            className={
              example.id === selectedExampleId
                ? "rounded-lg border border-primary/30 bg-primary/[0.04] px-3 py-2 text-left text-sm font-bold text-primary shadow-[inset_3px_0_0_theme(--color-primary)] focus-ring"
                : "rounded-lg border border-border/60 bg-muted/20 px-3 py-2 text-left text-sm font-bold text-foreground transition-colors hover:bg-muted/50 focus-ring"
            }
            key={example.id}
            onClick={() => onSelect(example)}
            type="button"
          >
            <span>{example.label}</span>
            <span className="mt-1 block text-xs font-semibold text-muted-foreground">
              {example.inputFormat} to {example.targetFormat}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}

export function SharedWorkflowOptions({
  inputFormat,
  schemaId,
  schemas,
  setInputFormat,
  setSchemaId,
  setTargetFormat,
  sourceDisabled = false,
  targetFormat,
}: {
  inputFormat: string;
  schemaId: string;
  schemas: Array<{ schema_id: string }>;
  setInputFormat: (value: string) => void;
  setSchemaId: (value: string) => void;
  setTargetFormat: (value: string) => void;
  sourceDisabled?: boolean;
  targetFormat: string;
}) {
  return (
    <div className="grid gap-3 md:grid-cols-3">
      <Label>
        Source
        <Select
          aria-label="Source format"
          disabled={sourceDisabled}
          value={inputFormat}
          onChange={(event) => setInputFormat(event.target.value)}
        >
          <option value="auto">Auto</option>
          <option value="csv">CSV</option>
          <option value="json">JSON</option>
          <option value="yaml">YAML</option>
        </Select>
      </Label>
      <Label>
        Target
        <Select
          aria-label="Target format"
          value={targetFormat}
          onChange={(event) => setTargetFormat(event.target.value)}
        >
          <option value="json">JSON</option>
          <option value="yaml">YAML</option>
          <option value="csv">CSV</option>
        </Select>
      </Label>
      <Label>
        Schema
        <Select
          aria-label="Schema profile"
          value={schemaId}
          onChange={(event) => setSchemaId(event.target.value)}
        >
          <option value="">No schema</option>
          {schemas.map((schema) => (
            <option key={schema.schema_id} value={schema.schema_id}>
              {schema.schema_id}
            </option>
          ))}
        </Select>
      </Label>
    </div>
  );
}

function ControlFact({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 bg-card p-4">
      <div className="text-[11px] font-bold uppercase text-muted-foreground">{label}</div>
      <div className="mt-1 truncate font-extrabold">{value}</div>
    </div>
  );
}

function PayloadStandard({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs font-bold uppercase text-blue-900/70">{label}</div>
      <div className="mt-1 leading-6 text-blue-900">{value}</div>
    </div>
  );
}
