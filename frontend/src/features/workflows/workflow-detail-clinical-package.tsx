import { GitCompare, Stethoscope, Tags } from "lucide-react";

import { Badge } from "../../components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { SeverityBadge } from "../../components/domain/workflow-badges";
import { Notice } from "../../components/ui/notice";
import { Table, TBody, TD, TH, THead, TR } from "../../components/ui/table";
import { humanize } from "../../lib/utils";
import type {
  ClinicalPackage,
  ClinicalResourceRecord,
  TerminologyCandidate,
  UnitValidationResult,
  ValidationIssue,
  WorkflowState,
} from "../../types";

export function ClinicalPackagePanel({ workflow }: { workflow: WorkflowState }) {
  const clinicalPackage = workflow.clinical_package;
  if (!clinicalPackage) {
    return (
      <Notice title="No clinical package">
        This workflow has no supported healthcare package mapping yet.
      </Notice>
    );
  }

  const resources = clinicalPackage.clinical_bundle.resources;
  return (
    <div className="grid min-w-0 gap-4">
      <Notice title="FHIR-like output boundary">
        This package is an OJTFlow clinical package with FHIR-like resources. It is not HL7 FHIR compliant until a target FHIR validator accepts it.
      </Notice>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        <ClinicalMetric label="Resources" value={resources.length} />
        <ClinicalMetric label="Terminology" value={clinicalPackage.terminology_candidates.length} />
        <ClinicalMetric label="Units" value={clinicalPackage.unit_validations.length} />
        <ClinicalMetric label="Issues" value={clinicalPackage.operation_outcome.issue.length} />
        <ClinicalMetric label="Provenance" value={clinicalPackage.provenance.length} />
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
        <TerminologyEvidencePanel clinicalPackage={clinicalPackage} />
        <PackageResourceSummary clinicalPackage={clinicalPackage} />
      </div>

      <ClinicalPackageDiff resources={resources} />

      {clinicalPackage.warnings.length ? (
        <Card className="min-w-0 overflow-hidden">
          <CardHeader className="border-b border-border bg-card/70 p-4">
            <CardTitle>Package warnings</CardTitle>
            <CardDescription>Limitations carried with the package export.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-2 pt-4">
            {clinicalPackage.warnings.map((warning) => (
              <div
                className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm font-semibold text-amber-950"
                key={warning}
              >
                {warning}
              </div>
            ))}
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}

function ClinicalMetric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-border bg-card p-3">
      <div className="text-xs font-bold uppercase text-muted-foreground">{label}</div>
      <div className="mt-1 text-2xl font-black tabular-nums">{value}</div>
    </div>
  );
}

function TerminologyEvidencePanel({
  clinicalPackage,
}: {
  clinicalPackage: ClinicalPackage;
}) {
  const candidates = clinicalPackage.terminology_candidates;
  const unitValidations = clinicalPackage.unit_validations;
  return (
    <Card className="min-w-0 overflow-hidden">
      <CardHeader className="border-b border-border bg-card/70 p-4">
        <div className="flex min-w-0 items-start gap-3">
          <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
            <Tags className="h-4 w-4" />
          </span>
          <div className="min-w-0">
            <CardTitle>Terminology evidence</CardTitle>
            <CardDescription>
              Source text, candidate code, confidence, source terminology, and reviewer state.
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="grid gap-4 pt-4">
        <div className="grid gap-3">
          {candidates.map((candidate) => (
            <TerminologyCandidateCard candidate={candidate} key={candidate.candidate_id} />
          ))}
          {!candidates.length ? (
            <div className="rounded-md border border-border p-3 text-sm text-muted-foreground">
              No terminology candidates generated.
            </div>
          ) : null}
        </div>

        <div className="grid gap-2 border-t border-border pt-4">
          <div className="text-sm font-extrabold">Unit checks</div>
          {unitValidations.map((unit) => (
            <UnitValidationCard key={unit.validation_id} unit={unit} />
          ))}
          {!unitValidations.length ? (
            <div className="rounded-md border border-border p-3 text-sm text-muted-foreground">
              No unit validations recorded.
            </div>
          ) : null}
        </div>
      </CardContent>
    </Card>
  );
}

function TerminologyCandidateCard({ candidate }: { candidate: TerminologyCandidate }) {
  return (
    <article className="grid gap-3 rounded-md border border-border bg-muted/20 p-3">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="break-words font-extrabold">{candidate.source_value}</div>
          <div className="mt-0.5 text-xs font-semibold text-muted-foreground">
            {candidate.source_field} {formatLocation(candidate.location)}
          </div>
        </div>
        <div className="flex flex-wrap justify-end gap-1.5">
          <Badge variant={candidate.requires_review ? "warning" : "success"}>
            {humanize(candidate.status)}
          </Badge>
          <Badge variant="muted">{formatConfidence(candidate.confidence)}</Badge>
        </div>
      </div>
      <div className="grid gap-2 text-sm sm:grid-cols-2">
        <ClinicalFact label="Candidate code" value={`${candidate.standard_system} ${candidate.code}`} />
        <ClinicalFact label="Display" value={candidate.display} />
        <ClinicalFact label="Source terminology" value={candidate.source_uri ?? candidate.standard_system} />
        <ClinicalFact
          label="Matched aliases"
          value={candidate.matched_aliases.length ? candidate.matched_aliases.join(", ") : "none"}
        />
      </div>
    </article>
  );
}

function UnitValidationCard({ unit }: { unit: UnitValidationResult }) {
  return (
    <article className="grid gap-2 rounded-md border border-border bg-card p-3 text-sm">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="min-w-0 font-extrabold">
          {unit.source_field}: {unit.source_unit || "missing"}
        </div>
        <div className="flex flex-wrap justify-end gap-1.5">
          <Badge variant={unit.requires_review ? "warning" : "success"}>
            {humanize(unit.status)}
          </Badge>
          <Badge variant="muted">{formatConfidence(unit.confidence)}</Badge>
        </div>
      </div>
      <div className="grid gap-2 sm:grid-cols-2">
        <ClinicalFact label="Normalized unit" value={unit.normalized_unit ?? "none"} />
        <ClinicalFact label="Standard" value={unit.standard_system} />
      </div>
      <p className="text-muted-foreground">{unit.message}</p>
    </article>
  );
}

function PackageResourceSummary({
  clinicalPackage,
}: {
  clinicalPackage: ClinicalPackage;
}) {
  const resourceCounts = clinicalPackage.clinical_bundle.resources.reduce<Record<string, number>>(
    (counts, resource) => {
      counts[resource.resource_type] = (counts[resource.resource_type] ?? 0) + 1;
      return counts;
    },
    {},
  );
  return (
    <Card className="min-w-0 overflow-hidden">
      <CardHeader className="border-b border-border bg-card/70 p-4">
        <div className="flex min-w-0 items-start gap-3">
          <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
            <Stethoscope className="h-4 w-4" />
          </span>
          <div className="min-w-0">
            <CardTitle>Package summary</CardTitle>
            <CardDescription>{clinicalPackage.package_id}</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="grid gap-4 pt-4">
        <div className="grid gap-2 rounded-md border border-border p-3 text-sm">
          <Row label="Schema" value={clinicalPackage.schema_version} />
          <Row label="Detected input" value={clinicalPackage.raw_input.detected_format} />
          <Row label="Review" value={clinicalPackage.review?.status ?? "not required"} />
          <Row label="Output refs" value={String(clinicalPackage.output_refs.length)} />
        </div>
        <div className="grid gap-2">
          <div className="text-sm font-extrabold">Resource types</div>
          <div className="flex flex-wrap gap-2">
            {Object.entries(resourceCounts).map(([resourceType, count]) => (
              <Badge key={resourceType} variant="muted">
                {resourceType}: {count}
              </Badge>
            ))}
          </div>
        </div>
        {clinicalPackage.operation_outcome.issue.length ? (
          <div className="grid gap-2">
            <div className="text-sm font-extrabold">OperationOutcome-like issues</div>
            {clinicalPackage.operation_outcome.issue.slice(0, 5).map((issue) => (
              <div className="rounded-md border border-border bg-muted/20 p-2 text-sm" key={issue.issue_id ?? issue.diagnostics}>
                <div className="flex flex-wrap items-center gap-2">
                  <SeverityBadge severity={issue.severity} />
                  <span className="font-bold">{issue.code}</span>
                  {issue.requires_review ? <Badge variant="warning">Review</Badge> : null}
                </div>
                <p className="mt-1 text-muted-foreground">{issue.diagnostics}</p>
              </div>
            ))}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

function ClinicalPackageDiff({ resources }: { resources: ClinicalResourceRecord[] }) {
  return (
    <Card className="min-w-0 overflow-hidden">
      <CardHeader className="border-b border-border bg-card/70 p-4">
        <div className="flex min-w-0 items-start gap-3">
          <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
            <GitCompare className="h-4 w-4" />
          </span>
          <div className="min-w-0">
            <CardTitle>Clinical package diff</CardTitle>
            <CardDescription>Raw source fields mapped to generated FHIR-like resource fields.</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="grid gap-4 pt-4">
        {resources.map((resource) => (
          <ResourceDiffCard key={`${resource.resource_type}-${resource.resource_id}`} resource={resource} />
        ))}
        {!resources.length ? (
          <div className="rounded-md border border-border p-3 text-sm text-muted-foreground">
            No resources generated.
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

function ResourceDiffCard({ resource }: { resource: ClinicalResourceRecord }) {
  return (
    <article className="min-w-0 overflow-hidden rounded-md border border-border bg-card">
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-border bg-muted/20 px-3 py-2">
        <div className="min-w-0">
          <div className="break-words font-extrabold">
            {resource.resource_type}/{resource.resource_id}
          </div>
          <div className="text-xs font-semibold text-muted-foreground">
            Source row {resource.source_row ?? "n/a"}
          </div>
        </div>
        <div className="flex flex-wrap justify-end gap-1.5">
          {resource.review_required ? <Badge variant="warning">Review required</Badge> : null}
          {resource.warnings.map((warning) => (
            <Badge key={warning} variant="warning">{humanize(warning)}</Badge>
          ))}
        </div>
      </div>
      <Table wrapperClassName="max-h-[22rem] overflow-auto">
        <THead>
          <TR>
            <TH>Generated field</TH>
            <TH>Source field</TH>
            <TH>Source value</TH>
            <TH>Derivation</TH>
            <TH>Evidence</TH>
          </TR>
        </THead>
        <TBody>
          {resource.field_provenance.map((field) => (
            <TR key={`${resource.resource_id}-${field.target_path}-${field.note}`}>
              <TD className="min-w-48 font-medium">{field.target_path}</TD>
              <TD>{field.source_field ?? "-"}</TD>
              <TD className="max-w-72 break-words">{formatUnknownValue(field.source_value)}</TD>
              <TD><Badge variant={derivationVariant(field.derivation)}>{humanize(field.derivation)}</Badge></TD>
              <TD className="min-w-56 text-muted-foreground">
                <div>{field.evidence_ids.length ? field.evidence_ids.join(", ") : "none"}</div>
                <div className="mt-1 text-xs">{field.note}</div>
              </TD>
            </TR>
          ))}
          {!resource.field_provenance.length ? (
            <TR><TD colSpan={5}>No field provenance recorded.</TD></TR>
          ) : null}
        </TBody>
      </Table>
      <details className="border-t border-border bg-muted/20 px-3 py-2">
        <summary className="cursor-pointer text-sm font-bold">Resource JSON</summary>
        <pre className="mt-2 max-h-72 overflow-auto whitespace-pre-wrap break-words rounded-md bg-card p-2 text-xs text-muted-foreground">
          {JSON.stringify(resource.resource, null, 2)}
        </pre>
      </details>
    </article>
  );
}

function ClinicalFact({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid gap-1 rounded-md border border-border bg-card px-3 py-2">
      <span className="text-xs font-bold uppercase text-muted-foreground">{label}</span>
      <span className="min-w-0 break-words font-semibold">{value}</span>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid grid-cols-[110px_minmax(0,1fr)] gap-3">
      <span className="font-bold text-muted-foreground">{label}</span>
      <span className="break-words">{value}</span>
    </div>
  );
}

function formatConfidence(confidence: number | null | undefined) {
  return typeof confidence === "number" ? `${Math.round(confidence * 100)}%` : "n/a";
}

function formatUnknownValue(value: unknown) {
  if (value === null || value === undefined || value === "") return "-";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return JSON.stringify(value);
}

function formatLocation(location: ValidationIssue["location"] | null | undefined) {
  if (!location) return "";
  const parts = [
    location.row ? `row ${location.row}` : null,
    location.column ? `column ${location.column}` : null,
    location.field ? `field ${location.field}` : null,
  ].filter((item): item is string => Boolean(item));
  return parts.length ? ` / ${parts.join(", ")}` : "";
}

function derivationVariant(
  derivation: ClinicalResourceRecord["field_provenance"][number]["derivation"],
): "default" | "success" | "warning" | "destructive" | "muted" {
  if (derivation === "source") return "success";
  if (derivation === "review_required") return "warning";
  if (derivation === "unmapped") return "destructive";
  if (derivation === "defaulted") return "muted";
  return "default";
}
