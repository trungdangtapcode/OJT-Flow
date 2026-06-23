import { MessageSquareText } from "lucide-react";

import { Badge } from "../../components/ui/badge";
import { HelpTooltip } from "../../components/ui/help-tooltip";
import { Notice } from "../../components/ui/notice";
import { humanize } from "../../lib/utils";
import type { AssistantToolSpec } from "../../types";

export function ToolCatalogPanel({
  error,
  isLoading,
  tools,
}: {
  error: string | null;
  isLoading: boolean;
  tools: AssistantToolSpec[];
}) {
  return (
    <details className="group relative">
      <summary className="flex h-10 cursor-pointer list-none items-center gap-2 rounded-lg border border-border/60 bg-card px-3 text-sm font-black shadow-sm transition hover:border-primary">
        <MessageSquareText className="h-4 w-4 text-primary" />
        Tool catalog
        <HelpTooltip label="Tool catalog help">
          The real backend tools the assistant is allowed to call. Approval badges mean a tool can pause or require human review before changing state.
        </HelpTooltip>
        <Badge variant="muted">{isLoading ? "loading" : `${tools.length}`}</Badge>
      </summary>
      <div className="absolute bottom-12 right-0 z-20 grid max-h-[560px] w-[min(720px,calc(100vw-2rem))] gap-3 overflow-auto rounded-lg border border-border/60 bg-card p-4 shadow-lg max-sm:left-0 max-sm:right-auto">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <div className="text-sm font-black">Assistant tool catalog</div>
            <p className="mt-1 text-sm leading-6 text-muted-foreground">
              Server allowlist used by chat and local MCP clients.
            </p>
          </div>
          <Badge variant="muted">{isLoading ? "loading" : `${tools.length} tools`}</Badge>
        </div>
        {error ? (
          <Notice title="Tool catalog unavailable" tone="danger">
            {error}
          </Notice>
        ) : null}
        {!error && isLoading ? (
          <div className="grid gap-2">
            {Array.from({ length: 4 }).map((_, index) => (
              <div
                aria-hidden="true"
                className="h-16 rounded-lg border border-border/60 bg-muted/35"
                key={index}
              />
            ))}
          </div>
        ) : null}
        {!error && !isLoading ? (
          <div className="grid gap-2">
            {tools.map((tool) => (
              <div className="rounded-lg border border-border/60 bg-muted/20 p-3" key={tool.name}>
                <div className="flex flex-wrap items-center gap-2">
                  <div className="min-w-0 flex-1 break-words font-mono text-sm font-black">
                    {tool.name}
                  </div>
                  <Badge variant={tool.requires_approval ? "warning" : "success"}>
                    {tool.requires_approval ? "approval" : "read/run"}
                  </Badge>
                  <Badge variant={tool.risk_level === "high" ? "warning" : "muted"}>
                    {humanize(tool.risk_level)}
                  </Badge>
                  <Badge variant="muted">{humanize(tool.permission_scope)}</Badge>
                </div>
                <p className="mt-1 text-sm leading-6 text-muted-foreground">
                  {tool.description}
                </p>
                {tool.permission_tags.length ? (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {tool.permission_tags.slice(0, 6).map((tag) => (
                      <Badge key={tag} variant="muted">
                        {humanize(tag)}
                      </Badge>
                    ))}
                  </div>
                ) : null}
                {tool.approval_reason ? (
                  <p className="mt-2 text-xs font-semibold leading-5 text-muted-foreground">
                    {tool.approval_reason}
                  </p>
                ) : null}
              </div>
            ))}
          </div>
        ) : null}
      </div>
    </details>
  );
}
