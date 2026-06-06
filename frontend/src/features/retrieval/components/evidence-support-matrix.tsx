import type { ReactNode } from "react";

import { Badge } from "../../../components/ui/badge";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import { Table, TBody, TD, TH, THead, TR } from "../../../components/ui/table";
import { SectionHelpText } from "./section-help-text";

export type EvidenceSupportMatrixRowView = {
  aspectCount: number;
  bucketLabels: string[];
  conceptCount: number;
  confidenceLabel: string;
  evidenceId: string;
  judgment: { value: "relevant" | "partial" | "not_relevant" } | null;
  matchedTermCount: number;
  provenanceCount: number;
  rank: number;
  score: number;
  sourceId: string;
  sourceType: string;
  standardSystem: string | null;
  supportStatus: "strong" | "partial" | "weak";
};

type BadgeVariant = "default" | "success" | "warning" | "destructive" | "muted";

export function EvidenceSupportMatrix({
  formatCount,
  formatScore,
  humanize,
  judgmentBadgeVariant,
  judgmentLabel,
  rows,
  supportStatusBadgeVariant,
}: {
  formatCount: (count: number, singular: string) => string;
  formatScore: (score: number) => string;
  humanize: (value: string) => string;
  judgmentBadgeVariant: (value: "relevant" | "partial" | "not_relevant") => BadgeVariant;
  judgmentLabel: (value: "relevant" | "partial" | "not_relevant") => string;
  rows: EvidenceSupportMatrixRowView[];
  supportStatusBadgeVariant: (
    status: EvidenceSupportMatrixRowView["supportStatus"],
  ) => BadgeVariant;
}) {
  if (!rows.length) return null;
  return (
    <section className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="inline-flex items-center gap-1.5 text-xs font-black uppercase text-muted-foreground">
            <span>Evidence support matrix</span>
            <HelpTooltip label="Evidence support matrix help">
              Fast scan of whether each ranked hit has terms, provenance, concept grounding, query-aspect support, judgment state, and enough score support to trust for review.
            </HelpTooltip>
          </div>
          <div className="mt-1 text-sm font-semibold text-muted-foreground">
            Coverage, grounding, provenance, and review state for selected evidence.
          </div>
        </div>
        <Badge variant={rows.some((row) => row.supportStatus === "weak") ? "warning" : "success"}>
          {formatCount(rows.length, "evidence row")}
        </Badge>
      </div>
      <SectionHelpText>
        Weak rows need inspection before use. Missing provenance means the source locator is thin; missing concepts or aspects means the hit may match words without enough medical grounding.
      </SectionHelpText>
      <div className="grid gap-2 md:hidden">
        {rows.map((row) => (
          <EvidenceSupportMatrixCard
            formatScore={formatScore}
            humanize={humanize}
            judgmentBadgeVariant={judgmentBadgeVariant}
            judgmentLabel={judgmentLabel}
            key={row.evidenceId}
            row={row}
            supportStatusBadgeVariant={supportStatusBadgeVariant}
          />
        ))}
      </div>
      <div className="hidden overflow-auto rounded-md border border-border bg-card md:block">
        <Table>
          <THead>
            <TR>
              <TH>Rank</TH>
              <TH>Source</TH>
              <TH>Standard</TH>
              <TH>Evidence buckets</TH>
              <TH>Support</TH>
              <TH>Judgment</TH>
              <TH>Score</TH>
            </TR>
          </THead>
          <TBody>
            {rows.map((row) => (
              <TR key={row.evidenceId}>
                <TD className="font-mono text-xs font-bold">#{row.rank}</TD>
                <TD>
                  <div className="max-w-72 break-words font-bold">{row.sourceId}</div>
                  <div className="mt-1 text-xs text-muted-foreground">
                    {humanize(row.sourceType)} / {row.confidenceLabel}
                  </div>
                </TD>
                <TD>
                  {row.standardSystem ? (
                    <Badge variant="muted">{row.standardSystem}</Badge>
                  ) : (
                    <span className="text-xs font-semibold text-muted-foreground">-</span>
                  )}
                </TD>
                <TD>
                  <div className="flex min-w-52 flex-wrap gap-1">
                    {row.bucketLabels.length ? (
                      row.bucketLabels.map((label) => (
                        <Badge key={label} variant="muted">
                          {label}
                        </Badge>
                      ))
                    ) : (
                      <Badge variant="warning">No bucket</Badge>
                    )}
                  </div>
                </TD>
                <TD>
                  <div className="flex min-w-44 flex-wrap gap-1">
                    <Badge variant={row.matchedTermCount ? "success" : "warning"}>
                      {row.matchedTermCount} terms
                    </Badge>
                    <Badge variant={row.provenanceCount ? "success" : "warning"}>
                      {row.provenanceCount} provenance
                    </Badge>
                    <Badge variant={row.conceptCount ? "success" : "muted"}>
                      {row.conceptCount} concepts
                    </Badge>
                    <Badge variant={row.aspectCount ? "success" : "muted"}>
                      {row.aspectCount} aspects
                    </Badge>
                  </div>
                </TD>
                <TD>
                  {row.judgment ? (
                    <Badge variant={judgmentBadgeVariant(row.judgment.value)}>
                      {judgmentLabel(row.judgment.value)}
                    </Badge>
                  ) : (
                    <Badge variant="muted">Unjudged</Badge>
                  )}
                </TD>
                <TD>
                  <div className="font-mono text-xs font-bold">{formatScore(row.score)}</div>
                  <Badge variant={supportStatusBadgeVariant(row.supportStatus)}>
                    {humanize(row.supportStatus)}
                  </Badge>
                </TD>
              </TR>
            ))}
          </TBody>
        </Table>
      </div>
    </section>
  );
}

