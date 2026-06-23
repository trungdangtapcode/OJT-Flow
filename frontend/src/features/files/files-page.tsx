import * as React from "react";
import { Download, FileText, HardDrive, Loader2, Search, ShieldCheck } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import {
  getWorkspaceArtifact,
  listWorkspaceArtifacts,
  workspaceArtifactDownloadUrl,
} from "../../api";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardTitle } from "../../components/ui/card";
import { Input, Select } from "../../components/ui/form";
import { Notice } from "../../components/ui/notice";
import { Table, TBody, TD, TH, THead, TR } from "../../components/ui/table";
import { workflowErrorMessage } from "../../lib/server-state";
import { cn, formatCompactDate, humanize } from "../../lib/utils";
import { formatBytes } from "../workbench/workbench-utils";
import type { ArtifactScope, UploadedArtifact } from "../../types";

const ARTIFACT_LIMIT = 200;

export function FilesPage() {
  const [scope, setScope] = React.useState<ArtifactScope>("workspace");
  const [q, setQ] = React.useState("");
  const [source, setSource] = React.useState("");
  const [selectedId, setSelectedId] = React.useState<string | null>(null);
  const artifactsQuery = useQuery({
    queryKey: ["workspace-artifacts", scope, q, source],
    queryFn: () =>
      listWorkspaceArtifacts({
        scope,
        limit: ARTIFACT_LIMIT,
        q,
        source,
      }),
  });
  const artifacts = artifactsQuery.data?.items ?? [];
  const selected = artifacts.find((artifact) => artifact.artifact_id === selectedId) ?? null;
  const detailQuery = useQuery({
    queryKey: ["workspace-artifact-detail", selected?.artifact_id],
    queryFn: () => getWorkspaceArtifact(selected!.artifact_id),
    enabled: Boolean(selected),
  });

  React.useEffect(() => {
    if (!artifacts.length) {
      setSelectedId(null);
      return;
    }
    if (!selectedId || !artifacts.some((artifact) => artifact.artifact_id === selectedId)) {
      setSelectedId(artifacts[0].artifact_id);
    }
  }, [artifacts, selectedId]);

  const totalBytes = artifacts.reduce((sum, artifact) => sum + artifact.byte_size, 0);
  const minioActive = artifactsQuery.data?.object_storage_backend === "minio";

  return (
    <div className="grid min-w-0 gap-5">
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-lg font-bold tracking-tight text-foreground">Files</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Uploaded PDFs, images, spreadsheets, clipboard files, and extraction artifacts.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge variant={minioActive ? "success" : "warning"}>
            {minioActive ? "MinIO object storage" : "local legacy storage"}
          </Badge>
          <Badge variant="muted">{artifacts.length} files</Badge>
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        <StatCard icon={FileText} label="Visible files" value={String(artifacts.length)} />
        <StatCard icon={HardDrive} label="Visible bytes" value={formatBytes(totalBytes)} />
        <StatCard icon={ShieldCheck} label="Metadata scope" value={humanize(scope)} />
      </div>

      <Card className="min-w-0 overflow-hidden">
        <div className="border-b border-border/60 bg-muted/30 p-4">
          <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_160px_180px]">
            <div className="relative">
              <Search className="pointer-events-none absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                aria-label="Search files"
                className="pl-8"
                onChange={(event) => setQ(event.target.value)}
                placeholder="Search filename"
                value={q}
              />
            </div>
            <Select
              aria-label="File scope"
              onChange={(event) => setScope(event.target.value as ArtifactScope)}
              value={scope}
            >
              <option value="workspace">Workspace files</option>
              <option value="mine">My files</option>
            </Select>
            <Select
              aria-label="Upload source"
              onChange={(event) => setSource(event.target.value)}
              value={source}
            >
              <option value="">All sources</option>
              <option value="upload">Upload</option>
              <option value="clipboard">Clipboard</option>
              <option value="assistant_attachment">Assistant</option>
              <option value="api">API</option>
            </Select>
          </div>
        </div>
        <CardContent className="grid gap-4 p-0">
          {artifactsQuery.isLoading ? (
            <div className="flex items-center gap-2 p-5 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" /> Loading workspace files
            </div>
          ) : null}
          {artifactsQuery.isError ? (
            <div className="p-5">
              <Notice title="Files could not be loaded" tone="danger">
                {workflowErrorMessage(artifactsQuery.error)}
              </Notice>
            </div>
          ) : null}
          {!artifactsQuery.isLoading && !artifactsQuery.isError && !artifacts.length ? (
            <div className="p-5">
              <Notice title="No files found">
                Upload a file in Workbench or attach an image/PDF in Assistant to create artifacts.
              </Notice>
            </div>
          ) : null}
          {artifacts.length ? (
            <div className="grid min-w-0 xl:grid-cols-[minmax(0,1fr)_400px]">
              <ArtifactTable
                artifacts={artifacts}
                selectedId={selectedId}
                onSelect={setSelectedId}
              />
              <ArtifactDetails
                artifact={selected}
                loading={detailQuery.isLoading}
                error={detailQuery.error}
                detail={detailQuery.data ?? null}
              />
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}

function ArtifactTable({
  artifacts,
  selectedId,
  onSelect,
}: {
  artifacts: UploadedArtifact[];
  selectedId: string | null;
  onSelect: (artifactId: string) => void;
}) {
  return (
    <Table wrapperClassName="min-w-0">
      <THead>
        <TR>
          <TH>File</TH>
          <TH>Source</TH>
          <TH>Size</TH>
          <TH>Uploaded</TH>
          <TH>Storage</TH>
        </TR>
      </THead>
      <TBody>
        {artifacts.map((artifact) => (
          <TR
            className={cn(
              "cursor-pointer",
              artifact.artifact_id === selectedId && "bg-primary/5",
            )}
            key={artifact.artifact_id}
            onClick={() => onSelect(artifact.artifact_id)}
          >
            <TD>
              <div className="min-w-0">
                <div className="truncate font-semibold text-foreground">{artifact.filename}</div>
                <div className="truncate text-xs text-muted-foreground">
                  {artifact.mime_type} / {artifact.sha256.slice(0, 12)}
                </div>
              </div>
            </TD>
            <TD>
              <Badge variant="muted">{humanize(artifact.source)}</Badge>
            </TD>
            <TD>{formatBytes(artifact.byte_size)}</TD>
            <TD>{formatCompactDate(artifact.created_at)}</TD>
            <TD>
              <StorageBadge artifact={artifact} />
            </TD>
          </TR>
        ))}
      </TBody>
    </Table>
  );
}

function ArtifactDetails({
  artifact,
  loading,
  error,
  detail,
}: {
  artifact: UploadedArtifact | null;
  loading: boolean;
  error: unknown;
  detail: Awaited<ReturnType<typeof getWorkspaceArtifact>> | null;
}) {
  if (!artifact) {
    return (
      <aside className="border-l border-border/60 p-5 text-sm text-muted-foreground">
        Select a file to inspect metadata.
      </aside>
    );
  }
  return (
    <aside className="min-w-0 border-l border-border/60 bg-muted/10 p-5">
      <div className="flex min-w-0 items-start justify-between gap-3">
        <div className="min-w-0">
          <CardTitle className="truncate">{artifact.filename}</CardTitle>
          <div className="mt-1 text-xs text-muted-foreground">{artifact.artifact_id}</div>
        </div>
        <Button asChild size="sm" variant="outline">
          <a href={workspaceArtifactDownloadUrl(artifact.artifact_id, artifact)}>
            <Download className="h-4 w-4" />
            Download
          </a>
        </Button>
      </div>

      <div className="mt-4 grid gap-2 text-sm">
        <DetailRow label="MIME type" value={artifact.mime_type} />
        <DetailRow label="Byte size" value={formatBytes(artifact.byte_size)} />
        <DetailRow label="SHA256" value={artifact.sha256} mono />
        <DetailRow label="Owner" value={artifact.owner_user_id} mono />
        <DetailRow label="Workspace" value={artifact.organization_id ?? "legacy owner-only"} mono />
        <DetailRow label="Storage" value={storageLabel(artifact)} />
        <DetailRow label="Retention" value={humanize(artifact.retention_policy.action)} />
      </div>

      <div className="mt-5 grid gap-3">
        {loading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" /> Loading traces
          </div>
        ) : null}
        {error ? (
          <Notice title="Artifact detail could not be loaded" tone="danger">
            {workflowErrorMessage(error)}
          </Notice>
        ) : null}
        {detail ? (
          <>
            <DetailSection
              count={detail.traces.length}
              title="Extraction traces"
              empty="No extraction trace has been recorded yet."
            >
              {detail.traces.map((trace) => (
                <div className="rounded-lg border border-border/60 bg-card p-3" key={trace.trace_id}>
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant={trace.confidence >= 0.8 ? "success" : "warning"}>
                      {trace.extractor_chosen}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      {trace.char_count} chars / {trace.page_count ?? "n/a"} pages
                    </span>
                  </div>
                  {trace.warnings.length ? (
                    <div className="mt-2 text-xs text-amber-700">
                      {trace.warnings.slice(0, 3).join("; ")}
                    </div>
                  ) : null}
                </div>
              ))}
            </DetailSection>
            <DetailSection
              count={detail.access_events.length}
              title="Access events"
              empty="No access events recorded."
            >
              {detail.access_events.slice(0, 6).map((event) => (
                <div className="rounded-lg border border-border/60 bg-card p-3 text-xs" key={event.event_id}>
                  <div className="font-semibold text-foreground">{humanize(event.action)}</div>
                  <div className="mt-1 text-muted-foreground">
                    {formatCompactDate(event.timestamp)} / {event.actor_user_id}
                  </div>
                </div>
              ))}
            </DetailSection>
          </>
        ) : null}
      </div>
    </aside>
  );
}

function DetailSection({
  title,
  count,
  empty,
  children,
}: {
  title: string;
  count: number;
  empty: string;
  children: React.ReactNode;
}) {
  return (
    <section className="grid gap-2">
      <div className="flex items-center justify-between gap-2">
        <div className="text-sm font-bold text-foreground">{title}</div>
        <Badge variant="muted">{count}</Badge>
      </div>
      {count ? children : <div className="text-sm text-muted-foreground">{empty}</div>}
    </section>
  );
}

function DetailRow({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="grid gap-1 rounded-lg border border-border/50 bg-card p-3">
      <div className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
        {label}
      </div>
      <div className={cn("break-words text-sm text-foreground", mono && "font-mono text-xs")}>
        {value}
      </div>
    </div>
  );
}

function StorageBadge({ artifact }: { artifact: UploadedArtifact }) {
  const isObjectStore = artifact.storage_ref.startsWith("s3://");
  return (
    <Badge variant={isObjectStore ? "success" : "warning"}>
      {isObjectStore ? "MinIO" : "legacy local"}
    </Badge>
  );
}

function storageLabel(artifact: UploadedArtifact) {
  return artifact.storage_ref.startsWith("s3://") ? "MinIO object" : "Legacy local file";
}

function StatCard({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
}) {
  return (
    <Card>
      <CardContent className="flex items-center gap-3 p-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            {label}
          </div>
          <div className="text-base font-bold text-foreground">{value}</div>
        </div>
      </CardContent>
    </Card>
  );
}
