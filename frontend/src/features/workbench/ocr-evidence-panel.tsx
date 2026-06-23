import * as React from "react";
import { Loader2, ScanLine } from "lucide-react";

import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { Label, Textarea } from "../../components/ui/form";
import { HelpTooltip } from "../../components/ui/help-tooltip";
import { Notice } from "../../components/ui/notice";
import { useOcrEvidenceMutation, workflowErrorMessage } from "../../lib/server-state";
import type { Evidence, OcrEvidenceFieldInput, OcrField } from "../../types";

export function OcrEvidencePanel() {
  const ocrEvidence = useOcrEvidenceMutation();
  const [fieldsText, setFieldsText] = React.useState("");
  const [parseError, setParseError] = React.useState<string | null>(null);
  const normalized = ocrEvidence.data ?? null;
  const pageGroups = React.useMemo(
    () => groupFieldsByPage(normalized?.fields ?? []),
    [normalized?.fields],
  );

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    const parsed = parseOcrFields(fieldsText);
    if (!parsed.ok) {
      setParseError(parsed.error);
      return;
    }
    setParseError(null);
    await ocrEvidence.mutateAsync(parsed.fields);
  };

  return (
    <Card className="min-w-0 overflow-hidden">
      <CardHeader className="border-b border-border/60 bg-muted/30 p-4">
        <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
          <div className="min-w-0">
            <CardTitle className="flex items-center gap-2">
              <ScanLine className="h-5 w-5" />
              OCR evidence review
            </CardTitle>
            <CardDescription>
              Normalize page-level OCR boxes before trusting extracted values.
            </CardDescription>
          </div>
          {normalized ? (
            <Badge variant={normalized.requires_review ? "warning" : "success"}>
              {normalized.requires_review ? "review needed" : "review clear"}
            </Badge>
          ) : null}
        </div>
      </CardHeader>
      <CardContent className="grid gap-4 pt-4">
        <form className="grid gap-3" onSubmit={(event) => void submit(event)}>
          {parseError ? (
            <Notice title="OCR fields could not be parsed" tone="danger">
              {parseError}
            </Notice>
          ) : null}
          {ocrEvidence.isError ? (
            <Notice title="OCR evidence could not be normalized" tone="danger">
              {workflowErrorMessage(ocrEvidence.error)}
            </Notice>
          ) : null}
          <Label>
            <span className="inline-flex items-center gap-1.5">
              Fields JSON
              <HelpTooltip label="OCR evidence JSON help">
                Paste either an array of OCR fields or an object with a fields array. Each field needs page, name, value, bbox, confidence, and source_ref.
              </HelpTooltip>
            </span>
            <Textarea
              className="min-h-40 resize-y font-mono text-xs"
              onChange={(event) => {
                setFieldsText(event.target.value);
                if (parseError) setParseError(null);
              }}
              placeholder='[{"page":1,"name":"field_name","value":"...","bbox":[x,y,width,height],"confidence":0.95,"source_ref":"storage://..."}]'
              spellCheck={false}
              value={fieldsText}
            />
          </Label>
          <Button disabled={ocrEvidence.isPending} type="submit" variant="outline">
            {ocrEvidence.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <ScanLine className="h-4 w-4" />
            )}
            Normalize OCR evidence
          </Button>
        </form>

        {normalized ? (
          <div className="grid gap-3">
            <OcrEvidenceSummary
              evidence={normalized.evidence}
              fieldCount={normalized.fields.length}
              pageCount={pageGroups.length}
              requiresReview={normalized.requires_review}
            />
            {pageGroups.map((group) => (
              <OcrPageEvidenceGroup
                fields={group.fields}
                key={group.page}
                page={group.page}
              />
            ))}
          </div>
        ) : (
          <div className="rounded-md border border-dashed border-border bg-muted/25 p-4 text-sm leading-6 text-muted-foreground">
            OCR evidence appears here grouped by page after normalization. Low confidence
            fields are marked for human review.
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function OcrEvidenceSummary({
  evidence,
  fieldCount,
  pageCount,
  requiresReview,
}: {
  evidence: Evidence[];
  fieldCount: number;
  pageCount: number;
  requiresReview: boolean;
}) {
  return (
    <div className="grid gap-2 rounded-lg border border-border/60 bg-muted/25 p-3 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="muted">{formatCount(pageCount, "page")}</Badge>
        <Badge variant="muted">{formatCount(fieldCount, "field")}</Badge>
        <Badge variant="muted">{formatCount(evidence.length, "evidence ref")}</Badge>
        <Badge variant={requiresReview ? "warning" : "success"}>
          {requiresReview ? "low confidence present" : "all confidence ok"}
        </Badge>
      </div>
      {evidence.length ? (
        <div className="grid gap-1 text-xs text-muted-foreground">
          {evidence.slice(0, 4).map((item) => (
            <div className="line-clamp-2" key={item.evidence_id}>
              <span className="font-mono text-foreground">{item.evidence_id}</span> /{" "}
              {item.claim}
            </div>
          ))}
          {evidence.length > 4 ? (
            <div>{formatCount(evidence.length - 4, "more evidence ref")} hidden.</div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

function OcrPageEvidenceGroup({ fields, page }: { fields: OcrField[]; page: number }) {
  return (
    <section className="grid gap-3 rounded-lg border border-border/60 bg-card p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <div className="font-extrabold">Page {page}</div>
          <div className="text-xs font-semibold text-muted-foreground">
            {formatCount(fields.length, "OCR field")}
          </div>
        </div>
        <Badge variant={fields.some((field) => field.requires_review) ? "warning" : "success"}>
          {fields.some((field) => field.requires_review) ? "review needed" : "confidence ok"}
        </Badge>
      </div>
      <OcrPageMap fields={fields} />
      <div className="grid gap-2">
        {fields.map((field) => (
          <OcrFieldRow field={field} key={field.field_id} />
        ))}
      </div>
    </section>
  );
}

function OcrPageMap({ fields }: { fields: OcrField[] }) {
  const bounds = pageBounds(fields);
  return (
    <div className="relative h-44 overflow-hidden rounded-lg border border-border/60 bg-[linear-gradient(90deg,rgba(148,163,184,0.16)_1px,transparent_1px),linear-gradient(rgba(148,163,184,0.16)_1px,transparent_1px)] bg-[size:24px_24px]">
      {fields.map((field) => {
        const [x, y, width, height] = field.bbox;
        return (
          <div
            className={`absolute min-h-5 min-w-12 overflow-hidden rounded-sm border px-1 py-0.5 text-[10px] font-black shadow-sm ${
              field.requires_review
                ? "border-amber-400 bg-amber-100/80 text-amber-950"
                : "border-teal-500 bg-teal-100/80 text-teal-950"
            }`}
            key={field.field_id}
            style={{
              left: `${percent(x, bounds.maxX)}%`,
              top: `${percent(y, bounds.maxY)}%`,
              width: `${Math.max(8, percent(width, bounds.maxX))}%`,
              height: `${Math.max(10, percent(height, bounds.maxY))}%`,
            }}
            title={`${field.name}: ${field.value}`}
          >
            <span className="truncate">{field.name}</span>
          </div>
        );
      })}
    </div>
  );
}

function OcrFieldRow({ field }: { field: OcrField }) {
  return (
    <div className="grid gap-2 rounded-lg border border-border/60 bg-muted/20 p-3 text-sm">
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="break-words font-extrabold">{field.name}</div>
          <div className="break-words text-muted-foreground">{field.value || "(empty)"}</div>
        </div>
        <Badge variant={field.requires_review ? "warning" : "success"}>
          {Math.round(field.confidence * 100)}%
        </Badge>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-muted">
        <div
          className={field.requires_review ? "h-full bg-warning" : "h-full bg-primary"}
          style={{ width: `${Math.round(field.confidence * 100)}%` }}
        />
      </div>
      <div className="grid gap-1 text-xs font-semibold text-muted-foreground sm:grid-cols-2">
        <span className="break-all">Source: {field.source_ref}</span>
        <span>BBox: [{field.bbox.map((value) => round(value)).join(", ")}]</span>
        {field.normalized_to ? <span>Normalized to: {field.normalized_to}</span> : null}
        {field.requires_review ? <span>Reason: confidence below review threshold</span> : null}
      </div>
    </div>
  );
}

function parseOcrFields(value: string):
  | { ok: true; fields: OcrEvidenceFieldInput[] }
  | { ok: false; error: string } {
  if (!value.trim()) return { ok: false, error: "Paste at least one OCR evidence field." };
  try {
    const parsed = JSON.parse(value);
    const fields = Array.isArray(parsed)
      ? parsed
      : isRecord(parsed) && Array.isArray(parsed.fields)
        ? parsed.fields
        : null;
    if (!fields) {
      return {
        ok: false,
        error: "JSON must be an array or an object with a fields array.",
      };
    }
    const normalized = fields.map(normalizeOcrField);
    const invalid = normalized.find((field) => typeof field === "string");
    if (typeof invalid === "string") return { ok: false, error: invalid };
    return { ok: true, fields: normalized as OcrEvidenceFieldInput[] };
  } catch (error) {
    return {
      ok: false,
      error: error instanceof Error ? error.message : "JSON is invalid.",
    };
  }
}

function normalizeOcrField(value: unknown, index: number): OcrEvidenceFieldInput | string {
  if (!isRecord(value)) return `Field ${index + 1} must be an object.`;
  const page = numberValue(value.page);
  const name = stringValue(value.name);
  const fieldValue = stringValue(value.value, true);
  const bbox = Array.isArray(value.bbox) ? value.bbox.map(numberValue) : [];
  const confidence = numberValue(value.confidence);
  const sourceRef = stringValue(value.source_ref);
  const normalizedTo = stringValue(value.normalized_to, true);
  if (!Number.isInteger(page) || page < 1) return `Field ${index + 1} needs page >= 1.`;
  if (!name) return `Field ${index + 1} needs a non-empty name.`;
  if (bbox.length !== 4 || bbox.some((item) => !Number.isFinite(item) || item < 0)) {
    return `Field ${index + 1} needs bbox as [x, y, width, height].`;
  }
  if (!Number.isFinite(confidence) || confidence < 0 || confidence > 1) {
    return `Field ${index + 1} needs confidence between 0 and 1.`;
  }
  if (!sourceRef) return `Field ${index + 1} needs a non-empty source_ref.`;
  return {
    page,
    name,
    value: fieldValue,
    bbox,
    confidence,
    source_ref: sourceRef,
    normalized_to: normalizedTo || null,
  };
}

function groupFieldsByPage(fields: OcrField[]) {
  const groups = new Map<number, OcrField[]>();
  for (const field of fields) {
    groups.set(field.page, [...(groups.get(field.page) ?? []), field]);
  }
  return Array.from(groups, ([page, pageFields]) => ({ page, fields: pageFields })).sort(
    (left, right) => left.page - right.page,
  );
}

function pageBounds(fields: OcrField[]) {
  return fields.reduce(
    (bounds, field) => {
      const [x, y, width, height] = field.bbox;
      return {
        maxX: Math.max(bounds.maxX, x + width),
        maxY: Math.max(bounds.maxY, y + height),
      };
    },
    { maxX: 1, maxY: 1 },
  );
}

function percent(value: number, max: number) {
  if (!max) return 0;
  return Math.max(0, Math.min(100, (value / max) * 100));
}

function round(value: number) {
  return Number.isInteger(value) ? String(value) : value.toFixed(2);
}

function formatCount(value: number, singular: string) {
  return `${value} ${singular}${value === 1 ? "" : "s"}`;
}

function numberValue(value: unknown) {
  if (typeof value === "number") return value;
  if (typeof value === "string" && value.trim()) return Number(value);
  return Number.NaN;
}

function stringValue(value: unknown, allowEmpty = false) {
  if (typeof value !== "string") return "";
  const trimmed = value.trim();
  return trimmed || (allowEmpty ? value : "");
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
