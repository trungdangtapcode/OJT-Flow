import { Building2, Copy, Loader2, Plus, Trash2, UserPlus } from "lucide-react";
import * as React from "react";

import {
  createInvitation,
  createWorkspace,
  listInvitations,
  listWorkspaces,
  revokeInvitation,
} from "../../api";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { Input, Label, Select } from "../../components/ui/form";
import { Notice } from "../../components/ui/notice";
import type { Workspace, WorkspaceInvitation } from "../../types";

const ASSIGNABLE_ROLES = ["operator", "reviewer", "viewer", "data-steward"];

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

export function WorkspacesPanel() {
  const [workspaces, setWorkspaces] = React.useState<Workspace[]>([]);
  const [selectedId, setSelectedId] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const refreshWorkspaces = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await listWorkspaces();
      setWorkspaces(result.items);
      setSelectedId((current) => current ?? result.items[0]?.organization.organization_id ?? null);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void refreshWorkspaces();
  }, [refreshWorkspaces]);

  const selected = workspaces.find(
    (workspace) => workspace.organization.organization_id === selectedId,
  );
  const canManageMembers = selected?.effective_permission_scopes.includes("users:write") ?? false;

  return (
    <Card className="min-w-0 overflow-hidden xl:col-span-2">
      <CardHeader className="border-b border-border/60 bg-muted/30">
        <div className="flex min-w-0 flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <CardTitle className="flex items-center gap-2">
              <Building2 className="h-5 w-5 text-primary" />
              Workspaces and members
            </CardTitle>
            <CardDescription>
              Create organization workspaces and invite teammates by email.
            </CardDescription>
          </div>
          <Badge variant="muted">{workspaces.length} workspace(s)</Badge>
        </div>
      </CardHeader>
      <CardContent className="grid gap-4 pt-4 sm:pt-5 lg:grid-cols-2">
        {error ? (
          <Notice title="Workspace data unavailable" tone="danger">
            {error}
          </Notice>
        ) : null}

        <div className="grid content-start gap-3">
          <div className="text-sm font-bold text-foreground">Your workspaces</div>
          {loading ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" /> Loading workspaces
            </div>
          ) : null}
          <div className="grid gap-2">
            {workspaces.map((workspace) => {
              const isSelected = workspace.organization.organization_id === selectedId;
              return (
                <button
                  className={`flex min-w-0 flex-wrap items-center justify-between gap-2 rounded-lg border px-3 py-2 text-left text-sm ${
                    isSelected
                      ? "border-primary bg-primary/5"
                      : "border-border/60 bg-card hover:bg-muted/40"
                  }`}
                  key={workspace.organization.organization_id}
                  onClick={() => setSelectedId(workspace.organization.organization_id)}
                  type="button"
                >
                  <span className="min-w-0">
                    <span className="block truncate font-semibold">
                      {workspace.organization.display_name}
                    </span>
                    <span className="block truncate text-xs text-muted-foreground">
                      {workspace.organization.slug}
                    </span>
                  </span>
                  <Badge variant="muted">{workspace.membership.role_key}</Badge>
                </button>
              );
            })}
            {!loading && !workspaces.length ? (
              <div className="text-sm text-muted-foreground">No workspaces yet.</div>
            ) : null}
          </div>
          <CreateWorkspaceForm onCreated={refreshWorkspaces} />
        </div>

        <div className="grid content-start gap-3">
          {selected ? (
            <MembersPanel
              canManage={canManageMembers}
              organizationId={selected.organization.organization_id}
            />
          ) : (
            <div className="text-sm text-muted-foreground">
              Select a workspace to manage invitations.
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function CreateWorkspaceForm({ onCreated }: { onCreated: () => Promise<void> }) {
  const [displayName, setDisplayName] = React.useState("");
  const [pending, setPending] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    const name = displayName.trim();
    if (!name) return;
    setPending(true);
    setError(null);
    try {
      await createWorkspace({ display_name: name });
      setDisplayName("");
      await onCreated();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setPending(false);
    }
  };

  return (
    <form className="grid gap-2 rounded-lg border border-border/60 bg-muted/20 p-3" onSubmit={submit}>
      <Label>
        New workspace name
        <Input
          onChange={(event) => setDisplayName(event.target.value)}
          placeholder="Radiology Operations"
          type="text"
          value={displayName}
        />
      </Label>
      {error ? (
        <Notice title="Could not create workspace" tone="danger">
          {error}
        </Notice>
      ) : null}
      <Button disabled={pending || !displayName.trim()} type="submit">
        {pending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
        Create workspace
      </Button>
    </form>
  );
}

function MembersPanel({
  canManage,
  organizationId,
}: {
  canManage: boolean;
  organizationId: string;
}) {
  const [invitations, setInvitations] = React.useState<WorkspaceInvitation[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [email, setEmail] = React.useState("");
  const [roleKey, setRoleKey] = React.useState(ASSIGNABLE_ROLES[0]);
  const [pending, setPending] = React.useState(false);
  const [lastInviteUrl, setLastInviteUrl] = React.useState<string | null>(null);
  const [copied, setCopied] = React.useState(false);

  const refresh = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await listInvitations(organizationId);
      setInvitations(result.items);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [organizationId]);

  React.useEffect(() => {
    setLastInviteUrl(null);
    void refresh();
  }, [refresh]);

  const invite = async (event: React.FormEvent) => {
    event.preventDefault();
    const trimmed = email.trim();
    if (!trimmed) return;
    setPending(true);
    setError(null);
    try {
      const result = await createInvitation(organizationId, { email: trimmed, role_key: roleKey });
      setEmail("");
      setLastInviteUrl(result.invite_url);
      setCopied(false);
      await refresh();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setPending(false);
    }
  };

  const copyLink = async (url: string) => {
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  };

  const revoke = async (invitationId: string) => {
    try {
      await revokeInvitation(organizationId, invitationId);
      await refresh();
    } catch (err) {
      setError(errorMessage(err));
    }
  };

  return (
    <div className="grid gap-3">
      <div className="text-sm font-bold text-foreground">Invitations</div>

      {canManage ? (
        <form className="grid gap-2 rounded-lg border border-border/60 bg-muted/20 p-3" onSubmit={invite}>
          <Label>
            Invite by email
            <Input
              onChange={(event) => setEmail(event.target.value)}
              placeholder="teammate@example.org"
              type="email"
              value={email}
            />
          </Label>
          <Label>
            Role
            <Select onChange={(event) => setRoleKey(event.target.value)} value={roleKey}>
              {ASSIGNABLE_ROLES.map((role) => (
                <option key={role} value={role}>
                  {role}
                </option>
              ))}
            </Select>
          </Label>
          <Button disabled={pending || !email.trim()} type="submit">
            {pending ? <Loader2 className="h-4 w-4 animate-spin" /> : <UserPlus className="h-4 w-4" />}
            Send invitation
          </Button>
        </form>
      ) : (
        <Notice title="Read-only">
          You need the users:write permission to invite members to this workspace.
        </Notice>
      )}

      {lastInviteUrl ? (
        <div className="grid gap-2 rounded-lg border border-primary/40 bg-primary/5 p-3 text-sm">
          <div className="font-semibold text-foreground">Share this invite link</div>
          <code className="break-all rounded bg-card px-2 py-1 font-mono text-xs">{lastInviteUrl}</code>
          <Button onClick={() => void copyLink(lastInviteUrl)} type="button" variant="secondary">
            <Copy className="h-4 w-4" />
            {copied ? "Copied" : "Copy link"}
          </Button>
        </div>
      ) : null}

      {error ? (
        <Notice title="Invitation error" tone="danger">
          {error}
        </Notice>
      ) : null}

      <div className="grid gap-2">
        {loading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" /> Loading invitations
          </div>
        ) : null}
        {invitations.map((invitation) => (
          <div
            className="flex min-w-0 flex-wrap items-center justify-between gap-2 rounded-lg border border-border/60 bg-card px-3 py-2 text-sm"
            key={invitation.invitation_id}
          >
            <span className="min-w-0">
              <span className="block truncate font-semibold">{invitation.email}</span>
              <span className="block text-xs text-muted-foreground">
                {invitation.role_key}
              </span>
            </span>
            <span className="flex items-center gap-2">
              <Badge variant={invitationVariant(invitation.status)}>{invitation.status}</Badge>
              {canManage && invitation.status === "pending" ? (
                <Button
                  onClick={() => void revoke(invitation.invitation_id)}
                  type="button"
                  variant="ghost"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              ) : null}
            </span>
          </div>
        ))}
        {!loading && !invitations.length ? (
          <div className="text-sm text-muted-foreground">No invitations yet.</div>
        ) : null}
      </div>
    </div>
  );
}

function invitationVariant(
  status: WorkspaceInvitation["status"],
): React.ComponentProps<typeof Badge>["variant"] {
  if (status === "accepted") return "success";
  if (status === "pending") return "warning";
  return "muted";
}
