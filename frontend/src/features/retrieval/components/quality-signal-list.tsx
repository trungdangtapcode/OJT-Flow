import { AlertTriangle, CheckCircle2 } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import type { RetrievalQualitySignal } from "../../../types";
import { SectionHelpText } from "./section-help-text";
import { TokenList } from "./token-list";

type BadgeVariant = "default" | "success" | "warning" | "destructive" | "muted";

export function QualitySignalList({ signals }: { signals: RetrievalQualitySignal[] }) {
  if (!signals.length) {
    return (
      <TokenList
        description="Backend quality checks did not return warnings or blockers."
        items={[]}
        title="Retrieval quality"
      />
    );
  }
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="text-xs font-bold uppercase text-muted-foreground">
          Retrieval quality
        </div>
        <Badge variant={qualitySignalSummaryVariant(signals)}>
          {formatCount(signals.length, "signal")}
        </Badge>
      </div>
      <SectionHelpText>
        Quality signals explain why the evidence package is ready, needs review, or is blocked.
      </SectionHelpText>
      <div className="grid gap-2">
        {signals.map((signal) => {
          const warning = signal.severity === "warning" || signal.severity === "destructive";
          return (
            <div
              className="grid gap-1.5 rounded-md border border-border bg-card p-2 text-xs"
              key={signal.code}
            >
              <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
                <span className="flex min-w-0 items-center gap-1.5">
                  {warning ? (
                    <AlertTriangle className="h-3.5 w-3.5 shrink-0 text-amber-600" />
                  ) : (
                    <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-emerald-600" />
                  )}
                  <span className="break-words font-bold">{humanize(signal.code)}</span>
                </span>
                <Badge variant={qualitySignalBadgeVariant(signal.severity)}>
                  {humanize(signal.severity)}
                </Badge>
              </div>
              <div className="break-words text-muted-foreground">{signal.message}</div>
              <div className="break-words font-semibold text-foreground">
                {signal.suggested_action}
              </div>
              <QualitySignalMetadataDetails signal={signal} />
              {signal.evidence_ids.length ? (
                <div className="flex min-w-0 flex-wrap gap-1">
                  {signal.evidence_ids.slice(0, 4).map((evidenceId) => (
                    <code
                      className="max-w-full break-words rounded bg-muted px-1.5 py-1 font-mono text-[11px]"
                      key={`${signal.code}-${evidenceId}`}
                    >
                      {evidenceId}
                    </code>
                  ))}
                  {signal.evidence_ids.length > 4 ? (
                    <span className="rounded bg-muted px-1.5 py-1 font-bold text-muted-foreground">
                      +{signal.evidence_ids.length - 4}
                    </span>
                  ) : null}
                </div>
              ) : null}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function qualitySignalBadgeVariant(severity: string): BadgeVariant {
  if (severity === "success") return "success";
  if (severity === "warning") return "warning";
  if (severity === "destructive" || severity === "error") return "destructive";
  if (severity === "info") return "muted";
  return "default";
}

function QualitySignalMetadataDetails({ signal }: { signal: RetrievalQualitySignal }) {
  const details = qualitySignalMetadataDetails(signal);
  if (!details.length) return null;
  return (
    <div className="grid gap-1.5 rounded-md border border-border bg-muted/20 p-2">
      <div className="text-[11px] font-bold uppercase text-muted-foreground">
        Signal details
      </div>
      <div className="grid gap-1.5">
        {details.map((detail) => (
          <div className="grid gap-1" key={detail.label}>
            <span className="font-bold text-muted-foreground">{detail.label}</span>
            <div className="flex min-w-0 flex-wrap gap-1">
              {detail.values.map((value) => (
                <Badge
                  className="max-w-full break-words text-left"
                  key={`${detail.label}-${value}`}
                  variant={detail.variant}
                >
                  {value}
                </Badge>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function qualitySignalSummaryVariant(signals: RetrievalQualitySignal[]): BadgeVariant {
  if (
    signals.some(
      (signal) => signal.severity === "destructive" || signal.severity === "error",
    )
  ) {
    return "destructive";
  }
  if (signals.some((signal) => signal.severity === "warning")) return "warning";
  if (signals.some((signal) => signal.severity === "success")) return "success";
  return "muted";
}

function qualitySignalMetadataDetails(signal: RetrievalQualitySignal): Array<{
  label: string;
  values: string[];
  variant: "success" | "warning" | "destructive" | "muted";
}> {
  const metadata = recordValue(signal.metadata);
  const details: Array<{
    label: string;
    values: string[];
    variant: "success" | "warning" | "destructive" | "muted";
  }> = [];
  const missingConcepts = conceptMetadataValues(metadata.missing_concepts);
  if (missingConcepts.length) {
    details.push({
      label: "Missing concepts",
      values: missingConcepts,
      variant: "warning",
    });
  }
  const provenanceIssues = provenanceIssueMetadataValues(metadata.issues);
  if (provenanceIssues.length) {
    details.push({
      label: "Provenance issues",
      values: provenanceIssues,
      variant: "warning",
    });
  }
  const missingStandards = stringArrayValue(metadata.missing_standards);
  if (missingStandards.length) {
    details.push({
      label: "Missing standards",
      values: missingStandards,
      variant: "warning",
    });
  }
  const missingAspects = stringArrayValue(metadata.missing_aspects).map(humanize);
  if (missingAspects.length) {
    details.push({
      label: "Missing aspects",
      values: missingAspects,
      variant: "warning",
    });
  }
  const suggestedFilters = suggestedFilterMetadataValues(metadata.suggested_filters);
  if (suggestedFilters.length) {
    details.push({
      label: "Suggested filters",
      values: suggestedFilters,
      variant: "muted",
    });
  }
  return details;
}

function conceptMetadataValues(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((concept) => {
      const standard = stringValue(concept.standard_system, "standard");
      const code = optionalStringValue(concept.code);
      const name = stringValue(concept.display_name, stringValue(concept.concept_id, "concept"));
      const confidence = numberValue(concept.confidence);
      const confidenceText = confidence === null ? "" : ` / ${Math.round(confidence * 100)}%`;
      return `${standard}${code ? ` ${code}` : ""}: ${name}${confidenceText}`;
    })
    .filter(Boolean);
}

function provenanceIssueMetadataValues(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((issue) => {
      const sourceId = stringValue(issue.source_id, "source");
      const missing = stringArrayValue(issue.missing).map(humanize);
      return `${sourceId}: missing ${missing.length ? missing.join(", ") : "metadata"}`;
    })
    .filter(Boolean);
}

function suggestedFilterMetadataValues(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .flatMap((filter) =>
      Object.entries(filter)
        .map(([field, rawValue]) => {
          const value = stringValue(rawValue, "");
          return value ? `${humanize(field)}=${value}` : "";
        })
        .filter(Boolean),
    );
}

function recordValue(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function stringArrayValue(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.map((item) => stringValue(item, "")).filter(Boolean);
}

function stringValue(value: unknown, fallback: string): string {
  return typeof value === "string" && value.trim() ? value.trim() : fallback;
}

function optionalStringValue(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function numberValue(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function formatCount(count: number, singular: string) {
  return `${count} ${singular}${count === 1 ? "" : "s"}`;
}
