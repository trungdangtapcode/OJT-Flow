import { useEffect, useState } from "react";
import { CheckCircle2, Clipboard, ExternalLink } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { humanize } from "../../../lib/utils";
import type { SearchHintStack } from "./search-plan-detail-panels";
import { TokenList } from "./token-list";

type SearchHintParameterExample = {
  example: string;
  matchedDatasetField: boolean;
  name: string;
  targetField: string;
};

type SearchHintLineageFollowup = {
  parameter: string;
  purpose: string;
};

export function SearchHintList({ hints }: { hints: SearchHintStack[] }) {
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  useEffect(() => {
    if (!copiedKey) return undefined;
    const timeoutId = window.setTimeout(() => setCopiedKey(null), 1800);
    return () => window.clearTimeout(timeoutId);
  }, [copiedKey]);

  const copyHintQuery = async (hintKey: string, query: string) => {
    await copyTextToClipboard(query);
    setCopiedKey(hintKey);
  };

  if (!hints.length) {
    return <TokenList items={[]} title="Medical search hints" />;
  }
  return (
    <div className="grid gap-1.5">
      <div className="text-xs font-bold uppercase text-muted-foreground">
        Medical search hints
      </div>
      <div className="grid gap-2">
        {hints.map((hint) => {
          const hintKey = `${hint.target}-${hint.query}`;
          const copied = copiedKey === hintKey;
          return (
            <div
              className="grid gap-1.5 rounded-md border border-border bg-card p-2 text-xs"
              key={hintKey}
            >
              <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
                <span className="break-words font-bold">{humanize(hint.target)}</span>
                <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
                  <Badge variant={hint.url ? "success" : "muted"}>
                    {hint.url ? "launchable hint" : "syntax hint"}
                  </Badge>
                  <Button
                    onClick={() => void copyHintQuery(hintKey, hint.query)}
                    size="sm"
                    title="Copy medical search hint"
                    type="button"
                    variant="outline"
                  >
                    {copied ? (
                      <CheckCircle2 className="h-4 w-4" />
                    ) : (
                      <Clipboard className="h-4 w-4" />
                    )}
                    {copied ? "Copied" : "Copy"}
                  </Button>
                  {hint.url ? (
                    <Button asChild size="sm" title="Open medical search hint" variant="outline">
                      <a href={hint.url} rel="noopener noreferrer" target="_blank">
                        <ExternalLink className="h-4 w-4" />
                        Open
                      </a>
                    </Button>
                  ) : null}
                </div>
              </div>
              <code className="block max-h-24 overflow-auto break-words rounded bg-muted px-2 py-1 font-mono text-xs">
                {hint.query}
              </code>
              <SearchHintMetadata metadata={hint.metadata} />
              <div className="break-words text-muted-foreground">{hint.rationale}</div>
              {hint.warnings.length ? (
                <TokenList items={hint.warnings} title="Hint warnings" tone="warning" />
              ) : null}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function SearchHintMetadata({ metadata }: { metadata: Record<string, unknown> }) {
  const parameterExamples = searchHintParameterExamples(metadata.parameter_examples);
  const lineageFollowup = searchHintLineageFollowup(metadata.lineage_followup);
  const scopeEndpoints = stringArrayValue(metadata.scope_endpoints);
  const selectedTerms = stringArrayValue(metadata.selected_terms);
  const selectedUnitCandidates = stringArrayValue(metadata.selected_unit_candidates);
  const selectedCandidates = selectedTerms.length ? selectedTerms : selectedUnitCandidates;
  const selectedCandidateTitle = selectedTerms.length ? "Selected terminology terms" : "Selected unit candidates";
  const capabilityWarning = optionalStringValue(metadata.capability_warning);
  if (
    !parameterExamples.length &&
    !lineageFollowup.length &&
    !scopeEndpoints.length &&
    !selectedCandidates.length &&
    !capabilityWarning
  ) {
    return null;
  }
  return (
    <details className="rounded-md border border-border bg-muted/20">
      <summary className="flex cursor-pointer list-none flex-wrap items-center gap-1.5 px-2 py-1.5 font-black">
        Route details
        {parameterExamples.length ? (
          <Badge variant="muted">{formatCount(parameterExamples.length, "parameter")}</Badge>
        ) : null}
        {scopeEndpoints.length ? <Badge variant="muted">scoped API</Badge> : null}
        {selectedCandidates.length ? (
          <Badge variant="success">{formatCount(selectedCandidates.length, "candidate")}</Badge>
        ) : null}
        {lineageFollowup.length ? <Badge variant="warning">lineage</Badge> : null}
      </summary>
      <div className="grid gap-2 border-t border-border p-2">
        {scopeEndpoints.length ? (
          <div className="grid gap-1.5">
            <div className="font-black uppercase text-muted-foreground">
              Endpoint scope
            </div>
            <div className="flex min-w-0 flex-wrap gap-1.5">
              {scopeEndpoints.slice(0, 6).map((endpoint) => (
                <code
                  className="rounded border border-border bg-card px-1.5 py-0.5 font-mono text-[11px]"
                  key={endpoint}
                >
                  {endpoint}
                </code>
              ))}
            </div>
          </div>
        ) : null}
        {selectedCandidates.length ? (
          <div className="grid gap-1.5">
            <div className="font-black uppercase text-muted-foreground">
              {selectedCandidateTitle}
            </div>
            <div className="flex min-w-0 flex-wrap gap-1.5">
              {selectedCandidates.slice(0, 8).map((candidate) => (
                <Badge key={candidate} variant="success">
                  {candidate}
                </Badge>
              ))}
            </div>
          </div>
        ) : null}
        {parameterExamples.length ? (
          <div className="grid gap-1.5">
            <div className="font-black uppercase text-muted-foreground">
              Parameter examples
            </div>
            {parameterExamples.map((example) => (
              <div
                className="grid gap-1 rounded-md border border-border bg-card px-2 py-1.5"
                key={`${example.name}:${example.example}`}
              >
                <div className="flex min-w-0 flex-wrap items-center gap-1.5">
                  <Badge variant={example.matchedDatasetField ? "success" : "muted"}>
                    {example.name}
                  </Badge>
                  <span className="break-words text-muted-foreground">
                    {example.targetField}
                  </span>
                </div>
                <code className="break-words font-mono text-[11px]">{example.example}</code>
              </div>
            ))}
          </div>
        ) : null}
        {lineageFollowup.length ? (
          <div className="grid gap-1.5">
            <div className="font-black uppercase text-muted-foreground">
              Lineage follow-up
            </div>
            {lineageFollowup.map((item) => (
              <div
                className="grid gap-1 rounded-md border border-amber-200 bg-amber-50 px-2 py-1.5 text-amber-950"
                key={item.parameter}
              >
                <code className="break-words font-mono text-[11px]">{item.parameter}</code>
                <div className="break-words text-[11px] leading-5">{item.purpose}</div>
              </div>
            ))}
          </div>
        ) : null}
        {capabilityWarning ? (
          <div className="rounded-md border border-border bg-card px-2 py-1.5 text-[11px] font-semibold leading-5 text-muted-foreground">
            {capabilityWarning}
          </div>
        ) : null}
      </div>
    </details>
  );
}

function stringArrayValue(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}

function optionalStringValue(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function searchHintParameterExamples(value: unknown): SearchHintParameterExample[] {
  return Array.isArray(value)
    ? value.flatMap((item) => {
        if (!item || typeof item !== "object" || Array.isArray(item)) return [];
        const record = item as Record<string, unknown>;
        const name = optionalStringValue(record.name);
        const targetField = optionalStringValue(record.target_field);
        const example = optionalStringValue(record.example);
        if (!name || !targetField || !example) return [];
        return [{
          example,
          matchedDatasetField: Boolean(record.matched_dataset_field),
          name,
          targetField,
        }];
      })
    : [];
}

function searchHintLineageFollowup(value: unknown): SearchHintLineageFollowup[] {
  return Array.isArray(value)
    ? value.flatMap((item) => {
        if (!item || typeof item !== "object" || Array.isArray(item)) return [];
        const record = item as Record<string, unknown>;
        const parameter = optionalStringValue(record.parameter);
        const purpose = optionalStringValue(record.purpose);
        return parameter && purpose ? [{ parameter, purpose }] : [];
      })
    : [];
}

async function copyTextToClipboard(text: string): Promise<void> {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }
  const element = document.createElement("textarea");
  element.value = text;
  element.setAttribute("readonly", "true");
  element.style.position = "fixed";
  element.style.left = "-9999px";
  document.body.appendChild(element);
  element.select();
  try {
    document.execCommand("copy");
  } finally {
    document.body.removeChild(element);
  }
}

function formatCount(count: number, singular: string) {
  return `${count} ${singular}${count === 1 ? "" : "s"}`;
}
