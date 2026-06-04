import {
  CheckCircle2,
  Clock3,
  Database,
  HardDrive,
  KeyRound,
  Loader2,
  Save,
  Server,
  ShieldCheck,
  SlidersHorizontal,
  UploadCloud,
  UserRound,
  Users,
} from "lucide-react";
import * as React from "react";

import { useAuth } from "../../app/auth";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { Input, Label, Select } from "../../components/ui/form";
import { Notice } from "../../components/ui/notice";
import { PageHeader } from "../../components/layout/page-header";
import { SummaryStrip, SummaryStripItem } from "../../components/ui/summary-strip";
import {
  runtimeConfig,
  useExtractorInventoryQuery,
  useRuntimeConfigQuery,
  useRuntimeHealthQuery,
  useRuntimeReadinessQuery,
  useRuntimeRetrievalSettingsMutation,
  useSchemasQuery,
  workflowErrorMessage,
} from "../../lib/server-state";
import type {
  ReadinessCheck,
  RuntimeConfig,
  RuntimeReadiness,
  RuntimeRetrievalSettings,
  RuntimeRetrievalSettingsPayload,
} from "../../types";

export function SettingsPage() {
  const { user } = useAuth();
  const healthQuery = useRuntimeHealthQuery();
  const runtimeConfigQuery = useRuntimeConfigQuery();
  const readinessQuery = useRuntimeReadinessQuery();
  const schemasQuery = useSchemasQuery();
  const extractorsQuery = useExtractorInventoryQuery();
  const schemaCount = schemasQuery.data?.length ?? 0;
  const runtime = runtimeConfigQuery.data;
  const availableExtractors = extractorsQuery.data?.available ?? [];
  const supportedExtensions =
    runtime?.upload.allowed_extensions ?? extractorsQuery.data?.supported_extensions ?? [];
  const apiHealthy = healthQuery.data?.status === "ok";
  const readiness = readinessQuery.data;
  const readinessCounts = countReadinessChecks(readiness?.checks ?? []);
  const cookieEffectiveSecure =
    runtime?.auth.cookie_effective_secure ?? runtime?.auth.cookie_secure ?? false;
  const securityAttentionCount =
    (user ? 0 : 1) +
    (runtime?.auth.google_oauth_configured || runtimeConfigQuery.isLoading ? 0 : 1) +
    (runtimeConfigQuery.isLoading || cookieEffectiveSecure ? 0 : 1);

  return (
    <div className="grid gap-5">
      <PageHeader
        title="Settings"
        description="Runtime readiness, security posture, and integration scope for the local enterprise backend."
      />

      <RuntimeStatusStrip
        apiHealthy={apiHealthy}
        healthLoading={healthQuery.isLoading}
        healthUnavailable={healthQuery.isError}
        readiness={readiness}
        readinessLoading={readinessQuery.isLoading}
        runtime={runtime}
        runtimeLoading={runtimeConfigQuery.isLoading}
        runtimeUnavailable={runtimeConfigQuery.isError}
        schemaCount={schemaCount}
        schemaLoading={schemasQuery.isLoading}
        userEmail={user?.email ?? null}
      />

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.08fr)_minmax(360px,0.92fr)]">
        <Card className="min-w-0 overflow-hidden">
          <CardHeader className="border-b border-border bg-card/70">
            <CardTitle className="flex items-center gap-2">
              <Server className="h-5 w-5 text-primary" />
              Runtime configuration
            </CardTitle>
            <CardDescription>Runtime facts, backend dependencies, and configured data limits.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-5 pt-4 sm:pt-5">
            <div className="grid gap-3 lg:grid-cols-2">
              <RuntimeFactGroup icon={Server} title="Service endpoints">
                <SettingRow label="API base" value={runtimeConfig.apiBaseUrl} />
                <SettingRow
                  label="Health"
                  value={
                    healthQuery.isLoading
                      ? "Checking /health"
                      : apiHealthy
                        ? "Healthy"
                        : "Unavailable"
                  }
                  badge={apiHealthy ? "ok" : "attention"}
                />
                <SettingRow
                  label="Readiness"
                  value={
                    readinessQuery.isLoading
                      ? "Checking readiness"
                      : readiness
                        ? readinessLabel(readiness)
                        : "Unavailable"
                  }
                  badge={
                    readiness?.status === "ready"
                      ? "ready"
                      : readinessQuery.isLoading
                        ? undefined
                        : "attention"
                  }
                />
              </RuntimeFactGroup>

              <RuntimeFactGroup icon={HardDrive} title="Persistence">
                <SettingRow
                  label="Storage backend"
                  value={runtime?.storage_backend ?? runtimeConfigLabel(runtimeConfigQuery)}
                  badge={
                    runtime?.persistent_storage
                      ? "persistent"
                      : runtimeConfigQuery.isLoading
                        ? undefined
                        : "attention"
                  }
                />
                <SettingRow
                  label="Postgres"
                  value={
                    runtime?.postgres_configured
                      ? "Configured"
                      : runtimeConfigLabel(runtimeConfigQuery)
                  }
                  badge={
                    runtime?.postgres_configured
                      ? "configured"
                      : runtimeConfigQuery.isLoading
                        ? undefined
                        : "missing"
                  }
                />
                <SettingRow
                  label="Redis"
                  value={runtime?.redis_configured ? "Configured" : runtimeConfigLabel(runtimeConfigQuery)}
                  badge={
                    runtime?.redis_configured
                      ? "configured"
                      : runtimeConfigQuery.isLoading
                        ? undefined
                        : "missing"
                  }
                />
              </RuntimeFactGroup>

              <RuntimeFactGroup icon={UploadCloud} title="Data limits">
                <SettingRow
                  label="Upload limit"
                  value={
                    runtime
                      ? `${formatBytes(runtime.upload.max_upload_bytes)} max`
                      : runtimeConfigLabel(runtimeConfigQuery)
                  }
                />
                <SettingRow
                  label="Read chunk"
                  value={
                    runtime
                      ? formatBytes(runtime.upload.read_chunk_bytes)
                      : runtimeConfigLabel(runtimeConfigQuery)
                  }
                />
                <SettingRow
                  label="Inline data limit"
                  value={
                    runtime
                      ? `${formatBytes(runtime.upload.max_inline_data_bytes)} max`
                      : runtimeConfigLabel(runtimeConfigQuery)
                  }
                />
              </RuntimeFactGroup>

              <RuntimeFactGroup icon={UserRound} title="Identity and retrieval AI">
                <SettingRow
                  label="User"
                  value={user?.email ?? "No active session"}
                  badge={user ? "verified" : "missing"}
                />
                <SettingRow
                  label="Provider"
                  value={runtime?.embedding.provider ?? runtimeConfigLabel(runtimeConfigQuery)}
                />
                <SettingRow
                  label="Model"
                  value={
                    runtime
                      ? `${runtime.embedding.model} / ${runtime.embedding.dimensions}d`
                      : runtimeConfigLabel(runtimeConfigQuery)
                  }
                />
                <SettingRow
                  label="Reranker"
                  value={
                    runtime
                      ? runtime.rerank?.enabled
                        ? `${runtime.rerank.provider} / ${runtime.rerank.device}`
                        : "disabled"
                      : runtimeConfigLabel(runtimeConfigQuery)
                  }
                  badge={
                    runtime?.rerank?.enabled
                      ? "configured"
                      : runtimeConfigQuery.isLoading
                        ? undefined
                        : "offline"
                  }
                />
                <SettingRow
                  label="Rerank model"
                  value={
                    runtime
                      ? runtime.rerank?.enabled
                        ? `${runtime.rerank.model} / top ${runtime.rerank.candidate_limit}`
                        : "First-stage hybrid only"
                      : runtimeConfigLabel(runtimeConfigQuery)
                  }
                />
                <SettingRow
                  label="Retrieval framework"
                  value={
                    runtime
                      ? runtime.retrieval?.framework ?? "custom"
                      : runtimeConfigLabel(runtimeConfigQuery)
                  }
                  badge={
                    runtime?.retrieval?.framework === "llamaindex"
                      ? "configured"
                      : runtimeConfigQuery.isLoading
                        ? undefined
                        : "native"
                  }
                />
                <SettingRow
                  label="Diversity"
                  value={
                    runtime
                      ? runtime.retrieval?.diversity_enabled
                        ? `MMR / lambda ${runtime.retrieval.diversity_lambda?.toFixed(2) ?? "n/a"}`
                        : "Score order"
                      : runtimeConfigLabel(runtimeConfigQuery)
                  }
                  badge={
                    runtime?.retrieval?.diversity_enabled
                      ? "configured"
                      : runtimeConfigQuery.isLoading
                        ? undefined
                        : "disabled"
                  }
                />
                <SettingRow
                  label="HNSW search"
                  value={
                    runtime
                      ? runtime.retrieval?.hnsw_ef_search
                        ? `ef_search ${runtime.retrieval.hnsw_ef_search}`
                        : "Postgres vector tuning unavailable"
                      : runtimeConfigLabel(runtimeConfigQuery)
                  }
                />
              </RuntimeFactGroup>
            </div>

            <div className="border-t border-border pt-5">
              <SectionTitle
                description="Sanitized backend checks for storage, artifacts, retrieval, and governance inventory."
                icon={CheckCircle2}
                title="Readiness checks"
              />
              <div className="mt-3 grid gap-2 text-sm sm:grid-cols-3">
                <ReadinessCounter label="Ok" tone="success" value={readinessCounts.ok} />
                <ReadinessCounter label="Warning" tone="warning" value={readinessCounts.warning} />
                <ReadinessCounter label="Failed" tone="danger" value={readinessCounts.failed} />
              </div>
              <div className="mt-3">
                <ReadinessChecks
                  checks={readiness?.checks ?? []}
                  isError={readinessQuery.isError}
                  isLoading={readinessQuery.isLoading}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid min-w-0 gap-4">
          <Card className="min-w-0 overflow-hidden">
            <CardHeader className="border-b border-border bg-card/70">
              <div className="flex min-w-0 flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <CardTitle className="flex items-center gap-2">
                    <KeyRound className="h-5 w-5 text-primary" />
                    Security posture
                  </CardTitle>
                  <CardDescription>
                    Controls that protect healthcare data workflow decisions.
                  </CardDescription>
                </div>
                <Badge variant={securityAttentionCount ? "warning" : "success"}>
                  {securityAttentionCount ? `${securityAttentionCount} attention` : "all active"}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="grid gap-2 pt-4 sm:pt-5">
              <ControlStatus title="Google OAuth session" status={user ? "active" : "attention"}>
                Session identity is attached to review decisions and audit events.
              </ControlStatus>
              <ControlStatus
                title="OAuth client configuration"
                status={
                  runtime?.auth.google_oauth_configured
                    ? "active"
                    : runtimeConfigQuery.isLoading
                      ? "planned"
                      : "attention"
                }
              >
                Backend reports only whether OAuth credentials are configured; client secrets are never exposed.
              </ControlStatus>
              <ControlStatus title="Human review gate" status="active">
                Meaning-changing transformations remain blocked until a reviewer approves them.
              </ControlStatus>
              <ControlStatus title="User ownership scope" status="active">
                Workflow, review, retrieval, and output reads are scoped to the authenticated owner.
              </ControlStatus>
              <ControlStatus
                title="Cookie policy"
                status={
                  runtimeConfigQuery.isLoading
                    ? "planned"
                    : cookieEffectiveSecure
                      ? "active"
                      : "attention"
                }
              >
                SameSite is {runtime?.auth.cookie_samesite ?? "unknown"}; effective Secure is{" "}
                {runtimeConfigQuery.isLoading ? "checking" : cookieEffectiveSecure ? "on" : "off"}.
              </ControlStatus>
            </CardContent>
          </Card>

          <Card className="min-w-0 overflow-hidden">
            <CardHeader className="border-b border-border bg-card/70">
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5 text-primary" />
                Governance inventory
              </CardTitle>
              <CardDescription>Validation and retrieval grounding assets currently available.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4 pt-4 sm:pt-5">
              <InventoryGroup count={schemaCount} title="Schema profiles">
                {(schemasQuery.data ?? []).map((schema) => (
                  <Badge key={schema.schema_id} variant="muted">
                    {schema.schema_id} / {schema.version}
                  </Badge>
                ))}
                {!schemaCount ? <Badge variant="warning">No schemas loaded</Badge> : null}
              </InventoryGroup>
              <InventoryGroup count={availableExtractors.length} title="Extractor engines">
                {availableExtractors.map((extractor) => (
                  <Badge key={extractor} variant="success">
                    {extractor}
                  </Badge>
                ))}
                {!availableExtractors.length ? <Badge variant="warning">No document engines</Badge> : null}
              </InventoryGroup>
              <InventoryGroup count={supportedExtensions.length} title="Supported upload formats">
                {supportedExtensions.slice(0, 16).map((extension) => (
                  <Badge key={extension} variant="default">
                    {extension}
                  </Badge>
                ))}
                {supportedExtensions.length > 16 ? (
                  <Badge variant="muted">+{supportedExtensions.length - 16} more</Badge>
                ) : null}
              </InventoryGroup>
            </CardContent>
          </Card>

          <RetrievalSettingsForm
            isLoading={runtimeConfigQuery.isLoading}
            runtime={runtime}
          />
        </div>

        <Card className="min-w-0 overflow-hidden xl:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5 text-primary" />
              Operational policy
            </CardTitle>
            <CardDescription>How this backend should be operated before production expansion.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-0 text-sm text-muted-foreground">
            <PolicyItem title="Reviewer accountability">
              Review decisions use the authenticated session user, not client-supplied identity.
            </PolicyItem>
            <PolicyItem title="Audit durability">
              Workflow events and step state are persisted before a user-facing transition is returned.
            </PolicyItem>
            <PolicyItem title="FHIR/OCR scope">
              FHIR-like profiling and OCR evidence are contract stubs until dedicated validators are added.
            </PolicyItem>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