function EvidenceSupportMatrixCard({
  formatScore,
  humanize,
  judgmentBadgeVariant,
  judgmentLabel,
  row,
  supportStatusBadgeVariant,
}: {
  formatScore: (score: number) => string;
  humanize: (value: string) => string;
  judgmentBadgeVariant: (value: "relevant" | "partial" | "not_relevant") => BadgeVariant;
  judgmentLabel: (value: "relevant" | "partial" | "not_relevant") => string;
  row: EvidenceSupportMatrixRowView;
  supportStatusBadgeVariant: (
    status: EvidenceSupportMatrixRowView["supportStatus"],
  ) => BadgeVariant;
}) {
  return (
    <article className="grid min-w-0 gap-2 rounded-md border border-border bg-card p-3 text-sm">
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="text-xs font-black uppercase text-muted-foreground">
            Rank {row.rank}
          </div>
          <div className="mt-1 break-words font-black">{row.sourceId}</div>
          <div className="mt-1 text-xs font-semibold text-muted-foreground">
            {humanize(row.sourceType)} / {row.confidenceLabel}
          </div>
        </div>
        <div className="flex shrink-0 flex-wrap justify-end gap-1">
          <Badge variant={supportStatusBadgeVariant(row.supportStatus)}>
            {humanize(row.supportStatus)}
          </Badge>
          <Badge variant="muted">{formatScore(row.score)}</Badge>
        </div>
      </div>
      <div className="grid gap-2">
        <EvidenceSupportMobileField label="Standard">
          {row.standardSystem ? (
            <Badge variant="muted">{row.standardSystem}</Badge>
          ) : (
            <span className="text-xs font-semibold text-muted-foreground">Not specified</span>
          )}
        </EvidenceSupportMobileField>
        <EvidenceSupportMobileField label="Evidence buckets">
          <div className="flex min-w-0 flex-wrap gap-1">
            {row.bucketLabels.length ? (
              row.bucketLabels.map((label) => (
                <Badge key={label} variant="muted">
                  {label}
                </Badge>
              ))
            ) : (
              <Badge variant="warning">No bucket</Badge>
            )}
          </div>
        </EvidenceSupportMobileField>
        <EvidenceSupportMobileField label="Support">
          <div className="flex min-w-0 flex-wrap gap-1">
            <Badge variant={row.matchedTermCount ? "success" : "warning"}>
              {row.matchedTermCount} terms
            </Badge>
            <Badge variant={row.provenanceCount ? "success" : "warning"}>
              {row.provenanceCount} provenance
            </Badge>
            <Badge variant={row.conceptCount ? "success" : "muted"}>
              {row.conceptCount} concepts
            </Badge>
            <Badge variant={row.aspectCount ? "success" : "muted"}>
              {row.aspectCount} aspects
            </Badge>
          </div>
        </EvidenceSupportMobileField>
        <EvidenceSupportMobileField label="Judgment">
          {row.judgment ? (
            <Badge variant={judgmentBadgeVariant(row.judgment.value)}>
              {judgmentLabel(row.judgment.value)}
            </Badge>
          ) : (
            <Badge variant="muted">Unjudged</Badge>
          )}
        </EvidenceSupportMobileField>
      </div>
    </article>
  );
}

function EvidenceSupportMobileField({
  children,
  label,
}: {
  children: ReactNode;
  label: string;
}) {
  return (
    <div className="min-w-0 rounded-md bg-muted/45 px-2 py-1.5">
      <div className="text-[11px] font-black uppercase text-muted-foreground">
        {label}
      </div>
      <div className="mt-1 min-w-0">{children}</div>
    </div>
  );
}
