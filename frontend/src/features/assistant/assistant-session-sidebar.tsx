import { Plus, Search, Trash2 } from "lucide-react";

import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/form";
import { cn } from "../../lib/utils";
import { formatCount } from "./assistant-format";
import type { AssistantChatSession } from "./assistant-session";
import { relativeSessionTime } from "./assistant-session";

export function AssistantSessionSidebar({
  activeSessionId,
  isBusy = false,
  onDeleteSession,
  onNewSession,
  onSelectSession,
  onSearchTextChange,
  searchText,
  sessions,
}: {
  activeSessionId: string;
  isBusy?: boolean;
  onDeleteSession: (sessionId: string) => void;
  onNewSession: () => void;
  onSelectSession: (sessionId: string) => void;
  onSearchTextChange: (value: string) => void;
  searchText: string;
  sessions: AssistantChatSession[];
}) {
  return (
    <aside className="grid min-h-0 rounded-lg border border-border bg-card shadow-sm lg:h-full lg:grid-rows-[auto_minmax(0,1fr)] lg:overflow-hidden">
      <div className="flex items-center justify-between gap-2 border-b border-border p-3">
        <div>
          <div className="text-sm font-black">Chats</div>
          <div className="text-xs text-muted-foreground">
            {formatCount(sessions.length, "session")}
          </div>
        </div>
        <Button
          disabled={isBusy}
          onClick={onNewSession}
          size="sm"
          type="button"
          variant="outline"
        >
          <Plus className="h-4 w-4" />
          New
        </Button>
      </div>
      <div className="grid min-h-0 grid-rows-[auto_minmax(0,1fr)]">
        <label className="relative p-2">
          <Search className="pointer-events-none absolute left-5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            aria-label="Search chats"
            className="pl-9"
            disabled={isBusy}
            onChange={(event) => onSearchTextChange(event.target.value)}
            placeholder="Search chats"
            value={searchText}
          />
        </label>
        <div className="grid max-h-72 content-start gap-1 overflow-y-auto overscroll-contain p-2 pt-0 lg:max-h-none">
          {sessions.length === 0 ? (
            <div className="rounded-md border border-dashed border-border p-3 text-xs font-semibold text-muted-foreground">
              {searchText ? "No chats match this search." : "No saved chats yet."}
            </div>
          ) : null}
          {sessions.map((session) => (
            <div
              className={cn(
                "group grid gap-1 rounded-md border p-2 text-left transition",
                session.id === activeSessionId
                  ? "border-primary bg-primary/5"
                  : "border-transparent hover:border-border hover:bg-muted/40",
              )}
              key={session.id}
            >
              <button
                className="grid min-w-0 gap-1 text-left focus-ring"
                onClick={() => onSelectSession(session.id)}
                type="button"
              >
                <div className="line-clamp-2 break-words text-sm font-black">
                  {session.title}
                </div>
                <div className="flex min-w-0 flex-wrap gap-2 text-[11px] font-semibold text-muted-foreground">
                  <span>{formatCount(session.messageCount, "message")}</span>
                  <span>{relativeSessionTime(session.updatedAt)}</span>
                </div>
              </button>
              <div className="flex justify-end">
                <Button
                  aria-label={`Delete chat ${session.title}`}
                  disabled={isBusy}
                  onClick={() => onDeleteSession(session.id)}
                  size="sm"
                  type="button"
                  variant="ghost"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
}