type RetrievalSettingsFormState = {
  framework: "custom" | "llamaindex";
  candidateMultiplier: string;
  minCandidates: string;
  vectorWeight: string;
  bm25Weight: string;
  diversityEnabled: boolean;
  diversityLambda: string;
  hnswEfSearch: string;
};

function RetrievalSettingsForm({
  isLoading,
  runtime,
}: {
  isLoading: boolean;
  runtime: RuntimeConfig | undefined;
}) {
  const mutation = useRuntimeRetrievalSettingsMutation();
  const [form, setForm] = React.useState<RetrievalSettingsFormState | null>(null);
  const [localError, setLocalError] = React.useState<string | null>(null);

  React.useEffect(() => {
    const settings = runtimeRetrievalSettingsFromRuntime(runtime);
    if (!settings) return;
    setForm({
      framework: settings.retrieval_framework,
      candidateMultiplier: String(settings.retrieval_candidate_multiplier),
      minCandidates: String(settings.retrieval_min_candidates),
      vectorWeight: String(settings.retrieval_vector_weight),
      bm25Weight: String(settings.retrieval_bm25_weight),
      diversityEnabled: settings.retrieval_diversity_enabled,
      diversityLambda: String(settings.retrieval_diversity_lambda),
      hnswEfSearch: String(settings.retrieval_hnsw_ef_search),
    });
  }, [runtime]);

  const updateField = <Key extends keyof RetrievalSettingsFormState>(
    key: Key,
    value: RetrievalSettingsFormState[Key],
  ) => {
    setForm((current) => (current ? { ...current, [key]: value } : current));
    if (localError) setLocalError(null);
  };

  const save = (event: React.FormEvent) => {
    event.preventDefault();
    if (!form) return;
    try {
      mutation.mutate(runtimeRetrievalPayloadFromForm(form));
    } catch (error) {
      setLocalError(error instanceof Error ? error.message : String(error));
    }
  };

  return (
    <Card className="min-w-0 overflow-hidden">
      <CardHeader className="border-b border-border bg-card/70">
        <div className="flex min-w-0 flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <CardTitle className="flex items-center gap-2">
              <SlidersHorizontal className="h-5 w-5 text-primary" />
              Retrieval runtime
            </CardTitle>
            <CardDescription>Operator-tuned search framework and ranking controls.</CardDescription>
          </div>
          {runtime?.retrieval?.runtime_settings_configured ? (
            <Badge variant="success">reloadable</Badge>
          ) : (
            <Badge variant="muted">config-backed</Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="pt-4 sm:pt-5">
        {!form ? (
          <Notice title={isLoading ? "Runtime loading" : "Runtime settings unavailable"}>
            Backend runtime config has not returned editable retrieval settings.
          </Notice>
        ) : (
          <form className="grid gap-4" onSubmit={save}>
            {localError ? (
              <Notice title="Settings blocked" tone="danger">
                {localError}
              </Notice>
            ) : null}
            {mutation.isError ? (
              <Notice title="Settings update failed" tone="danger">
                {workflowErrorMessage(mutation.error)}
              </Notice>
            ) : null}
            {mutation.data?.reloaded ? (
              <Notice title="Settings reloaded">
                Active framework is {mutation.data.settings.retrieval_framework}.
              </Notice>
            ) : null}

            <div className="grid gap-3 sm:grid-cols-2">
              <Label>
                Framework
                <Select
                  onChange={(event) =>
                    updateField(
                      "framework",
                      event.target.value === "llamaindex" ? "llamaindex" : "custom",
                    )
                  }
                  value={form.framework}
                >
                  <option value="custom">Custom</option>
                  <option value="llamaindex">LlamaIndex</option>
                </Select>
              </Label>
              <Label>
                Candidate multiplier
                <Input
                  min={1}
                  max={20}
                  onChange={(event) => updateField("candidateMultiplier", event.target.value)}
                  type="number"
                  value={form.candidateMultiplier}
                />
              </Label>
              <Label>
                Minimum candidates
                <Input
                  min={1}
                  max={200}
                  onChange={(event) => updateField("minCandidates", event.target.value)}
                  type="number"
                  value={form.minCandidates}
                />
              </Label>
              <Label>
                HNSW ef_search
                <Input
                  min={1}
                  max={1000}
                  onChange={(event) => updateField("hnswEfSearch", event.target.value)}
                  type="number"
                  value={form.hnswEfSearch}
                />
              </Label>
              <Label>
                Vector weight
                <Input
                  min={0}
                  max={1}
                  onChange={(event) => updateField("vectorWeight", event.target.value)}
                  step={0.01}
                  type="number"
                  value={form.vectorWeight}
                />
              </Label>
              <Label>
                BM25 weight
                <Input
                  min={0}
                  max={1}
                  onChange={(event) => updateField("bm25Weight", event.target.value)}
                  step={0.01}
                  type="number"
                  value={form.bm25Weight}
                />
              </Label>
              <Label>
                Diversity lambda
                <Input
                  min={0}
                  max={1}
                  onChange={(event) => updateField("diversityLambda", event.target.value)}
                  step={0.01}
                  type="number"
                  value={form.diversityLambda}
                />
              </Label>
              <label className="flex min-h-9 items-center gap-2 rounded-md border border-border bg-muted/20 px-3 text-sm font-semibold">
                <input
                  checked={form.diversityEnabled}
                  className="h-4 w-4 accent-primary"
                  onChange={(event) => updateField("diversityEnabled", event.target.checked)}
                  type="checkbox"
                />
                Source diversity
              </label>
            </div>

            <Button disabled={mutation.isPending} type="submit">
              {mutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Save className="h-4 w-4" />
              )}
              Save and reload
            </Button>
          </form>
        )}
      </CardContent>
    </Card>
  );
}

function runtimeRetrievalSettingsFromRuntime(
  runtime: RuntimeConfig | undefined,
): RuntimeRetrievalSettings | null {
  const retrieval = runtime?.retrieval;
  const settings = retrieval?.runtime_settings;
  if (settings) return settings;
  if (!retrieval) return null;
  const framework = retrieval.framework === "llamaindex" ? "llamaindex" : "custom";
  if (
    !isFiniteNumber(retrieval.candidate_multiplier) ||
    !isFiniteNumber(retrieval.min_candidates) ||
    !isFiniteNumber(retrieval.vector_weight) ||
    !isFiniteNumber(retrieval.bm25_weight) ||
    typeof retrieval.diversity_enabled !== "boolean" ||
    !isFiniteNumber(retrieval.diversity_lambda) ||
    !isFiniteNumber(retrieval.hnsw_ef_search)
  ) {
    return null;
  }
  return {
    retrieval_framework: framework,
    retrieval_candidate_multiplier: retrieval.candidate_multiplier,
    retrieval_min_candidates: retrieval.min_candidates,
    retrieval_vector_weight: retrieval.vector_weight,
    retrieval_bm25_weight: retrieval.bm25_weight,
    retrieval_diversity_enabled: retrieval.diversity_enabled,
    retrieval_diversity_lambda: retrieval.diversity_lambda,
    retrieval_hnsw_ef_search: retrieval.hnsw_ef_search,
  };
}

function runtimeRetrievalPayloadFromForm(
  form: RetrievalSettingsFormState,
): RuntimeRetrievalSettingsPayload {
  const retrieval_vector_weight = numberField(form.vectorWeight, "Vector weight", 0, 1);
  const retrieval_bm25_weight = numberField(form.bm25Weight, "BM25 weight", 0, 1);
  if (retrieval_vector_weight + retrieval_bm25_weight <= 0) {
    throw new Error("Vector and BM25 weights cannot both be zero.");
  }
  return {
    retrieval_framework: form.framework,
    retrieval_candidate_multiplier: integerField(
      form.candidateMultiplier,
      "Candidate multiplier",
      1,
      20,
    ),
    retrieval_min_candidates: integerField(form.minCandidates, "Minimum candidates", 1, 200),
    retrieval_vector_weight,
    retrieval_bm25_weight,
    retrieval_diversity_enabled: form.diversityEnabled,
    retrieval_diversity_lambda: numberField(form.diversityLambda, "Diversity lambda", 0, 1),
    retrieval_hnsw_ef_search: integerField(form.hnswEfSearch, "HNSW ef_search", 1, 1000),
  };
}

function integerField(raw: string, label: string, min: number, max: number) {
  const value = numberField(raw, label, min, max);
  if (!Number.isInteger(value)) {
    throw new Error(`${label} must be an integer.`);
  }
  return value;
}

function numberField(raw: string, label: string, min: number, max: number) {
  const value = Number(raw);
  if (!Number.isFinite(value) || value < min || value > max) {
    throw new Error(`${label} must be between ${min} and ${max}.`);
  }
  return value;
}

function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function readinessLabel(readiness: RuntimeReadiness | undefined) {
  if (!readiness) return "unavailable";
  if (readiness.status === "not_ready") return "not ready";
  return readiness.status;
}

function readinessTone(
  readiness: RuntimeReadiness | undefined,
  isLoading: boolean,
): "success" | "warning" | "neutral" {
  if (isLoading) return "neutral";
  return readiness?.status === "ready" ? "success" : "warning";
}

function countReadinessChecks(checks: ReadinessCheck[]) {
  return checks.reduce(
    (counts, check) => {
      if (check.status === "ok") counts.ok += 1;
      else if (check.status === "warning") counts.warning += 1;
      else counts.failed += 1;
      return counts;
    },
    { failed: 0, ok: 0, warning: 0 },
  );
}

function RuntimeStatusStrip({
  apiHealthy,
  healthLoading,
  healthUnavailable,
  readiness,
  readinessLoading,
  runtime,
  runtimeLoading,
  runtimeUnavailable,
  schemaCount,
  schemaLoading,
  userEmail,
}: {
  apiHealthy: boolean;
  healthLoading: boolean;
  healthUnavailable: boolean;
  readiness: RuntimeReadiness | undefined;
  readinessLoading: boolean;
  runtime: RuntimeConfig | undefined;
  runtimeLoading: boolean;
  runtimeUnavailable: boolean;
  schemaCount: number;
  schemaLoading: boolean;
  userEmail: string | null;
}) {
  return (
    <SummaryStrip columns={5}>
      <SummaryStripItem
        icon={Server}
        label="API health"
        supporting={healthUnavailable ? "Health endpoint failed" : "Runtime endpoint"}
        tone={apiHealthy ? "success" : healthLoading ? "neutral" : "warning"}
        value={healthLoading ? "checking" : apiHealthy ? "ok" : "attention"}
      />
      <SummaryStripItem
        icon={CheckCircle2}
        label="Readiness"
        supporting={readiness ? `${readiness.checks.length} runtime checks` : "Readiness endpoint failed"}
        tone={readinessTone(readiness, readinessLoading)}
        value={readinessLoading ? "checking" : readinessLabel(readiness)}
      />
      <SummaryStripItem
        icon={Database}
        label="Storage"
        supporting={
          runtimeUnavailable
            ? "Runtime config failed"
            : runtime?.persistent_storage
              ? "Persistent backend"
              : "Ephemeral backend"
        }
        tone={runtime?.persistent_storage ? "success" : runtimeLoading ? "neutral" : "warning"}
        value={runtimeLoading ? "checking" : runtime?.storage_backend ?? "unknown"}
      />
      <SummaryStripItem
        icon={ShieldCheck}
        label="Session"
        supporting={userEmail ?? "No active user"}
        tone={userEmail ? "success" : "warning"}
        value={userEmail ? "active" : "missing"}
      />
      <SummaryStripItem
        icon={Database}
        label="Schemas"
        loading={schemaLoading}
        supporting="Approved validation profiles"
        tone={schemaCount > 0 ? "success" : schemaLoading ? "neutral" : "warning"}
        value={schemaCount}
      />
    </SummaryStrip>
  );
}

function SectionTitle({
  description,
  icon: Icon,
  title,
}: {
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  title: string;
}) {
  return (
    <div className="min-w-0">
      <CardTitle className="flex items-center gap-2">
        <Icon className="h-5 w-5 text-primary" />
        {title}
      </CardTitle>
      <CardDescription className="mt-1">{description}</CardDescription>
    </div>
  );
}

function RuntimeFactGroup({
  children,
  icon: Icon,
  title,
}: {
  children: React.ReactNode;
  icon: React.ComponentType<{ className?: string }>;
  title: string;
}) {
  return (
    <section className="min-w-0 border-t border-border pt-3 first:border-t-0 first:pt-0 lg:border-t-0 lg:pt-0">
      <div className="mb-2 flex min-w-0 items-center gap-2">
        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
          <Icon className="h-4 w-4" />
        </span>
        <h3 className="min-w-0 text-sm font-extrabold">{title}</h3>
      </div>
      <div className="grid gap-0">{children}</div>
    </section>
  );
}

function ReadinessCounter({
  label,
  tone,
  value,
}: {
  label: string;
  tone: "danger" | "success" | "warning";
  value: number;
}) {
  const toneClass =
    tone === "success"
      ? "border-emerald-200 bg-emerald-50 text-emerald-900"
      : tone === "warning"
        ? "border-amber-200 bg-amber-50 text-amber-900"
        : "border-red-200 bg-red-50 text-red-900";
  return (
    <div className={`rounded-md border px-3 py-2 ${toneClass}`}>
      <div className="text-[11px] font-bold uppercase leading-tight">{label}</div>
      <div className="mt-0.5 text-xl font-black tabular-nums">{value}</div>
    </div>
  );
}

function InventoryGroup({
  children,
  count,
  title,
}: {
  children: React.ReactNode;
  count: number;
  title: string;
}) {
  return (
    <div className="grid gap-2">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="text-sm font-bold">{title}</div>
        <Badge variant={count ? "muted" : "warning"}>{count}</Badge>
      </div>
      <div className="flex flex-wrap gap-2">{children}</div>
    </div>
  );
}

function SettingRow({ badge, label, value }: { badge?: string; label: string; value: string }) {
  const badgeVariant: React.ComponentProps<typeof Badge>["variant"] =
    badge === "attention" || badge === "missing"
      ? "warning"
      : badge === "offline" || badge === "disabled"
        ? "muted"
        : "success";
  return (
    <div className="grid gap-1 border-b border-border py-2 last:border-b-0">
      <div className="text-xs font-bold uppercase text-muted-foreground">{label}</div>
      <div className="flex min-w-0 flex-wrap items-center gap-2 text-sm">
        <span className="break-words font-semibold">{value}</span>
        {badge ? <Badge variant={badgeVariant}>{badge}</Badge> : null}
      </div>
    </div>
  );
}

function ReadinessChecks({
  checks,
  isError,
  isLoading,
}: {
  checks: ReadinessCheck[];
  isError: boolean;
  isLoading: boolean;
}) {
  if (isLoading) {
    return <div className="text-sm text-muted-foreground">Checking runtime readiness.</div>;
  }
  if (isError) {
    return <Badge variant="warning">Readiness unavailable</Badge>;
  }
  if (!checks.length) {
    return <Badge variant="warning">No checks reported</Badge>;
  }
  return (
    <div className="grid gap-2">
      {checks.map((check) => (
        <div
          className="grid gap-1 border-b border-border py-2.5 last:border-b-0"
          key={check.name}
        >
          <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
            <div className="min-w-0 break-words text-sm font-bold">{humanizeCheckName(check.name)}</div>
            <Badge
              variant={
                check.status === "ok"
                  ? "success"
                  : check.status === "warning"
                    ? "warning"
                    : "destructive"
              }
            >
              {check.status}
            </Badge>
          </div>
          <p className="text-sm leading-5 text-muted-foreground">{check.summary}</p>
          <ReadinessDetailChips details={check.details} />
        </div>
      ))}
    </div>
  );
}

function ReadinessDetailChips({ details }: { details: Record<string, unknown> }) {
  const entries = readinessDetailEntries(details);
  if (!entries.length) return null;
  return (
    <div className="flex min-w-0 flex-wrap gap-2">
      {entries.map((entry) => (
        <span
          className="min-w-0 rounded-full bg-muted px-2 py-1 text-[11px] font-semibold text-muted-foreground"
          key={entry.label}
        >
          {entry.label} {entry.value}
        </span>
      ))}
    </div>
  );
}

function readinessDetailEntries(details: Record<string, unknown>) {
  return Object.entries(details)
    .flatMap(([key, value]) => {
      if (typeof value === "boolean") {
        return [{ label: formatDetailLabel(key), value: value ? "yes" : "no" }];
      }
      if (typeof value === "number" && Number.isFinite(value)) {
        return [{ label: formatDetailLabel(key), value: String(value) }];
      }
      if (typeof value === "string" && value.trim()) {
        return [{ label: formatDetailLabel(key), value }];
      }
      return [];
    })
    .slice(0, 5);
}

function formatDetailLabel(value: string) {
  return value.replaceAll("_", " ");
}

function humanizeCheckName(value: string) {
  return value.replaceAll("_", " ");
}

function runtimeConfigLabel(query: { isLoading: boolean; isError: boolean }) {
  if (query.isLoading) return "Checking runtime config";
  if (query.isError) return "Runtime config unavailable";
  return "Not configured";
}

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function ControlStatus({
  children,
  status,
  title,
}: {
  children: React.ReactNode;
  status: "active" | "attention" | "planned";
  title: string;
}) {
  const Icon = status === "active" ? CheckCircle2 : Clock3;
  return (
    <div className="grid grid-cols-[24px_minmax(0,1fr)] gap-3 border-b border-border py-3 last:border-b-0">
      <Icon
        className={
          status === "active"
            ? "mt-0.5 h-5 w-5 text-emerald-700"
            : "mt-0.5 h-5 w-5 text-amber-700"
        }
      />
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <div className="font-bold">{title}</div>
          <Badge
            variant={status === "active" ? "success" : status === "attention" ? "warning" : "muted"}
          >
            {status}
          </Badge>
        </div>
        <p className="mt-1 text-sm leading-6 text-muted-foreground">{children}</p>
      </div>
    </div>
  );
}

function PolicyItem({ children, title }: { children: React.ReactNode; title: string }) {
  return (
    <div className="grid gap-1 border-b border-border py-3 last:border-b-0 sm:grid-cols-[220px_minmax(0,1fr)]">
      <div className="font-bold text-foreground">{title}</div>
      <p className="leading-6">{children}</p>
    </div>
  );
}
