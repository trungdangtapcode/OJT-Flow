import {
  Bot,
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
import { WorkspacesPanel } from "./workspaces-panel";
import {
  runtimeConfig,
  useExtractorInventoryQuery,
  useRuntimeAiRiskRegisterQuery,
  useRuntimeConfigQuery,
  useRuntimeHealthQuery,
  useRuntimeMigrationsQuery,
  useRuntimeOwaspLlmThreatModelQuery,
  useRuntimeReadinessQuery,
  useRuntimeAssistantSettingsMutation,
  useRuntimeRetrievalSettingsMutation,
  useSchemasQuery,
  workflowErrorMessage,
} from "../../lib/server-state";
import type {
  AiRiskLevel,
  AiRiskRegister,
  OwaspLlmThreatModel,
  ThreatRiskLevel,
  ReadinessCheck,
  RuntimeAssistantSettings,
  RuntimeAssistantSettingsPayload,
  RuntimeConfig,
  MigrationDiagnostics,
  RuntimeReadiness,
  RuntimeRetrievalRulePack,
  RuntimeRetrievalSettings,
  RuntimeRetrievalSettingsPayload,
} from "../../types";

export function SettingsPage() {
  const { user } = useAuth();
  const healthQuery = useRuntimeHealthQuery();
  const runtimeConfigQuery = useRuntimeConfigQuery();
  const migrationsQuery = useRuntimeMigrationsQuery();
  const readinessQuery = useRuntimeReadinessQuery();
  const aiRiskQuery = useRuntimeAiRiskRegisterQuery();
  const owaspQuery = useRuntimeOwaspLlmThreatModelQuery();
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
  const authConfigured =
    runtime?.auth.auth_configured ?? runtime?.auth.google_oauth_configured ?? false;
  const authProviderLabel =
    runtime?.auth.provider === "keycloak" ? "Keycloak SSO" : "Google OAuth";
  const productionLikeMode =
    runtime?.product_mode === "production" || runtime?.product_mode === "pilot";
  const dataPolicyNeedsAttention =
    productionLikeMode && runtime?.policy.effective_no_mock_data === false;
  const llmPolicyNeedsAttention =
    productionLikeMode && runtime?.policy.requires_real_llm === false;
  const cookieNeedsAttention =
    productionLikeMode && !runtimeConfigQuery.isLoading && !cookieEffectiveSecure;
  const securityAttentionCount =
    (user ? 0 : 1) +
    (authConfigured || runtimeConfigQuery.isLoading ? 0 : 1) +
    (dataPolicyNeedsAttention ? 1 : 0) +
    (llmPolicyNeedsAttention ? 1 : 0) +
    (cookieNeedsAttention ? 1 : 0);

  return (
    <div className="grid gap-5">
      <PageHeader
        title="Settings"
        description="Runtime configuration and security posture."
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

      <WorkspacesPanel />

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.08fr)_minmax(360px,0.92fr)]">
        <Card className="min-w-0 overflow-hidden">
          <CardHeader className="border-b border-border/60 bg-muted/30">
            <CardTitle className="flex items-center gap-2">
              <Server className="h-5 w-5 text-primary" />
              Runtime configuration
            </CardTitle>
            <CardDescription>Backend dependencies and data limits.</CardDescription>
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
                  label="Product mode"
                  value={runtime?.product_mode ?? runtimeConfigLabel(runtimeConfigQuery)}
                  badge={
                    runtime?.product_mode === "production" || runtime?.product_mode === "pilot"
                      ? "controlled"
                      : runtimeConfigQuery.isLoading
                        ? undefined
                        : "local"
                  }
                />
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
                  label="Embedding"
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
                description="Backend readiness checks."
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
            <CardHeader className="border-b border-border/60 bg-muted/30">
              <div className="flex min-w-0 flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <CardTitle className="flex items-center gap-2">
                    <KeyRound className="h-5 w-5 text-primary" />
                    Security posture
                  </CardTitle>
                  <CardDescription>Active security controls.</CardDescription>
                </div>
                <Badge variant={securityAttentionCount ? "warning" : "success"}>
                  {securityAttentionCount ? `${securityAttentionCount} attention` : "all active"}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="grid gap-2 pt-4 sm:pt-5">
              <ControlStatus
                title={`${authProviderLabel} session`}
                status={user ? "active" : "attention"}
              >
                Identity for reviews and audit.
              </ControlStatus>
              <ControlStatus
                title={`${authProviderLabel} config`}
                badgeLabel={runtimeConfigQuery.isLoading ? "checking" : undefined}
                status={
                  authConfigured
                    ? "active"
                    : runtimeConfigQuery.isLoading
                      ? "planned"
                      : "attention"
                }
              >
                OAuth credentials configured.
              </ControlStatus>
              <ControlStatus title="Human review gate" status="active">
                Blocks meaning-changing transforms.
              </ControlStatus>
              <ControlStatus title="Ownership scope" status="active">
                Data scoped to authenticated owner.
              </ControlStatus>
              <ControlStatus
                title="Production data policy"
                status={
                  runtimeConfigQuery.isLoading
                    ? "planned"
                    : runtime?.policy.effective_no_mock_data
                      ? "active"
                      : dataPolicyNeedsAttention
                        ? "attention"
                        : "planned"
                }
                badgeLabel={
                  runtimeConfigQuery.isLoading
                    ? "checking"
                    : runtime?.policy.effective_no_mock_data
                      ? "enforced"
                      : dataPolicyNeedsAttention
                        ? "required"
                        : "dev mode"
                }
              >
                {runtimeConfigQuery.isLoading
                  ? "Checking runtime data policy."
                  : runtime?.policy.effective_no_mock_data
                    ? "Mock/demo data is blocked for this runtime."
                    : "Local development may use sample data; pilot and production block it."}
              </ControlStatus>
              <ControlStatus
                title="AI provider enforcement"
                status={
                  runtimeConfigQuery.isLoading
                    ? "planned"
                    : runtime?.policy.requires_real_llm
                      ? "active"
                      : llmPolicyNeedsAttention
                        ? "attention"
                        : "planned"
                }
                badgeLabel={
                  runtimeConfigQuery.isLoading
                    ? "checking"
                    : runtime?.policy.requires_real_llm
                      ? "enforced"
                      : llmPolicyNeedsAttention
                        ? "required"
                        : "dev mode"
                }
              >
                {runtimeConfigQuery.isLoading
                  ? "Checking Assistant provider policy."
                  : runtime?.policy.requires_real_llm
                    ? "Assistant startup requires a configured real LLM."
                    : "Local development may run without an LLM; pilot and production fail startup without one."}
              </ControlStatus>
              <ControlStatus
                title="Browser session cookie"
                status={
                  runtimeConfigQuery.isLoading
                    ? "planned"
                    : cookieEffectiveSecure
                      ? "active"
                      : cookieNeedsAttention
                        ? "attention"
                        : "planned"
                }
                badgeLabel={
                  runtimeConfigQuery.isLoading
                    ? "checking"
                    : cookieEffectiveSecure
                      ? "secure"
                      : cookieNeedsAttention
                        ? "required"
                        : "localhost"
                }
              >
                {runtimeConfigQuery.isLoading
                  ? "Checking cookie security."
                  : cookieEffectiveSecure
                    ? "Secure cookies are active for this browser session."
                    : "Secure cookies are off for localhost; production should run behind HTTPS."}
              </ControlStatus>
            </CardContent>
          </Card>

          <Card className="min-w-0 overflow-hidden">
            <CardHeader className="border-b border-border/60 bg-muted/30">
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5 text-primary" />
                Governance inventory
              </CardTitle>
              <CardDescription>Schemas, extractors, and upload formats.</CardDescription>
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

          <MigrationAdminPanel
            diagnostics={migrationsQuery.data}
            error={migrationsQuery.isError ? workflowErrorMessage(migrationsQuery.error) : null}
            isLoading={migrationsQuery.isLoading}
          />

          <AssistantSettingsForm
            isLoading={runtimeConfigQuery.isLoading}
            runtime={runtime}
          />

          <RetrievalSettingsForm
            isLoading={runtimeConfigQuery.isLoading}
            runtime={runtime}
          />
        </div>

        <AdminPolicyPanel isLoading={runtimeConfigQuery.isLoading} runtime={runtime} />
        <AiRiskRegisterPanel
          error={aiRiskQuery.isError ? workflowErrorMessage(aiRiskQuery.error) : null}
          isLoading={aiRiskQuery.isLoading}
          register={aiRiskQuery.data}
        />
        <OwaspLlmThreatModelPanel
          error={owaspQuery.isError ? workflowErrorMessage(owaspQuery.error) : null}
          isLoading={owaspQuery.isLoading}
          model={owaspQuery.data}
        />
      </div>
    </div>
  );
}

