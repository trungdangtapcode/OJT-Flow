import * as React from "react";
import { Link, Outlet, useRouterState } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import {
  Bot,
  ClipboardCheck,
  Database,
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
import { useRuntimeConfigQuery } from "../../lib/server-state";
import { Button } from "../ui/button";
import { cn } from "../../lib/utils";

const navGroups = [
  {
    label: "Operations",
    items: [
      { to: "/assistant", label: "Assistant", icon: Bot },
      { to: "/workflows", label: "Workflows", icon: Layers },
      { to: "/reviews", label: "Reviews", icon: ClipboardCheck },
      { to: "/retrieval", label: "Retrieval", icon: Search },
      { to: "/audit", label: "Audit", icon: History },
    ],
  },
  {
    label: "Intake",
    items: [{ to: "/workbench", label: "Workbench", icon: FileCode }],
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
  const [refreshing, setRefreshing] = React.useState(false);
  const pathname = useRouterState({ select: (state) => state.location.pathname });
  const runtimeConfig = runtimeConfigQuery.data;
  const storageLabel = runtimeConfig
    ? `${runtimeConfig.storage_backend}${runtimeConfig.persistent_storage ? "" : " volatile"}`
    : "checking";
  const storageClass = runtimeConfig?.persistent_storage
    ? "bg-emerald-100 text-emerald-800"
    : "bg-amber-100 text-amber-800";
  const refreshApplicationData = async () => {
    setRefreshing(true);
    try {
      await queryClient.invalidateQueries();
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <div className="grid min-h-screen grid-cols-[204px_minmax(0,1fr)] bg-sidebar max-lg:grid-cols-1">
      <aside className="sticky top-0 z-20 flex h-dvh flex-col border-r border-black/15 bg-sidebar p-3 text-sidebar-foreground shadow-[inset_-1px_0_0_rgba(255,255,255,0.04)] max-lg:static max-lg:grid max-lg:h-auto max-lg:w-full max-lg:min-w-0 max-lg:grid-cols-[auto_minmax(0,1fr)] max-lg:items-center max-lg:gap-2 max-lg:border-b max-lg:border-r-0 max-lg:p-2 max-sm:grid-cols-1 max-sm:gap-0 max-sm:p-1.5">
        <div className="mb-6 flex shrink-0 items-center gap-3 px-1 max-lg:mb-0 max-lg:min-w-0 max-lg:px-0 max-sm:hidden">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-[#ccfbf1] text-[11px] font-black text-sidebar shadow-[0_8px_24px_rgba(45,212,191,0.16)] sm:h-9 sm:w-9 sm:rounded-lg sm:text-sm">
            OF
          </div>
          <div className="min-w-0 max-sm:sr-only">
            <div className="text-base font-extrabold">OJTFlow</div>
            <div className="whitespace-nowrap text-xs text-sidebar-foreground/62 max-sm:hidden">Clinical data ops</div>
          </div>
        </div>
        <nav className="grid gap-4 max-lg:flex max-lg:min-w-0 max-lg:justify-end max-lg:gap-1.5 max-lg:overflow-x-auto max-lg:pb-0 max-sm:grid max-sm:grid-cols-5 max-sm:justify-stretch max-sm:gap-1 max-sm:overflow-visible">
          {navGroups.map((group) => (
            <div className="grid gap-1 max-lg:contents" key={group.label}>
              <div className="px-3 text-[11px] font-bold uppercase tracking-wide text-sidebar-foreground/45 max-lg:hidden">
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
                      "mobile-nav-link flex h-9 items-center gap-3 rounded-md px-3 text-sm font-semibold text-sidebar-foreground/78 transition-colors hover:bg-white/10 hover:text-white max-lg:h-9 max-lg:min-w-[6.75rem] max-lg:shrink-0 max-lg:justify-center max-lg:bg-white/5 max-lg:px-3 max-lg:text-xs max-sm:h-11 max-sm:min-w-0 max-sm:shrink max-sm:px-0",
                      active && "bg-white/12 text-white ring-1 ring-white/12 shadow-[inset_3px_0_0_#5eead4] max-lg:shadow-none",
                    )}
                    key={item.to}
                    preload="intent"
                    title={item.label}
                    to={item.to}
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    <span className="max-sm:hidden">{item.label}</span>
                  </Link>
                );
              })}
            </div>
          ))}
        </nav>
      </aside>
      <main className="min-w-0 bg-background">
        <header className="sticky top-0 z-10 border-b border-border bg-card/88 backdrop-blur">
          <div className="mx-auto flex min-h-12 w-full max-w-[1440px] items-center justify-between gap-3 px-6 py-2 max-md:px-4 max-sm:gap-2 max-sm:px-3">
            <div className="hidden min-w-0 items-center gap-2 overflow-x-auto text-[11px] font-bold text-muted-foreground sm:flex">
              <span className="rounded-full bg-muted px-2 py-1">API {API_BASE_URL}</span>
              <span className={cn("shrink-0 rounded-full px-2 py-1", storageClass)}>
                {storageLabel}
              </span>
            </div>
            <div className="flex min-w-0 flex-1 items-center justify-end gap-2">
              <div className="flex h-9 min-w-0 flex-1 items-center gap-2 rounded-md border border-border bg-card px-2.5 shadow-sm md:max-w-[18rem]">
                <UserAvatar
                  avatarUrl={user?.avatar_url}
                  displayName={user?.display_name}
                  email={user?.email}
                />
                <div className="min-w-0">
                  <div className="truncate text-sm font-bold max-sm:text-xs">{user?.display_name || user?.email}</div>
                  <div className="truncate text-[11px] leading-4 text-muted-foreground max-sm:hidden">{user?.email}</div>
                </div>
              </div>
              <Button
                asChild
                className="shrink-0 max-sm:h-11 max-sm:w-11 max-sm:px-0"
                title="Assistant"
                type="button"
                variant="outline"
              >
                <Link aria-label="Open assistant" preload="intent" to="/assistant">
                  <Bot className="h-4 w-4" />
                  <span className="max-sm:hidden">Assistant</span>
                </Link>
              </Button>
              <Button
                aria-label="Refresh application data"
                className="max-sm:h-11 max-sm:w-11"
                disabled={refreshing}
                onClick={() => void refreshApplicationData()}
                size="icon"
                title="Refresh"
                type="button"
                variant="outline"
              >
                <RefreshCw className="h-4 w-4" />
              </Button>
              <Button
                aria-label="Sign out"
                className="max-sm:h-11 max-sm:w-11"
                onClick={() => void logout()}
                size="icon"
                title="Sign out"
                type="button"
                variant="outline"
              >
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </header>
        <div className="mx-auto w-full max-w-[1440px] p-6 max-md:p-4 max-sm:p-2">
          <Outlet />
        </div>
      </main>
    </div>
  );
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
        className="h-6 w-6 shrink-0 rounded-full border border-border bg-muted bg-cover bg-center"
        role="img"
        style={{ backgroundImage: `url("${escapeCssUrl(loadedAvatarUrl)}")` }}
      />
    );
  }

  if (initials) {
    return (
      <span
        aria-label={displayName || email || "User avatar"}
        className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-border bg-primary/10 text-[10px] font-black uppercase text-primary"
      >
        {initials}
      </span>
    );
  }

  return <UserCircle className="h-6 w-6 shrink-0 text-muted-foreground" />;
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
