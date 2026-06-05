import * as React from "react";
import {
  CheckCircle2,
  Database,
  FileText,
  ListChecks,
  Search,
  ShieldCheck,
} from "lucide-react";

import { Badge } from "../../components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { Input } from "../../components/ui/form";
import { GuideGrid, GuideItem, GuidePanel } from "../../components/ui/guide-panel";
import { HelpTooltip } from "../../components/ui/help-tooltip";
import { Notice } from "../../components/ui/notice";
import { PageHeader } from "../../components/layout/page-header";
import { Skeleton } from "../../components/ui/skeleton";
import { SummaryStrip, SummaryStripItem } from "../../components/ui/summary-strip";
import { Table, TBody, TD, TH, THead, TR } from "../../components/ui/table";
import { useSchemasQuery, workflowErrorMessage } from "../../lib/server-state";
import { cn } from "../../lib/utils";
import type { SchemaEntry } from "../../types";

export function SchemasPage() {
  const schemasQuery = useSchemasQuery();
  const schemas = schemasQuery.data ?? [];
  const [query, setQuery] = React.useState("");
  const [selectedSchemaId, setSelectedSchemaId] = React.useState<string | null>(null);
  const filteredSchemas = React.useMemo(
    () => filterSchemas(schemas, query),
    [query, schemas],
  );
  const selectedSchema =
    schemas.find((schema) => schema.schema_id === selectedSchemaId) ??
    filteredSchemas[0] ??
    schemas[0] ??
    null;

  React.useEffect(() => {
    if (!selectedSchemaId && schemas.length) {
      setSelectedSchemaId(schemas[0].schema_id);
      return;
    }
    if (selectedSchemaId && !schemas.some((schema) => schema.schema_id === selectedSchemaId)) {
      setSelectedSchemaId(schemas[0]?.schema_id ?? null);
    }
  }, [schemas, selectedSchemaId]);

  const requiredFieldCount = schemas.reduce((count, schema) => count + schema.required.length, 0);
  const totalFieldCount = schemas.reduce((count, schema) => count + schema.field_count, 0);

  return (
    <div className="grid gap-5">
      <PageHeader
        title="Schema registry"
        description="Approved healthcare data profiles used for validation, retrieval grounding, and review policy."
      />
      <GuidePanel title="How to use schema profiles">
        <GuideGrid>
          <GuideItem title="Pick the expected record shape">
            A schema tells the backend which fields matter for a healthcare data type, such as lab results or FHIR-like resources.
          </GuideItem>
          <GuideItem title="Read required fields">
            Missing required fields usually create validation issues and may require human review.
          </GuideItem>
          <GuideItem title="Use source references">
            Source references explain why a schema is trusted and help audit validation decisions later.
          </GuideItem>
        </GuideGrid>
      </GuidePanel>

      <SummaryStrip columns={3}>
        <SummaryStripItem
          icon={Database}
          label="Profiles"
          loading={schemasQuery.isLoading}
          supporting="Approved schemas"
          value={schemas.length}
        />
        <SummaryStripItem
          icon={ListChecks}
          label="Fields"
          loading={schemasQuery.isLoading}
          supporting="Validated attributes"
          tone="info"
          value={totalFieldCount}
        />
        <SummaryStripItem
          icon={ShieldCheck}
          label="Required"
          loading={schemasQuery.isLoading}
          supporting="Review-sensitive fields"
          tone="warning"
          value={requiredFieldCount}
        />
      </SummaryStrip>

      {schemasQuery.isLoading ? <SchemaRegistrySkeleton /> : null}
      {schemasQuery.isError ? (
        <Notice title="Schema registry could not be loaded" tone="danger">
          {workflowErrorMessage(schemasQuery.error)}
        </Notice>
      ) : null}
      {!schemasQuery.isLoading && !schemasQuery.isError && !schemas.length ? (
        <Notice title="No schemas available">
          Add approved schema definitions before running validation-backed workflows.
        </Notice>
      ) : null}

      {!schemasQuery.isLoading && !schemasQuery.isError && schemas.length ? (
        <div className="grid items-start gap-4 xl:grid-cols-[minmax(300px,0.42fr)_minmax(0,1fr)]">
          <Card className="min-w-0 self-start overflow-hidden">
            <CardHeader className="border-b border-border bg-card/70 p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Search className="h-5 w-5 text-primary" />
                    Registry search
                    <HelpTooltip label="Schema registry search help">
                      Search by profile ID, title, field name, or source reference when deciding which contract to use for validation.
                    </HelpTooltip>
                  </CardTitle>
                  <CardDescription>Find profiles by ID, title, field name, or source reference.</CardDescription>
                </div>
                <Badge variant="muted">{formatProfileCount(filteredSchemas.length)}</Badge>
              </div>
            </CardHeader>
            <CardContent className="grid gap-3 pt-4">
              <div className="relative">
                <Search className="pointer-events-none absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  aria-label="Search schemas"
                  className="w-full pl-8"
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Search schemas or fields"
                  value={query}
                />
              </div>
              <div className={cn("grid", filteredSchemas.length ? "divide-y divide-border" : "gap-2")}>
                {filteredSchemas.map((schema) => (
                  <button
                    className={cn(
                      "grid gap-2 rounded-md border border-transparent bg-card p-2.5 text-left transition-colors hover:border-primary/25 hover:bg-slate-50 focus-ring",
                      schema.schema_id === selectedSchema?.schema_id &&
                        "border-primary/35 bg-teal-50/75 shadow-[inset_3px_0_0_#087f7a]",
                    )}
                    key={schema.schema_id}
                    onClick={() => setSelectedSchemaId(schema.schema_id)}
                    type="button"
                  >
                    <div className="flex min-w-0 items-start justify-between gap-3">
                      <div className="min-w-0">
                        <div className="break-all font-bold">{schema.schema_id}</div>
                        <div className="mt-1 line-clamp-2 text-xs leading-5 text-muted-foreground">
                          {schema.title}
                        </div>
                      </div>
                      <Badge variant="muted">v{schema.version}</Badge>
                    </div>
                    <div className="flex flex-wrap gap-2 text-[11px] font-bold uppercase text-muted-foreground">
                      <span>{schema.field_count} fields</span>
                      <span>{schema.required.length} required</span>
                    </div>
                  </button>
                ))}
                {!filteredSchemas.length ? (
                  <Notice title="No matching schemas">
                    Clear the search to return to the full registry.
                  </Notice>
                ) : null}
              </div>
            </CardContent>
          </Card>

          <SchemaDetail schema={selectedSchema} />
        </div>
      ) : null}
    </div>
  );
}