function AiRiskRegisterPanel({
  error,
  isLoading,
  register,
}: {
  error: string | null;
  isLoading: boolean;
  register: AiRiskRegister | undefined;
}) {
  const criticalCount = register?.risks.filter((risk) => risk.severity === "critical").length ?? 0;
  const highCount = register?.risks.filter((risk) => risk.severity === "high").length ?? 0;
  const implementedControlCount =
    register?.risks.reduce(
      (count, risk) =>
        count + risk.controls.filter((control) => control.status === "implemented").length,
      0,
    ) ?? 0;
  const nistFunctions = Array.from(
    new Set(register?.risks.flatMap((risk) => risk.nist_ai_rmf_functions) ?? []),
  );

  return (
    <Card className="min-w-0 overflow-hidden xl:col-span-2">
      <CardHeader className="border-b border-border/60 bg-muted/30">
        <div className="flex min-w-0 flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <CardTitle className="flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-primary" />
              AI risk register
            </CardTitle>
            <CardDescription>NIST AI RMF risk controls.</CardDescription>
          </div>
          {register ? <Badge variant="success">{register.version}</Badge> : null}
        </div>
      </CardHeader>
      <CardContent className="grid gap-4 pt-4 sm:pt-5">
        {isLoading ? (
          <div className="text-sm text-muted-foreground">Loading AI governance register.</div>
        ) : null}
        {error ? (
          <Notice title="AI risk register unavailable" tone="danger">
            {error}
          </Notice>
        ) : null}
        {register ? (
          <>
            <div className="grid gap-2 text-sm sm:grid-cols-4">
              <ReadinessCounter
                label="Risks"
                tone={register.risks.length ? "warning" : "success"}
                value={register.risks.length}
              />
              <ReadinessCounter
                label="Critical"
                tone={criticalCount ? "danger" : "success"}
                value={criticalCount}
              />
              <ReadinessCounter
                label="High"
                tone={highCount ? "warning" : "success"}
                value={highCount}
              />
              <ReadinessCounter
                label="Controls"
                tone={implementedControlCount ? "success" : "warning"}
                value={implementedControlCount}
              />
            </div>

            <div className="grid gap-4 lg:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
              <div className="grid gap-3">
                <div className="rounded-lg border border-border/60 bg-muted/20 p-3">
                  <div className="text-sm font-bold text-foreground">Intended system use</div>
                  <p className="mt-1 text-sm leading-6 text-muted-foreground">
                    {register.intended_system_use}
                  </p>
                </div>
                <div className="rounded-lg border border-border/60 bg-card p-3">
                  <div className="text-sm font-bold text-foreground">Prohibited uses</div>
                  <ul className="mt-2 grid gap-2 text-sm leading-6 text-muted-foreground">
                    {register.prohibited_uses.map((use) => (
                      <li className="border-l-2 border-amber-300 pl-3" key={use}>
                        {use}
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="flex min-w-0 flex-wrap gap-2">
                  {nistFunctions.map((functionName) => (
                    <Badge key={functionName} variant="muted">
                      {functionName}
                    </Badge>
                  ))}
                  {register.standard_refs.map((reference) => (
                    <Badge className="max-w-full" key={reference} variant="default">
                      {reference}
                    </Badge>
                  ))}
                </div>
              </div>

              <div className="grid max-h-[540px] gap-3 overflow-y-auto pr-1">
                {register.risks.map((risk) => (
                  <details
                    className="group rounded-lg border border-border/60 bg-card p-3 text-sm"
                    key={risk.risk_id}
                    open={risk.severity === "critical"}
                  >
                    <summary className="flex cursor-pointer list-none flex-wrap items-start justify-between gap-3">
                      <span className="min-w-0">
                        <span className="block break-words font-black">
                          {risk.risk_id}: {risk.title}
                        </span>
                        <span className="mt-1 block text-xs text-muted-foreground">
                          Owner: {risk.owner_role}
                        </span>
                      </span>
                      <span className="flex flex-wrap gap-2">
                        <Badge variant={riskLevelVariant(risk.severity)}>
                          severity {risk.severity}
                        </Badge>
                        <Badge variant={riskLevelVariant(risk.residual_risk)}>
                          residual {risk.residual_risk}
                        </Badge>
                      </span>
                    </summary>
                    <div className="mt-3 grid gap-3 border-t border-border pt-3">
                      <PolicyItem title="Intended use">{risk.intended_use}</PolicyItem>
                      <PolicyItem title="Limitation">{risk.limitation}</PolicyItem>
                      <PolicyItem title="Human oversight">{risk.human_oversight}</PolicyItem>
                      <div className="grid gap-2">
                        <div className="text-xs font-bold uppercase text-muted-foreground">
                          Monitoring signals
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {risk.monitoring_signals.map((signal) => (
                            <Badge key={signal} variant="muted">
                              {signal}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      <div className="grid gap-2">
                        <div className="text-xs font-bold uppercase text-muted-foreground">
                          Controls
                        </div>
                        <div className="grid gap-2">
                          {risk.controls.map((control) => (
                            <div
                              className="rounded-lg border border-border/60 bg-muted/20 p-2"
                              key={control.control_id}
                            >
                              <div className="flex min-w-0 flex-wrap items-center gap-2">
                                <span className="font-bold">{control.title}</span>
                                <Badge
                                  variant={
                                    control.status === "implemented"
                                      ? "success"
                                      : control.status === "partial"
                                        ? "warning"
                                        : "muted"
                                  }
                                >
                                  {control.status}
                                </Badge>
                              </div>
                              <code className="mt-1 block break-all font-mono text-[11px] text-muted-foreground">
                                {control.implementation_ref}
                              </code>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </details>
                ))}
              </div>
            </div>
          </>
        ) : null}
      </CardContent>
    </Card>
  );
}

function OwaspLlmThreatModelPanel({
  error,
  isLoading,
  model,
}: {
  error: string | null;
  isLoading: boolean;
  model: OwaspLlmThreatModel | undefined;
}) {
  const highOrCriticalCount =
    model?.categories.filter(
      (category) =>
        category.residual_risk === "high" || category.residual_risk === "critical",
    ).length ?? 0;
  const mitigationCounts = model?.categories.reduce(
    (counts, category) => {
      for (const mitigation of category.mitigations) {
        counts[mitigation.status] += 1;
      }
      return counts;
    },
    { implemented: 0, partial: 0, planned: 0 },
  ) ?? { implemented: 0, partial: 0, planned: 0 };

  return (
    <Card className="min-w-0 overflow-hidden xl:col-span-2">
      <CardHeader className="border-b border-border/60 bg-muted/30">
        <div className="flex min-w-0 flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <CardTitle className="flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-primary" />
              OWASP LLM threat model
            </CardTitle>
            <CardDescription>Mitigations and residual risk.</CardDescription>
          </div>
          {model ? <Badge variant="success">{model.standard_ref}</Badge> : null}
        </div>
      </CardHeader>
      <CardContent className="grid gap-4 pt-4 sm:pt-5">
        {isLoading ? (
          <div className="text-sm text-muted-foreground">Loading OWASP LLM threat model.</div>
        ) : null}
        {error ? (
          <Notice title="OWASP threat model unavailable" tone="danger">
            {error}
          </Notice>
        ) : null}
        {model ? (
          <>
            <div className="grid gap-2 text-sm sm:grid-cols-4">
              <ReadinessCounter
                label="Categories"
                tone={model.categories.length === 10 ? "success" : "warning"}
                value={model.categories.length}
              />
              <ReadinessCounter
                label="High residual"
                tone={highOrCriticalCount ? "warning" : "success"}
                value={highOrCriticalCount}
              />
              <ReadinessCounter
                label="Implemented"
                tone={mitigationCounts.implemented ? "success" : "warning"}
                value={mitigationCounts.implemented}
              />
              <ReadinessCounter
                label="Partial"
                tone={mitigationCounts.partial ? "warning" : "success"}
                value={mitigationCounts.partial + mitigationCounts.planned}
              />
            </div>

            <div className="grid gap-2">
              {model.categories.map((category) => (
                <details
                  className="rounded-lg border border-border/60 bg-card p-3 text-sm"
                  key={category.category_id}
                  open={category.residual_risk === "high" || category.category_id === "LLM01"}
                >
                  <summary className="flex cursor-pointer list-none flex-wrap items-start justify-between gap-3">
                    <span className="min-w-0">
                      <span className="block break-words font-black">
                        {category.category_id}: {category.category_name}
                      </span>
                      <span className="mt-1 block text-xs text-muted-foreground">
                        {category.applicable_surfaces.slice(0, 5).join(" / ")}
                      </span>
                    </span>
                    <span className="flex flex-wrap gap-2">
                      <Badge variant={riskLevelVariant(category.residual_risk)}>
                        residual {category.residual_risk}
                      </Badge>
                      <Badge variant="muted">{category.mitigations.length} mitigation(s)</Badge>
                    </span>
                  </summary>
                  <div className="mt-3 grid gap-3 border-t border-border pt-3">
                    <p className="leading-6 text-muted-foreground">{category.risk_statement}</p>
                    <div className="grid gap-2">
                      <div className="text-xs font-bold uppercase text-muted-foreground">
                        Monitoring signals
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {category.monitoring_signals.map((signal) => (
                          <Badge key={signal} variant="muted">
                            {signal}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    <div className="grid gap-2 lg:grid-cols-2">
                      {category.mitigations.map((mitigation) => (
                        <div
                          className="grid gap-2 rounded-lg border border-border/60 bg-muted/20 p-3"
                          key={mitigation.mitigation_id}
                        >
                          <div className="flex min-w-0 flex-wrap items-center gap-2">
                            <span className="font-bold">{mitigation.title}</span>
                            <Badge
                              variant={
                                mitigation.status === "implemented"
                                  ? "success"
                                  : mitigation.status === "partial"
                                    ? "warning"
                                    : "muted"
                              }
                            >
                              {mitigation.status}
                            </Badge>
                          </div>
                          <p className="leading-6 text-muted-foreground">{mitigation.notes}</p>
                          <div className="grid gap-1">
                            <div className="text-[11px] font-bold uppercase text-muted-foreground">
                              Code refs
                            </div>
                            {mitigation.implementation_refs.slice(0, 3).map((ref) => (
                              <code
                                className="break-all rounded bg-card px-1.5 py-1 font-mono text-[10px] text-muted-foreground"
                                key={ref}
                              >
                                {ref}
                              </code>
                            ))}
                          </div>
                          <div className="flex flex-wrap gap-2">
                            {mitigation.test_refs.map((ref) => (
                              <Badge className="max-w-full" key={ref} variant="default">
                                {ref}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                    <p className="text-sm leading-6 text-muted-foreground">
                      Residual risk: {category.residual_risk_note}
                    </p>
                  </div>
                </details>
              ))}
            </div>
          </>
        ) : null}
      </CardContent>
    </Card>
  );
}

function MigrationAdminPanel({
  diagnostics,
  error,
  isLoading,
}: {
  diagnostics: MigrationDiagnostics | undefined;
  error: string | null;
  isLoading: boolean;
}) {
  const statusVariant: React.ComponentProps<typeof Badge>["variant"] =
    diagnostics?.status === "ok" || diagnostics?.status === "not_required"
      ? "success"
      : diagnostics?.status === "warning"
        ? "warning"
        : "destructive";
  return (
    <Card className="min-w-0 overflow-hidden">
      <CardHeader className="border-b border-border/60 bg-muted/30">
        <div className="flex min-w-0 flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5 text-primary" />
              Schema migrations
            </CardTitle>
            <CardDescription>Migration state and drift.</CardDescription>
          </div>
          {diagnostics ? (
            <Badge variant={statusVariant}>{diagnostics.status}</Badge>
          ) : null}
        </div>
      </CardHeader>
      <CardContent className="grid gap-4 pt-4 sm:pt-5">
        {isLoading ? (
          <div className="text-sm text-muted-foreground">Checking migration state.</div>
        ) : null}
        {error ? (
          <Notice title="Migration diagnostics unavailable" tone="danger">
            {error}
          </Notice>
        ) : null}
        {diagnostics ? (
          <>
            <div className="grid gap-2 text-sm sm:grid-cols-4">
              <ReadinessCounter
                label="Applied"
                tone="success"
                value={diagnostics.applied_count}
              />
              <ReadinessCounter
                label="Pending"
                tone={diagnostics.pending_count ? "danger" : "success"}
                value={diagnostics.pending_count}
              />
              <ReadinessCounter
                label="Mismatch"
                tone={diagnostics.checksum_mismatch_count ? "danger" : "success"}
                value={diagnostics.checksum_mismatch_count}
              />
              <ReadinessCounter
                label="Unknown"
                tone={diagnostics.unknown_applied_count ? "danger" : "success"}
                value={diagnostics.unknown_applied_count}
              />
            </div>
            <div className="grid gap-2 rounded-lg border border-border/60 bg-muted/20 p-3 text-sm">
              <div className="flex min-w-0 flex-wrap items-center gap-2">
                <Badge variant={diagnostics.connection_ok === false ? "warning" : "muted"}>
                  {diagnostics.bootstrap_code ?? "unknown"}
                </Badge>
                <span className="font-semibold">{diagnostics.bootstrap_summary}</span>
              </div>
              <div className="flex min-w-0 flex-wrap gap-2 text-xs text-muted-foreground">
                <span>backend: {diagnostics.storage_backend}</span>
                <span>latest available: {diagnostics.latest_available_version ?? "none"}</span>
                <span>latest applied: {diagnostics.latest_applied_version ?? "none"}</span>
                <span>table: {diagnostics.table_exists ? "present" : "missing"}</span>
              </div>
            </div>
            <div className="grid max-h-80 gap-2 overflow-y-auto pr-1">
              {diagnostics.migrations.map((migration) => (
                <div
                  className="grid gap-2 rounded-lg border border-border/60 bg-card p-3"
                  key={`${migration.status}-${migration.version}`}
                >
                  <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
                    <div className="min-w-0">
                      <div className="break-words text-sm font-black">
                        {migration.version} / {migration.name}
                      </div>
                      <div className="mt-0.5 break-all font-mono text-[11px] text-muted-foreground">
                        {migration.checksum ?? "checksum unavailable"}
                      </div>
                    </div>
                    <Badge variant={migrationStatusVariant(migration.status)}>
                      {migration.status}
                    </Badge>
                  </div>
                  <div className="grid gap-1 text-xs text-muted-foreground sm:grid-cols-3">
                    <span>applied: {migration.applied_at ?? "not applied"}</span>
                    <span>
                      duration:{" "}
                      {typeof migration.duration_ms === "number"
                        ? `${migration.duration_ms}ms`
                        : "not recorded"}
                    </span>
                    <span>failure: {migration.failure_reason ?? "none"}</span>
                  </div>
                </div>
              ))}
              {!diagnostics.migrations.length ? (
                <Badge variant="warning">No migration manifest entries</Badge>
              ) : null}
            </div>
          </>
        ) : null}
      </CardContent>
    </Card>
  );
}

function AdminPolicyPanel({
  isLoading,
  runtime,
}: {
  isLoading: boolean;
  runtime: RuntimeConfig | undefined;
}) {
  const assistantPolicy = runtimeAssistantSettingsFromRuntime(runtime);
  const providerPolicies = assistantPolicy
    ? [
        {
          label: "LLM planning",
          enabled: assistantPolicy.external_openai_llm_enabled,
          phiAllowed: assistantPolicy.external_openai_llm_allow_phi,
        },
        {
          label: "Vision OCR",
          enabled: assistantPolicy.external_openai_ocr_enabled,
          phiAllowed: assistantPolicy.external_openai_ocr_allow_phi,
        },
        {
          label: "Embeddings",
          enabled: assistantPolicy.external_openai_embeddings_enabled,
          phiAllowed: assistantPolicy.external_openai_embeddings_allow_phi,
        },
        {
          label: "External medical search",
          enabled: assistantPolicy.external_medical_search_enabled,
          phiAllowed: assistantPolicy.external_medical_search_allow_phi,
        },
      ]
    : [];
  const phiAllowedCount = providerPolicies.filter((policy) => policy.phiAllowed).length;
  const ocrThreshold = runtime?.review_policy?.ocr_low_confidence_threshold;

  return (
    <Card className="min-w-0 overflow-hidden xl:col-span-2">
      <CardHeader className="border-b border-border/60 bg-muted/30">
        <div className="flex min-w-0 flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5 text-primary" />
              Admin policy controls
            </CardTitle>
            <CardDescription>Review gates and PHI handling.</CardDescription>
          </div>
          <Badge variant={phiAllowedCount ? "warning" : "success"}>
            {phiAllowedCount ? `${phiAllowedCount} PHI exceptions` : "PHI blocked externally"}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="grid gap-4 pt-4 sm:pt-5 xl:grid-cols-2">
        <div className="grid gap-0 text-sm text-muted-foreground">
          <PolicyItem title="Review threshold">
            {isLoading
              ? "Loading review policy"
              : `Human review is required by default; OCR evidence below ${
                  typeof ocrThreshold === "number"
                    ? `${Math.round(ocrThreshold * 100)}% confidence`
                    : "the configured threshold"
                } is routed for review.`}
          </PolicyItem>
          <PolicyItem title="Reviewer accountability">
            Review decisions use the authenticated session user, not client-supplied identity.
          </PolicyItem>
          <PolicyItem title="Audit chain">
            {runtime?.audit?.hash_chain_written
              ? `Hash-chain fields are written${
                  runtime.audit.hash_chain_required ? " and required" : ""
                } for this deployment.`
              : "Audit hash-chain status is unavailable from runtime config."}
          </PolicyItem>
          <PolicyItem title="Retention">
            {runtime?.retention?.artifact_policy_configured
              ? `${runtime.retention.artifact_rule_count} artifact retention rule(s) configured.`
              : "No artifact retention override is configured; backend defaults apply."}
          </PolicyItem>
          <PolicyItem title="Tool gates">
            {runtime?.tools
              ? `${runtime.tools.approval_required_count} of ${
                  runtime.tools.registered_count
                } registered tool(s) require explicit approval.`
              : "Tool registry facts are unavailable from runtime config."}
          </PolicyItem>
        </div>

        <div className="grid gap-3">
          <div>
            <div className="text-sm font-bold text-foreground">External provider PHI policy</div>
            <p className="mt-1 text-sm leading-6 text-muted-foreground">
              These switches are persisted in Assistant runtime settings and enforced
              before outbound provider calls.
            </p>
          </div>
          <div className="grid gap-2">
            {providerPolicies.map((policy) => (
              <div
                className="flex min-w-0 flex-wrap items-center justify-between gap-2 rounded-lg border border-border/60 bg-card px-3 py-2"
                key={policy.label}
              >
                <span className="font-semibold">{policy.label}</span>
                <span className="flex flex-wrap gap-2">
                  <Badge variant={policy.enabled ? "success" : "muted"}>
                    {policy.enabled ? "enabled" : "disabled"}
                  </Badge>
                  <Badge variant={policy.phiAllowed ? "warning" : "success"}>
                    {policy.phiAllowed ? "PHI allowed" : "PHI blocked"}
                  </Badge>
                </span>
              </div>
            ))}
            {!providerPolicies.length ? (
              <Notice title="Policy loading">
                Runtime Assistant policy has not been returned by the backend yet.
              </Notice>
            ) : null}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

type RetrievalSettingsFormState = {
  embeddingProvider: "openai" | "huggingface";
  embeddingModel: string;
  embeddingDimensions: string;
  framework: "custom" | "llamaindex";
  candidateMultiplier: string;
  minCandidates: string;
  vectorWeight: string;
  bm25Weight: string;
  diversityEnabled: boolean;
  diversityLambda: string;
  hnswEfSearch: string;
};

type AssistantSettingsFormState = {
  provider: "disabled" | "openai";
  model: string;
  planningModel: string;
  synthesisModel: string;
  visionModel: string;
  baseUrl: string;
  timeoutSeconds: string;
  maxToolCalls: string;
  planningProgressIntervalSeconds: string;
  externalOpenAiLlmEnabled: boolean;
  externalOpenAiLlmAllowPhi: boolean;
  externalOpenAiOcrEnabled: boolean;
  externalOpenAiOcrAllowPhi: boolean;
  externalOpenAiOcrAllowUnknown: boolean;
  externalOpenAiEmbeddingsEnabled: boolean;
  externalOpenAiEmbeddingsAllowPhi: boolean;
  externalMedicalSearchEnabled: boolean;
  externalMedicalSearchAllowPhi: boolean;
};

function AssistantSettingsForm({
  isLoading,
  runtime,
}: {
  isLoading: boolean;
  runtime: RuntimeConfig | undefined;
}) {
  const mutation = useRuntimeAssistantSettingsMutation();
  const [form, setForm] = React.useState<AssistantSettingsFormState | null>(null);
  const [localError, setLocalError] = React.useState<string | null>(null);

  React.useEffect(() => {
    const settings = runtimeAssistantSettingsFromRuntime(runtime);
    if (!settings) return;
    setForm({
      provider: settings.llm_provider,
      model: settings.llm_model,
      planningModel: settings.llm_planning_model,
      synthesisModel: settings.llm_synthesis_model,
      visionModel: settings.llm_vision_model,
      baseUrl: settings.llm_base_url,
      timeoutSeconds: String(settings.llm_timeout_seconds),
      maxToolCalls: String(settings.llm_max_tool_calls),
      planningProgressIntervalSeconds: String(
        settings.llm_planning_progress_interval_seconds,
      ),
      externalOpenAiLlmEnabled: settings.external_openai_llm_enabled,
      externalOpenAiLlmAllowPhi: settings.external_openai_llm_allow_phi,
      externalOpenAiOcrEnabled: settings.external_openai_ocr_enabled,
      externalOpenAiOcrAllowPhi: settings.external_openai_ocr_allow_phi,
      externalOpenAiOcrAllowUnknown: settings.external_openai_ocr_allow_unknown,
      externalOpenAiEmbeddingsEnabled: settings.external_openai_embeddings_enabled,
      externalOpenAiEmbeddingsAllowPhi: settings.external_openai_embeddings_allow_phi,
      externalMedicalSearchEnabled: settings.external_medical_search_enabled,
      externalMedicalSearchAllowPhi: settings.external_medical_search_allow_phi,
    });
  }, [runtime]);

  const updateField = <Key extends keyof AssistantSettingsFormState>(
    key: Key,
    value: AssistantSettingsFormState[Key],
  ) => {
    setForm((current) => (current ? { ...current, [key]: value } : current));
    if (localError) setLocalError(null);
  };

  const save = (event: React.FormEvent) => {
    event.preventDefault();
    if (!form) return;
    try {
      mutation.mutate(runtimeAssistantPayloadFromForm(form));
    } catch (error) {
      setLocalError(error instanceof Error ? error.message : String(error));
    }
  };

  const openAiMissing =
    form?.provider === "openai" && runtime && runtime.llm?.openai_configured === false;

  return (
    <Card className="min-w-0 overflow-hidden">
      <CardHeader className="border-b border-border/60 bg-muted/30">
        <div className="flex min-w-0 flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <CardTitle className="flex items-center gap-2">
              <Bot className="h-5 w-5 text-primary" />
              Assistant runtime
            </CardTitle>
            <CardDescription>LLM planner and tool limits.</CardDescription>
          </div>
          {runtime?.llm?.runtime_settings_configured ? (
            <Badge variant="success">reloadable</Badge>
          ) : (
            <Badge variant="muted">config-backed</Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="pt-4 sm:pt-5">
        {!form ? (
          <Notice title={isLoading ? "Runtime loading" : "Runtime settings unavailable"}>
            Backend runtime config has not returned editable Assistant settings.
          </Notice>
        ) : (
          <form className="grid gap-4" onSubmit={save}>
            {openAiMissing ? (
              <Notice title="OpenAI key missing">
                OpenAI planner mode requires OJT_OPENAI_API_KEY or OPENAI_API_KEY in the backend environment.
              </Notice>
            ) : null}
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
                Assistant planner is {mutation.data.settings.llm_provider}.
              </Notice>
            ) : null}

            <div className="grid min-w-0 gap-3 sm:grid-cols-2 xl:grid-cols-3">
              <Label>
                Planner
                <Select
                  onChange={(event) =>
                    updateField(
                      "provider",
                      event.target.value === "openai" ? "openai" : "disabled",
                    )
                  }
                  value={form.provider}
                >
                  <option value="disabled">Unavailable</option>
                  <option value="openai">OpenAI</option>
                </Select>
              </Label>
              <Label>
                Default model
                <Input
                  onChange={(event) => updateField("model", event.target.value)}
                  placeholder="chat-latest"
                  type="text"
                  value={form.model}
                />
              </Label>
              <Label>
                Planning model
                <Input
                  onChange={(event) => updateField("planningModel", event.target.value)}
                  placeholder="chat-latest"
                  type="text"
                  value={form.planningModel}
                />
              </Label>
              <Label>
                Synthesis model
                <Input
                  onChange={(event) => updateField("synthesisModel", event.target.value)}
                  placeholder="chat-latest"
                  type="text"
                  value={form.synthesisModel}
                />
              </Label>
              <Label>
                Vision model
                <Input
                  onChange={(event) => updateField("visionModel", event.target.value)}
                  placeholder="gpt-4.1-mini"
                  type="text"
                  value={form.visionModel}
                />
              </Label>
              <Label>
                OpenAI-compatible endpoint
                <Input
                  onChange={(event) => updateField("baseUrl", event.target.value)}
                  placeholder="https://api.openai.com/v1"
                  type="url"
                  value={form.baseUrl}
                />
              </Label>
              <Label>
                Timeout seconds
                <Input
                  min={1}
                  max={300}
                  onChange={(event) => updateField("timeoutSeconds", event.target.value)}
                  step={0.5}
                  type="number"
                  value={form.timeoutSeconds}
                />
              </Label>
              <Label>
                Max tool calls
                <Input
                  min={1}
                  max={12}
                  onChange={(event) => updateField("maxToolCalls", event.target.value)}
                  type="number"
                  value={form.maxToolCalls}
                />
              </Label>
              <Label>
                Planning heartbeat seconds
                <Input
                  min={0.25}
                  max={30}
                  onChange={(event) =>
                    updateField("planningProgressIntervalSeconds", event.target.value)
                  }
                  step={0.25}
                  type="number"
                  value={form.planningProgressIntervalSeconds}
                />
              </Label>
            </div>

            <div className="grid gap-3 rounded-lg border border-border/60 bg-muted/30 p-3">
              <div className="min-w-0">
                <div className="text-sm font-bold text-foreground">
                  External provider policy
                </div>
                <p className="mt-1 text-sm leading-6 text-muted-foreground">
                  Decide which external services are allowed, and whether each service
                  may receive sensitive clinical data.
                </p>
              </div>
              <div className="grid gap-2">
                <ProviderPolicyRow
                  description="Planner and answer generation."
                  enabled={form.externalOpenAiLlmEnabled}
                  label="OpenAI LLM"
                  onEnabledChange={(checked) => updateField("externalOpenAiLlmEnabled", checked)}
                  onPhiChange={(checked) => updateField("externalOpenAiLlmAllowPhi", checked)}
                  phiAllowed={form.externalOpenAiLlmAllowPhi}
                />
                <ProviderPolicyRow
                  description="Image and scanned-PDF OCR."
                  enabled={form.externalOpenAiOcrEnabled}
                  label="OpenAI vision OCR"
                  onEnabledChange={(checked) => updateField("externalOpenAiOcrEnabled", checked)}
                  onPhiChange={(checked) => updateField("externalOpenAiOcrAllowPhi", checked)}
                  phiAllowed={form.externalOpenAiOcrAllowPhi}
                />
                <PolicyToggle
                  checked={form.externalOpenAiOcrAllowUnknown}
                  label="Allow OCR before PHI classification is known"
                  onChange={(checked) => updateField("externalOpenAiOcrAllowUnknown", checked)}
                />
                <ProviderPolicyRow
                  description="Semantic vector indexing and query embeddings."
                  enabled={form.externalOpenAiEmbeddingsEnabled}
                  label="OpenAI embeddings"
                  onEnabledChange={(checked) =>
                    updateField("externalOpenAiEmbeddingsEnabled", checked)
                  }
                  onPhiChange={(checked) =>
                    updateField("externalOpenAiEmbeddingsAllowPhi", checked)
                  }
                  phiAllowed={form.externalOpenAiEmbeddingsAllowPhi}
                />
                <ProviderPolicyRow
                  description="External medical web/API search surfaces."
                  enabled={form.externalMedicalSearchEnabled}
                  label="Medical search"
                  onEnabledChange={(checked) => updateField("externalMedicalSearchEnabled", checked)}
                  onPhiChange={(checked) => updateField("externalMedicalSearchAllowPhi", checked)}
                  phiAllowed={form.externalMedicalSearchAllowPhi}
                />
              </div>
            </div>

            <div className="flex min-w-0 flex-wrap gap-2">
              <Badge variant={runtime?.llm?.openai_configured ? "success" : "warning"}>
                {runtime?.llm?.openai_configured ? "OpenAI key configured" : "OpenAI key missing"}
              </Badge>
              <Badge variant="muted">
                {runtime?.llm?.base_url_configured ? "base URL configured" : "base URL missing"}
              </Badge>
              <Badge variant="success">write tools gated</Badge>
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
      embeddingProvider: settings.embedding_provider,
      embeddingModel: settings.embedding_model,
      embeddingDimensions: String(settings.embedding_dimensions),
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
      <CardHeader className="border-b border-border/60 bg-muted/30">
        <div className="flex min-w-0 flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <CardTitle className="flex items-center gap-2">
              <SlidersHorizontal className="h-5 w-5 text-primary" />
              Retrieval runtime
            </CardTitle>
            <CardDescription>Search and ranking controls.</CardDescription>
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

            <div className="grid min-w-0 gap-3 sm:grid-cols-2 xl:grid-cols-3">
              <Label>
                Embedding provider
                <Select
                  onChange={(event) => {
                    const provider = retrievalEmbeddingProvider(event.target.value);
                    updateField("embeddingProvider", provider);
                  }}
                  value={form.embeddingProvider}
                >
                  <option value="openai">OpenAI</option>
                  <option value="huggingface">Hugging Face</option>
                </Select>
              </Label>
              <Label>
                Embedding model
                <Input
                  onChange={(event) => updateField("embeddingModel", event.target.value)}
                  placeholder="text-embedding-3-small"
                  type="text"
                  value={form.embeddingModel}
                />
              </Label>
              <Label>
                Embedding dimensions
                <Input
                  min={1}
                  max={4096}
                  onChange={(event) => updateField("embeddingDimensions", event.target.value)}
                  type="number"
                  value={form.embeddingDimensions}
                />
              </Label>
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
                  disabled={!form.diversityEnabled}
                  min={0}
                  max={1}
                  onChange={(event) => updateField("diversityLambda", event.target.value)}
                  step={0.01}
                  type="number"
                  value={form.diversityLambda}
                />
                <span className="mt-1 block text-xs font-semibold leading-5 text-muted-foreground">
                  0 favors source novelty; 1 favors raw relevance. Default 0.72 keeps relevance primary while reducing repeated-source evidence.
                </span>
              </Label>
              <label className="flex min-h-9 items-center gap-2 rounded-lg border border-border/60 bg-muted/20 px-3 text-sm font-semibold">
                <input
                  checked={form.diversityEnabled}
                  className="h-4 w-4 accent-primary"
                  onChange={(event) => updateField("diversityEnabled", event.target.checked)}
                  type="checkbox"
                />
                Source diversity
              </label>
              <div className="rounded-lg border border-border/60 bg-muted/20 px-3 py-2 text-xs font-semibold leading-5 text-muted-foreground sm:col-span-2 xl:col-span-3">
                Embedding changes require retrieval reindexing before vector search is fully aligned. Source diversity changes final evidence selection after hybrid retrieval and reranking. Disable it only when strict score order is required.
              </div>
            </div>

            <RetrievalRulePackInventory packs={runtime?.retrieval?.rule_packs ?? []} />

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

function RetrievalRulePackInventory({ packs }: { packs: RuntimeRetrievalRulePack[] }) {
  if (!packs.length) {
    return (
      <Notice title="Retrieval rule packs unavailable">
        Runtime config has not returned retrieval rule-pack inventory.
      </Notice>
    );
  }
  const issueCount = packs.filter((pack) => pack.status !== "ok").length;
  return (
    <div className="grid gap-2 rounded-lg border border-border/60 bg-muted/20 p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="text-xs font-bold uppercase text-muted-foreground">
          Retrieval rule packs
        </div>
        <Badge variant={issueCount ? "warning" : "success"}>
          {issueCount ? `${issueCount} issue` : "loaded"}
        </Badge>
      </div>
      <div className="grid gap-2 sm:grid-cols-2">
        {packs.map((pack) => (
          <div
            className="grid min-w-0 gap-1 rounded-lg border border-border/60 bg-card p-2 text-xs"
            key={`${pack.name}-${pack.env_var}`}
          >
            <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
              <span className="break-words font-bold">{humanizeSettingLabel(pack.name)}</span>
              <Badge variant={runtimeRulePackVariant(pack.status)}>
                {pack.status}
              </Badge>
            </div>
            <div className="flex min-w-0 flex-wrap gap-1.5">
              <Badge variant="muted">{pack.rule_count} rules</Badge>
              {pack.version ? (
                <Badge className="max-w-full whitespace-normal break-all leading-4" variant="muted">
                  {pack.version}
                </Badge>
              ) : null}
              {pack.content_hash ? (
                <Badge variant="muted">{shortRulePackHash(pack.content_hash)}</Badge>
              ) : null}
              <Badge variant={pack.configured ? "success" : "muted"}>
                {pack.source}
              </Badge>
            </div>
            <code className="max-w-full break-words rounded bg-muted px-1.5 py-1 font-mono text-[11px] text-muted-foreground">
              {pack.env_var}
            </code>
            {pack.error ? (
              <div className="break-words font-semibold text-red-700">{pack.error}</div>
            ) : null}
          </div>
        ))}
      </div>
    </div>
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
    typeof runtime?.embedding?.provider !== "string" ||
    typeof runtime.embedding.model !== "string" ||
    !isFiniteNumber(runtime.embedding.dimensions) ||
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
    embedding_provider: retrievalEmbeddingProvider(runtime.embedding.provider),
    embedding_model: runtime.embedding.model,
    embedding_dimensions: runtime.embedding.dimensions,
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

function retrievalEmbeddingProvider(
  value: string,
): "openai" | "huggingface" {
  if (value === "openai" || value === "huggingface") return value;
  return "openai";
}

function runtimeAssistantSettingsFromRuntime(
  runtime: RuntimeConfig | undefined,
): RuntimeAssistantSettings | null {
  const llm = runtime?.llm;
  const settings = llm?.runtime_settings;
  if (settings) return runtimeAssistantSettingsWithPolicyDefaults(settings);
  if (!llm) return null;
  const provider = llm.provider === "openai" ? "openai" : "disabled";
  if (
    typeof llm.model !== "string" ||
    !llm.model.trim() ||
    !isFiniteNumber(llm.timeout_seconds) ||
    !isFiniteNumber(llm.max_tool_calls)
  ) {
    return null;
  }
  return runtimeAssistantSettingsWithPolicyDefaults({
    llm_provider: provider,
    llm_model: llm.model,
    llm_planning_model:
      typeof llm.planning_model === "string" && llm.planning_model.trim()
        ? llm.planning_model
        : llm.model,
    llm_synthesis_model:
      typeof llm.synthesis_model === "string" && llm.synthesis_model.trim()
        ? llm.synthesis_model
        : llm.model,
    llm_vision_model:
      typeof llm.vision_model === "string" && llm.vision_model.trim()
        ? llm.vision_model
        : llm.model === "chat-latest"
          ? "gpt-4.1-mini"
          : llm.model,
    llm_base_url:
      typeof llm.base_url === "string" && llm.base_url.trim()
        ? llm.base_url
        : "https://api.openai.com/v1",
    llm_timeout_seconds: llm.timeout_seconds,
    llm_max_tool_calls: llm.max_tool_calls,
    llm_planning_progress_interval_seconds: isFiniteNumber(
      llm.planning_progress_interval_seconds,
    )
      ? llm.planning_progress_interval_seconds
      : 2,
  } as RuntimeAssistantSettings);
}

function runtimeAssistantSettingsWithPolicyDefaults(
  settings: RuntimeAssistantSettings,
): RuntimeAssistantSettings {
  const defaults = {
    external_openai_llm_enabled: true,
    external_openai_llm_allow_phi: false,
    external_openai_ocr_enabled: true,
    external_openai_ocr_allow_phi: false,
    external_openai_ocr_allow_unknown: true,
    external_openai_embeddings_enabled: true,
    external_openai_embeddings_allow_phi: false,
    external_medical_search_enabled: true,
    external_medical_search_allow_phi: false,
  };
  return { ...defaults, ...settings };
}

function runtimeAssistantPayloadFromForm(
  form: AssistantSettingsFormState,
): RuntimeAssistantSettingsPayload {
  const llm_model = form.model.trim();
  const llm_planning_model = form.planningModel.trim();
  const llm_synthesis_model = form.synthesisModel.trim();
  const llm_vision_model = form.visionModel.trim();
  const llm_base_url = form.baseUrl.trim();
  if (!llm_model) {
    throw new Error("Default model must not be blank.");
  }
  if (!llm_planning_model || !llm_synthesis_model || !llm_vision_model) {
    throw new Error("Planning, synthesis, and vision models must not be blank.");
  }
  if (!llm_base_url) {
    throw new Error("OpenAI-compatible endpoint must not be blank.");
  }
  return {
    llm_provider: form.provider,
    llm_model,
    llm_planning_model,
    llm_synthesis_model,
    llm_vision_model,
    llm_base_url,
    llm_timeout_seconds: numberField(form.timeoutSeconds, "Timeout seconds", 1, 300),
    llm_max_tool_calls: integerField(form.maxToolCalls, "Max tool calls", 1, 12),
    llm_planning_progress_interval_seconds: numberField(
      form.planningProgressIntervalSeconds,
      "Planning heartbeat seconds",
      0.25,
      30,
    ),
    external_openai_llm_enabled: form.externalOpenAiLlmEnabled,
    external_openai_llm_allow_phi: form.externalOpenAiLlmAllowPhi,
    external_openai_ocr_enabled: form.externalOpenAiOcrEnabled,
    external_openai_ocr_allow_phi: form.externalOpenAiOcrAllowPhi,
    external_openai_ocr_allow_unknown: form.externalOpenAiOcrAllowUnknown,
    external_openai_embeddings_enabled: form.externalOpenAiEmbeddingsEnabled,
    external_openai_embeddings_allow_phi: form.externalOpenAiEmbeddingsAllowPhi,
    external_medical_search_enabled: form.externalMedicalSearchEnabled,
    external_medical_search_allow_phi: form.externalMedicalSearchAllowPhi,
  };
}

function runtimeRetrievalPayloadFromForm(
  form: RetrievalSettingsFormState,
): RuntimeRetrievalSettingsPayload {
  const embedding_model = form.embeddingModel.trim();
  if (!embedding_model) {
    throw new Error("Embedding model must not be blank.");
  }
  const retrieval_vector_weight = numberField(form.vectorWeight, "Vector weight", 0, 1);
  const retrieval_bm25_weight = numberField(form.bm25Weight, "BM25 weight", 0, 1);
  if (retrieval_vector_weight + retrieval_bm25_weight <= 0) {
    throw new Error("Vector and BM25 weights cannot both be zero.");
  }
  return {
    embedding_provider: form.embeddingProvider,
    embedding_model,
    embedding_dimensions: integerField(
      form.embeddingDimensions,
      "Embedding dimensions",
      1,
      4096,
    ),
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

function runtimeRulePackVariant(
  status: RuntimeRetrievalRulePack["status"],
): React.ComponentProps<typeof Badge>["variant"] {
  if (status === "ok") return "success";
  if (status === "error") return "destructive";
  return "warning";
}

function retrievalRulePacksFromDetails(
  details: Record<string, unknown>,
): RuntimeRetrievalRulePack[] {
  const rawPacks = details.packs;
  if (!Array.isArray(rawPacks)) return [];
  return rawPacks.reduce<RuntimeRetrievalRulePack[]>((packs, rawPack) => {
    if (!rawPack || typeof rawPack !== "object" || Array.isArray(rawPack)) {
      return packs;
    }
    const pack = rawPack as Record<string, unknown>;
    const name = typeof pack.name === "string" ? pack.name : "";
    const envVar = typeof pack.env_var === "string" ? pack.env_var : "";
    if (!name || !envVar) return packs;
    packs.push({
      name,
      status: runtimeRulePackStatus(pack.status),
      source: typeof pack.source === "string" ? pack.source : "unknown",
      env_var: envVar,
      configured: pack.configured === true,
      rule_count:
        typeof pack.rule_count === "number" && Number.isFinite(pack.rule_count)
          ? pack.rule_count
          : 0,
      version: typeof pack.version === "string" ? pack.version : null,
      content_hash: typeof pack.content_hash === "string" ? pack.content_hash : null,
      error: typeof pack.error === "string" ? pack.error : undefined,
    });
    return packs;
  }, []);
}

function runtimeRulePackStatus(value: unknown): RuntimeRetrievalRulePack["status"] {
  if (value === "ok" || value === "missing" || value === "error") return value;
  return "error";
}

function shortRulePackHash(hash: string) {
  return hash.length > 12 ? hash.slice(0, 12) : hash;
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

function migrationStatusVariant(
  status: MigrationDiagnostics["migrations"][number]["status"],
): React.ComponentProps<typeof Badge>["variant"] {
  if (status === "applied") return "success";
  if (status === "pending") return "warning";
  return "destructive";
}

function riskLevelVariant(
  level: AiRiskLevel | ThreatRiskLevel,
): React.ComponentProps<typeof Badge>["variant"] {
  if (level === "critical") return "destructive";
  if (level === "high" || level === "medium") return "warning";
  return "success";
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
          <ReadinessRulePackDetails check={check} />
          <ReadinessDetailChips details={check.details} />
        </div>
      ))}
    </div>
  );
}

function ReadinessRulePackDetails({ check }: { check: ReadinessCheck }) {
  if (check.name !== "retrieval_rule_packs") return null;
  const packs = retrievalRulePacksFromDetails(check.details);
  if (!packs.length) return null;
  const issueCount = packs.filter((pack) => pack.status !== "ok").length;
  return (
    <div className="grid gap-1.5 rounded-lg border border-border/60 bg-muted/20 p-2">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="text-[11px] font-bold uppercase text-muted-foreground">
          Rule pack readiness
        </span>
        <Badge variant={issueCount ? "warning" : "success"}>
          {issueCount ? `${issueCount} issue` : "all loadable"}
        </Badge>
      </div>
      <div className="grid gap-1.5 sm:grid-cols-2">
        {packs.map((pack) => (
          <div
            className="grid min-w-0 gap-1 rounded-lg border border-border/60 bg-card px-2 py-1.5 text-[11px]"
            key={`${pack.name}-${pack.env_var}`}
          >
            <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
              <span className="break-words font-bold">{humanizeSettingLabel(pack.name)}</span>
              <Badge variant={runtimeRulePackVariant(pack.status)}>{pack.status}</Badge>
            </div>
            <div className="flex min-w-0 flex-wrap gap-1">
              <Badge variant="muted">{pack.rule_count} rules</Badge>
              {pack.version ? (
                <Badge className="max-w-full whitespace-normal break-all leading-4" variant="muted">
                  {pack.version}
                </Badge>
              ) : null}
              {pack.content_hash ? (
                <Badge variant="muted">{shortRulePackHash(pack.content_hash)}</Badge>
              ) : null}
              <Badge variant={pack.configured ? "success" : "muted"}>
                {pack.source}
              </Badge>
            </div>
            <code className="break-words rounded bg-muted px-1.5 py-1 font-mono text-[10px] text-muted-foreground">
              {pack.env_var}
            </code>
          </div>
        ))}
      </div>
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

function humanizeSettingLabel(value: string) {
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
  badgeLabel,
  children,
  status,
  title,
}: {
  badgeLabel?: string;
  children: React.ReactNode;
  status: "active" | "attention" | "planned";
  title: string;
}) {
  const Icon = status === "active" ? CheckCircle2 : Clock3;
  const label =
    badgeLabel ?? (status === "active" ? "active" : status === "attention" ? "attention" : "not required");
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
            {label}
          </Badge>
        </div>
        <p className="mt-1 text-sm leading-6 text-muted-foreground">{children}</p>
      </div>
    </div>
  );
}

function PolicyToggle({
  checked,
  label,
  onChange,
  tone = "default",
}: {
  checked: boolean;
  label: string;
  onChange: (checked: boolean) => void;
  tone?: "default" | "danger";
}) {
  return (
    <label
      className={
        tone === "danger"
          ? "flex min-w-0 items-center gap-2 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm font-semibold text-amber-950"
          : "flex min-w-0 items-center gap-2 rounded-lg border border-border/60 bg-card px-3 py-2 text-sm font-semibold text-foreground"
      }
    >
      <input
        checked={checked}
        className="h-4 w-4 rounded border-input accent-primary"
        onChange={(event) => onChange(event.target.checked)}
        type="checkbox"
      />
      <span className="min-w-0 leading-5">{label}</span>
    </label>
  );
}

function ProviderPolicyRow({
  description,
  enabled,
  label,
  onEnabledChange,
  onPhiChange,
  phiAllowed,
}: {
  description: string;
  enabled: boolean;
  label: string;
  onEnabledChange: (checked: boolean) => void;
  onPhiChange: (checked: boolean) => void;
  phiAllowed: boolean;
}) {
  return (
    <div className="grid gap-3 rounded-lg border border-border/60 bg-card p-3">
      <div className="min-w-0">
        <div className="font-bold text-foreground">{label}</div>
        <p className="mt-1 text-sm leading-5 text-muted-foreground">{description}</p>
      </div>
      <div className="grid gap-2 sm:grid-cols-2">
        <PolicyToggle
          checked={enabled}
          label={enabled ? "Service enabled" : "Service disabled"}
          onChange={onEnabledChange}
        />
        <PolicyToggle
          checked={phiAllowed}
          label={phiAllowed ? "PHI allowed" : "PHI blocked"}
          onChange={onPhiChange}
          tone={phiAllowed ? "danger" : "default"}
        />
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
