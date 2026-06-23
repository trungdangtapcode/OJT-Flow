import * as React from "react";
import { Link, Outlet, useRouterState } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  Bot,
  BookOpen,
  ClipboardCheck,
  Database,
  Files,
  FileCode,
  HelpCircle,
  History,
  Layers,
  LogOut,
  RefreshCw,
  Search,
  Settings,
  UserCircle,
} from "lucide-react";

import { useAuth } from "../../app/auth";
import { API_BASE_URL } from "../../api";
import { useRuntimeConfigQuery, useRuntimeDisclaimersQuery } from "../../lib/server-state";
import { Button } from "../ui/button";
import { cn } from "../../lib/utils";
import { PageGuide } from "./page-guide";
import type { DisclaimerMessage, DisclaimerSurface } from "../../types";

const navGroups = [
  {
    label: "Operations",
    items: [
      { to: "/assistant", label: "Assistant", icon: Bot },
      { to: "/knowledge", label: "Knowledge", icon: BookOpen },
      { to: "/workflows", label: "Workflows", icon: Layers },
      { to: "/reviews", label: "Reviews", icon: ClipboardCheck },
      { to: "/retrieval", label: "Retrieval", icon: Search },
      { to: "/audit", label: "Audit", icon: History },
    ],
  },
  {
    label: "Intake",
    items: [
      { to: "/workbench", label: "Workbench", icon: FileCode },
      { to: "/files", label: "Files", icon: Files },
    ],
  },
  {
    label: "Governance",
    items: [
      { to: "/schemas", label: "Schemas", icon: Database },
      { to: "/settings", label: "Settings", icon: Settings },
      { to: "/help", label: "Help", icon: HelpCircle },
    ],
  },
];