function SchemaDetail({ schema }: { schema: SchemaEntry | null }) {
  if (!schema) {
    return (
      <Card className="min-h-[420px]">
        <CardContent className="grid h-full place-items-center p-8 text-center text-muted-foreground">
          Select a schema profile to inspect fields and governance metadata.
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid min-w-0 gap-4">
      <Card className="min-w-0 overflow-hidden">
        <CardHeader className="gap-3 border-b border-border bg-card/70 p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <CardDescription className="font-bold uppercase">Approved profile</CardDescription>
            <Badge variant="success">validation ready</Badge>
          </div>
          <div className="min-w-0">
            <CardTitle className="break-all font-mono text-xl leading-tight sm:text-2xl">
              {schema.schema_id}
            </CardTitle>
            <CardDescription className="mt-1">{schema.title} / version {schema.version}</CardDescription>
          </div>
          <div className="flex flex-wrap gap-2 text-xs font-semibold text-muted-foreground">
            <span className="rounded-full bg-muted px-2 py-1">{schema.field_count} fields</span>
            <span className="rounded-full bg-muted px-2 py-1">{schema.required.length} required</span>
            <span className="min-w-0 max-w-full break-all rounded-md bg-muted px-2 py-1 leading-relaxed">
              source {schema.source_ref}
            </span>
          </div>
        </CardHeader>
        <CardContent className="grid gap-3 pt-4">
          <div className="flex items-start gap-3">
            <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-primary" />
            <div className="min-w-0">
              <CardTitle className="text-sm">Required fields</CardTitle>
              <p className="mt-1 text-sm leading-6 text-muted-foreground">
                Records missing these fields are review-sensitive and should block automatic completion.
                <span className="ml-1 inline-flex align-middle">
                  <HelpTooltip label="Required fields help">
                    Required fields are the minimum data needed for this profile. If they are missing, the workflow should explain the issue instead of silently accepting the record.
                  </HelpTooltip>
                </span>
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                {schema.required.map((field) => (
                  <Badge key={field} variant="warning">{field}</Badge>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="min-w-0 overflow-hidden">
        <CardHeader className="border-b border-border bg-card/70 p-4">
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-primary" />
            Field contract
          </CardTitle>
          <CardDescription>Type expectations and field-level validation context.</CardDescription>
        </CardHeader>
        <CardContent className="p-0 md:p-4">
          <Table className="table-fixed" wrapperClassName="hidden rounded-md border border-border md:block">
            <THead>
              <TR>
                <TH className="w-[24%]">Field</TH>
                <TH className="w-[16%]">Type</TH>
                <TH className="w-[14%]">Policy</TH>
                <TH>Description</TH>
              </TR>
            </THead>
            <TBody>
              {schema.fields.map((field) => (
                <TR key={field.name}>
                  <TD className="truncate font-bold">{field.name}</TD>
                  <TD><Badge variant="muted">{field.type}</Badge></TD>
                  <TD>
                    {schema.required.includes(field.name) ? (
                      <Badge variant="warning">required</Badge>
                    ) : (
                      <Badge variant="muted">optional</Badge>
                    )}
                  </TD>
                  <TD className="text-muted-foreground">{field.description ?? "-"}</TD>
                </TR>
              ))}
            </TBody>
          </Table>
          <div className="grid gap-2 p-4 md:hidden">
            {schema.fields.map((field) => (
              <div className="grid gap-2 rounded-md border border-border bg-card p-2.5" key={field.name}>
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div className="break-all font-bold">{field.name}</div>
                  <Badge variant={schema.required.includes(field.name) ? "warning" : "muted"}>
                    {schema.required.includes(field.name) ? "required" : "optional"}
                  </Badge>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Badge variant="muted">{field.type}</Badge>
                </div>
                <p className="text-sm leading-6 text-muted-foreground">{field.description ?? "No description provided."}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function formatProfileCount(count: number) {
  return `${count} ${count === 1 ? "profile" : "profiles"}`;
}

function SchemaRegistrySkeleton() {
  return (
    <div
      aria-label="Loading schema registry"
      className="grid items-start gap-4 xl:grid-cols-[minmax(300px,0.42fr)_minmax(0,1fr)]"
      role="status"
    >
      <Card className="min-w-0 self-start overflow-hidden">
        <CardHeader className="border-b border-border bg-card/70 p-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="grid min-w-0 flex-1 gap-2">
              <Skeleton className="h-5 w-36 max-w-full" />
              <Skeleton className="h-4 w-full max-w-xs" />
            </div>
            <Skeleton className="h-6 w-24 rounded-full" />
          </div>
        </CardHeader>
        <CardContent className="grid gap-3 pt-4">
          <Skeleton className="h-9 w-full" />
          <div className="grid gap-2">
            {Array.from({ length: 4 }).map((_, index) => (
              <div
                aria-hidden="true"
                className="grid gap-2 rounded-md border border-border bg-card p-2.5"
                data-testid="schema-registry-skeleton-row"
                key={index}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="grid min-w-0 flex-1 gap-2">
                    <Skeleton className="h-5 w-40 max-w-full" />
                    <Skeleton className="h-4 w-full" />
                  </div>
                  <Skeleton className="h-6 w-10 rounded-full" />
                </div>
                <div className="flex flex-wrap gap-2">
                  <Skeleton className="h-4 w-16" />
                  <Skeleton className="h-4 w-20" />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="grid min-w-0 gap-4">
        <Card className="min-w-0 overflow-hidden">
          <CardHeader className="gap-3 border-b border-border bg-card/70 p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-6 w-28 rounded-full" />
            </div>
            <div className="grid gap-2">
              <Skeleton className="h-7 w-56 max-w-full" />
              <Skeleton className="h-4 w-full max-w-md" />
            </div>
            <div className="flex flex-wrap gap-2">
              <Skeleton className="h-6 w-20 rounded-full" />
              <Skeleton className="h-6 w-24 rounded-full" />
              <Skeleton className="h-6 w-44 rounded-md" />
            </div>
          </CardHeader>
          <CardContent className="grid gap-3 pt-4">
            <div className="flex items-start gap-3">
              <Skeleton className="mt-0.5 h-5 w-5 rounded-full" />
              <div className="grid min-w-0 flex-1 gap-2">
                <Skeleton className="h-5 w-36" />
                <Skeleton className="h-4 w-full max-w-lg" />
                <div className="flex flex-wrap gap-2">
                  <Skeleton className="h-6 w-20 rounded-full" />
                  <Skeleton className="h-6 w-24 rounded-full" />
                  <Skeleton className="h-6 w-16 rounded-full" />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="min-w-0 overflow-hidden">
          <CardHeader className="border-b border-border bg-card/70 p-4">
            <Skeleton className="h-5 w-36" />
            <Skeleton className="h-4 w-full max-w-md" />
          </CardHeader>
          <CardContent className="p-0 md:p-4">
            <Table className="table-fixed" wrapperClassName="hidden rounded-md border border-border md:block">
              <THead>
                <TR>
                  <TH className="w-[24%]">Field</TH>
                  <TH className="w-[16%]">Type</TH>
                  <TH className="w-[14%]">Policy</TH>
                  <TH>Description</TH>
                </TR>
              </THead>
              <TBody>
                {Array.from({ length: 5 }).map((_, index) => (
                  <TR aria-hidden="true" data-testid="schema-field-skeleton-row" key={index}>
                    <TD><Skeleton className="h-4 w-28" /></TD>
                    <TD><Skeleton className="h-6 w-16 rounded-full" /></TD>
                    <TD><Skeleton className="h-6 w-20 rounded-full" /></TD>
                    <TD><Skeleton className="h-4 w-full" /></TD>
                  </TR>
                ))}
              </TBody>
            </Table>
            <div className="grid gap-2 p-4 md:hidden">
              {Array.from({ length: 4 }).map((_, index) => (
                <div
                  aria-hidden="true"
                  className="grid gap-2 rounded-md border border-border bg-card p-2.5"
                  data-testid="schema-field-skeleton-card"
                  key={index}
                >
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <Skeleton className="h-5 w-32 max-w-full" />
                    <Skeleton className="h-6 w-20 rounded-full" />
                  </div>
                  <Skeleton className="h-6 w-16 rounded-full" />
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-3/4" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function filterSchemas(schemas: SchemaEntry[], query: string) {
  const normalized = query.trim().toLowerCase();
  if (!normalized) return schemas;
  return schemas.filter((schema) => {
    const haystack = [
      schema.schema_id,
      schema.title,
      schema.version,
      schema.source_ref,
      ...schema.required,
      ...schema.fields.flatMap((field) => [field.name, field.type, field.description ?? ""]),
    ]
      .join(" ")
      .toLowerCase();
    return haystack.includes(normalized);
  });
}