export function AppShell() {
  const { user, logout } = useAuth();
  const queryClient = useQueryClient();
  const runtimeConfigQuery = useRuntimeConfigQuery();
  const disclaimersQuery = useRuntimeDisclaimersQuery();
  const [refreshing, setRefreshing] = React.useState(false);
  const pathname = useRouterState({ select: (state) => state.location.pathname });
  const runtimeConfig = runtimeConfigQuery.data;
  const storageLabel = runtimeConfig
    ? `${runtimeConfig.storage_backend}${
        runtimeConfig.object_storage_backend
          ? ` + ${runtimeConfig.object_storage_backend}`
          : ""
      }${runtimeConfig.persistent_storage ? "" : " volatile"}`
    : "checking";
  const storageClass = runtimeConfig?.persistent_storage
    ? "bg-emerald-50 text-emerald-700 border-emerald-200"
    : "bg-amber-50 text-amber-700 border-amber-200";
  const refreshApplicationData = async () => {
    setRefreshing(true);
    try {
      await queryClient.invalidateQueries();
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <div className="grid h-dvh min-h-dvh grid-cols-[240px_minmax(0,1fr)] overflow-hidden bg-background max-lg:h-auto max-lg:min-h-screen max-lg:grid-cols-1 max-lg:overflow-visible">
      {/* ── Sidebar ── */}
      <aside className="sticky top-0 z-20 flex h-dvh flex-col bg-sidebar p-4 text-sidebar-foreground max-lg:static max-lg:grid max-lg:h-auto max-lg:w-full max-lg:min-w-0 max-lg:grid-cols-[auto_minmax(0,1fr)] max-lg:items-center max-lg:gap-2 max-lg:border-b max-lg:border-slate-800 max-lg:p-2 max-sm:grid-cols-1 max-sm:gap-0 max-sm:p-1.5">
        <div className="mb-8 flex shrink-0 items-center gap-3 px-2 max-lg:mb-0 max-lg:min-w-0 max-lg:px-0 max-sm:hidden">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-400 to-teal-500 text-xs font-black text-white shadow-lg shadow-cyan-500/20">
            OF
          </div>
          <div className="min-w-0 max-sm:sr-only">
            <div className="text-[15px] font-extrabold tracking-tight text-white">OJTFlow</div>
            <div className="text-[11px] font-medium text-slate-400">Clinical data ops</div>
          </div>
        </div>

        <nav className="grid gap-6 max-lg:flex max-lg:min-w-0 max-lg:justify-end max-lg:gap-1.5 max-lg:overflow-x-auto max-lg:pb-0 max-sm:grid max-sm:grid-cols-5 max-sm:justify-stretch max-sm:gap-1 max-sm:overflow-visible">
          {navGroups.map((group) => (
            <div className="grid gap-1 max-lg:contents" key={group.label}>
              <div className="mb-1 px-3 text-[10px] font-semibold uppercase tracking-[0.15em] text-slate-500 max-lg:hidden">
                {group.label}
              </div>
              {group.items.map((item) => {
                const Icon = item.icon;
                const active = pathname === item.to || pathname.startsWith(`${item.to}/`);
                return (
                  <Link
                    aria-current={active ? "page" : undefined}
                    aria-label={item.label}
                    data-active={active ? "true" : undefined}
                    className={cn(
                      "group flex h-10 items-center gap-3 rounded-xl px-3 text-[13px] font-medium text-slate-400 transition-all duration-200 hover:bg-white/[0.06] hover:text-slate-200 max-lg:h-9 max-lg:min-w-[6.75rem] max-lg:shrink-0 max-lg:justify-center max-lg:bg-white/5 max-lg:px-3 max-lg:text-xs max-sm:h-11 max-sm:min-w-0 max-sm:shrink max-sm:px-0",
                      active && "bg-white/[0.08] font-semibold text-white",
                    )}
                    key={item.to}
                    preload="intent"
                    title={item.label}
                    to={item.to}
                  >
                    <span className={cn(
                      "flex h-7 w-7 shrink-0 items-center justify-center rounded-lg transition-colors max-lg:h-auto max-lg:w-auto max-lg:rounded-none max-lg:bg-transparent",
                      active
                        ? "bg-cyan-500/20 text-cyan-400"
                        : "text-slate-500 group-hover:text-slate-300",
                    )}>
                      <Icon className="h-4 w-4" />
                    </span>
                    <span className="max-sm:hidden">{item.label}</span>
                  </Link>
                );
              })}
            </div>
          ))}
        </nav>

        {/* Sidebar footer */}
        <div className="mt-auto hidden border-t border-white/[0.06] pt-3 max-lg:hidden lg:block">
          <div className="flex items-center gap-2 rounded-lg px-2 py-1.5">
            <UserAvatar
              avatarUrl={user?.avatar_url}
              displayName={user?.display_name}
              email={user?.email}
            />
            <div className="min-w-0 flex-1">
              <div className="truncate text-xs font-semibold text-slate-300">{user?.display_name || user?.email}</div>
            </div>
            <button
              aria-label="Sign out"
              className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-slate-500 transition-colors hover:bg-white/[0.06] hover:text-slate-300"
              onClick={() => void logout()}
              title="Sign out"
              type="button"
            >
              <LogOut className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </aside>

      {/* ── Main ── */}
      <main className="flex min-h-0 min-w-0 flex-col overflow-hidden bg-background max-lg:min-h-screen max-lg:overflow-visible">
        <header className="z-10 shrink-0 border-b border-border/50 bg-white/80 shadow-[var(--shadow-header)] backdrop-blur-md">
          <div className="mx-auto flex h-14 w-full max-w-[1440px] items-center justify-between gap-4 px-8 max-md:px-4 max-sm:gap-2 max-sm:px-3">
            <div className="hidden items-center gap-2 text-xs font-medium text-muted-foreground md:flex">
              <span className="rounded-md border border-border/60 bg-muted/50 px-2 py-0.5">{API_BASE_URL}</span>
              <span className={cn("rounded-md border px-2 py-0.5", storageClass)}>
                {storageLabel}
              </span>
            </div>
            <div className="flex flex-1 items-center justify-end gap-2">
              <Button
                asChild
                className="shrink-0 max-sm:h-10 max-sm:w-10 max-sm:px-0"
                title="Assistant"
                type="button"
                variant="default"
              >
                <Link aria-label="Open assistant" preload="intent" to="/assistant">
                  <Bot className="h-4 w-4" />
                  <span className="max-sm:hidden">Assistant</span>
                </Link>
              </Button>
              <Button
                aria-label="Refresh application data"
                className="max-sm:h-10 max-sm:w-10"
                disabled={refreshing}
                onClick={() => void refreshApplicationData()}
                size="icon"
                title="Refresh"
                type="button"
                variant="ghost"
              >
                <RefreshCw className={cn("h-4 w-4", refreshing && "animate-spin")} />
              </Button>
              <div className="hidden lg:hidden max-lg:flex">
                <Button
                  aria-label="Sign out"
                  className="max-sm:h-10 max-sm:w-10"
                  onClick={() => void logout()}
                  size="icon"
                  title="Sign out"
                  type="button"
                  variant="ghost"
                >
                  <LogOut className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </header>
        <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain max-lg:overflow-visible">
          <div className="mx-auto w-full max-w-[1440px] px-5 py-5 max-md:p-4 max-sm:p-3">
            <Outlet />
            <div className="mt-6">
              <ClinicalBoundaryBanner
                message={disclaimerMessageForPath(disclaimersQuery.data?.surfaces, pathname)}
              />
              <PageGuide pathname={pathname} />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

function ClinicalBoundaryBanner({ message }: { message?: DisclaimerMessage | null }) {
  if (!message) return null;
  const severityClass =
    message.severity === "critical"
      ? "border-red-200 bg-red-50 text-red-950"
      : message.severity === "caution"
        ? "border-amber-200 bg-amber-50 text-amber-950"
        : "border-border bg-muted/40 text-muted-foreground";
  const iconClass =
    message.severity === "critical"
      ? "text-red-600"
      : message.severity === "caution"
        ? "text-amber-600"
        : "text-muted-foreground";
  return (
    <details className={cn("mb-4 rounded-lg border px-3 py-2 text-xs", severityClass)}>
      <summary className="flex cursor-pointer list-none flex-wrap items-center gap-2">
        <AlertTriangle className={cn("h-3.5 w-3.5", iconClass)} />
        <span className="text-xs font-bold">{message.title}</span>
        {message.review_required ? (
          <span className="rounded-full border border-current/20 bg-white/50 px-1.5 py-0.5 text-[10px] font-bold">
            human review required
          </span>
        ) : null}
        {message.prohibited_uses.length ? (
          <span className="hidden text-[10px] text-muted-foreground sm:inline">
            — Not for: {message.prohibited_uses.join(", ")}
          </span>
        ) : null}
      </summary>
      <div className="mt-2 grid gap-2 text-xs leading-5">
        <p className="leading-5">{message.message}</p>
        <div className="grid gap-2 sm:grid-cols-2">
          <div>
            <span className="font-bold">Review: </span>
            {message.human_review_text}
          </div>
          <div>
            <span className="font-bold">Evidence: </span>
            {message.evidence_text}
          </div>
        </div>
        {message.prohibited_uses.length ? (
          <div className="flex flex-wrap gap-1 sm:hidden">
            {message.prohibited_uses.map((use) => (
              <span
                className="rounded-full border border-current/20 bg-white/45 px-1.5 py-0.5 text-[10px] font-semibold"
                key={use}
              >
                {use}
              </span>
            ))}
          </div>
        ) : null}
      </div>
    </details>
  );
}

function disclaimerMessageForPath(
  surfaces: DisclaimerMessage[] | undefined,
  pathname: string,
): DisclaimerMessage | null {
  if (!surfaces?.length) return null;
  const surfaceId = disclaimerSurfaceForPath(pathname);
  return (
    surfaces.find((surface) => surface.surface_id === surfaceId) ??
    surfaces.find((surface) => surface.surface_id === "global") ??
    null
  );
}

function disclaimerSurfaceForPath(pathname: string): DisclaimerSurface {
  if (pathname.startsWith("/assistant")) return "assistant";
  if (pathname.startsWith("/workbench")) return "workbench";
  if (pathname.startsWith("/workflows/")) return "workflow_detail";
  if (pathname.startsWith("/workflows")) return "workflows";
  if (pathname.startsWith("/reviews")) return "reviews";
  if (pathname.startsWith("/knowledge")) return "retrieval";
  if (pathname.startsWith("/retrieval")) return "retrieval";
  if (pathname.startsWith("/audit")) return "audit";
  if (pathname.startsWith("/schemas")) return "schemas";
  if (pathname.startsWith("/settings")) return "settings";
  if (pathname.startsWith("/help")) return "help";
  return "global";
}

function UserAvatar({
  avatarUrl,
  displayName,
  email,
}: {
  avatarUrl?: string | null;
  displayName?: string | null;
  email?: string | null;
}) {
  const normalizedAvatarUrl = normalizeAvatarUrl(avatarUrl);
  const [loadedAvatarUrl, setLoadedAvatarUrl] = React.useState<string | null>(null);
  const initials = userInitials(displayName, email);

  React.useEffect(() => {
    setLoadedAvatarUrl(null);
    if (!normalizedAvatarUrl) return;

    let cancelled = false;
    const image = new Image();
    image.referrerPolicy = "no-referrer";
    image.onload = () => {
      if (!cancelled) setLoadedAvatarUrl(normalizedAvatarUrl);
    };
    image.onerror = () => {
      if (!cancelled) setLoadedAvatarUrl(null);
    };
    image.src = normalizedAvatarUrl;

    return () => {
      cancelled = true;
    };
  }, [normalizedAvatarUrl]);

  if (loadedAvatarUrl) {
    return (
      <span
        aria-label={displayName || email || "User avatar"}
        className="h-7 w-7 shrink-0 rounded-full bg-slate-700 bg-cover bg-center ring-2 ring-white/10"
        role="img"
        style={{ backgroundImage: `url("${escapeCssUrl(loadedAvatarUrl)}")` }}
      />
    );
  }

  if (initials) {
    return (
      <span
        aria-label={displayName || email || "User avatar"}
        className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-cyan-500 to-teal-600 text-[10px] font-bold text-white ring-2 ring-white/10"
      >
        {initials}
      </span>
    );
  }

  return <UserCircle className="h-7 w-7 shrink-0 text-slate-500" />;
}

function userInitials(displayName?: string | null, email?: string | null) {
  const source = (displayName || email?.split("@")[0] || "").trim();
  if (!source) return "";
  const parts = source.split(/\s+/).filter(Boolean);
  if (parts.length >= 2) {
    return `${firstGrapheme(parts[0])}${firstGrapheme(parts[parts.length - 1])}`.toUpperCase();
  }
  const compact = source.replace(/[^A-Za-z0-9]/g, "");
  return compact.slice(0, 2).toUpperCase() || firstGrapheme(source).toUpperCase();
}

function firstGrapheme(value: string) {
  return Array.from(value)[0] ?? "";
}

function normalizeAvatarUrl(value?: string | null) {
  if (!value) return null;
  try {
    const url = new URL(value);
    return url.protocol === "https:" || url.protocol === "http:" ? url.toString() : null;
  } catch {
    return null;
  }
}

function escapeCssUrl(value: string) {
  return value.replace(/["\\]/g, "\\$&");
}
