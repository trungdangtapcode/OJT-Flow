import { Image, Paperclip, Settings2, X } from "lucide-react";

import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { Label, Textarea } from "../../components/ui/form";
import { HelpTooltip } from "../../components/ui/help-tooltip";
import { formatBytes, formatCount } from "./assistant-format";

export function AttachmentPreview({
  file,
  onRemove,
}: {
  file: File;
  onRemove: () => void;
}) {
  const isImage = file.type.startsWith("image/");
  return (
    <div className="flex min-w-0 flex-wrap items-center justify-between gap-2 rounded-md border border-border bg-muted/30 px-3 py-2 text-sm">
      <div className="flex min-w-0 items-center gap-2">
        {isImage ? (
          <Image className="h-4 w-4 shrink-0 text-primary" />
        ) : (
          <Paperclip className="h-4 w-4 shrink-0 text-primary" />
        )}
        <div className="min-w-0">
          <div className="truncate font-black">{file.name}</div>
          <div className="text-xs text-muted-foreground">
            {file.type || "unknown type"} / {formatBytes(file.size)}
          </div>
        </div>
      </div>
      <Button
        aria-label="Remove attached file"
        onClick={onRemove}
        size="sm"
        type="button"
        variant="ghost"
      >
        <X className="h-4 w-4" />
      </Button>
    </div>
  );
}

export function AttachmentCapabilityBadge({
  availableExtractors,
  isLoading,
  supportedExtensions,
}: {
  availableExtractors: string[];
  isLoading: boolean;
  supportedExtensions: string[];
}) {
  const primaryExtractor = availableExtractors[0] ?? null;
  const hasVisionOcr = availableExtractors.includes("openai_vision");
  const imageCapable = supportedExtensions.some((extension) =>
    [".png", ".jpg", ".jpeg", ".webp", ".tiff", ".tif"].includes(extension.toLowerCase()),
  );
  return (
    <span className="flex min-w-0 flex-wrap items-center gap-1.5 text-xs font-semibold text-muted-foreground">
      <Badge variant={availableExtractors.length ? "success" : "warning"}>
        {isLoading
          ? "checking extractors"
          : hasVisionOcr
            ? "vision OCR enabled"
            : primaryExtractor
              ? `${primaryExtractor} parser`
              : "parser unavailable"}
      </Badge>
      {imageCapable ? <Badge variant="muted">image paste</Badge> : null}
      {supportedExtensions.length ? (
        <Badge variant="muted">{formatCount(supportedExtensions.length, "format")}</Badge>
      ) : null}
    </span>
  );
}

export function AssistantControlsPanel({
  contextText,
  executeWriteActions,
  onContextTextChange,
  onExecuteWriteActionsChange,
}: {
  contextText: string;
  executeWriteActions: boolean;
  onContextTextChange: (value: string) => void;
  onExecuteWriteActionsChange: (value: boolean) => void;
}) {
  return (
    <details className="group relative">
      <summary className="flex h-10 cursor-pointer list-none items-center gap-2 rounded-md border border-border bg-card px-3 text-sm font-black shadow-sm transition hover:border-primary">
        <Settings2 className="h-4 w-4 text-primary" />
        Advanced context
      </summary>
      <div className="absolute bottom-12 right-0 z-20 hidden w-[min(620px,calc(100vw-2rem))] gap-4 rounded-md border border-border bg-card p-4 shadow-lg group-open:grid">
        <div>
          <div className="text-sm font-black">Advanced context</div>
          <p className="mt-1 text-sm leading-6 text-muted-foreground">
            Context and safety gates for the next message.
          </p>
        </div>
        <label className="flex items-center gap-2 rounded-md border border-border bg-muted/35 px-3 py-2 text-sm font-semibold">
          <input
            checked={executeWriteActions}
            className="h-4 w-4 accent-primary"
            onChange={(event) => onExecuteWriteActionsChange(event.target.checked)}
            type="checkbox"
          />
          Execute write actions
          <HelpTooltip label="Execute write actions help">
            Keep this off for normal questions. Turn it on only when you explicitly want the assistant to run approved write-capable tools.
          </HelpTooltip>
        </label>
        <Label>
          <span className="inline-flex items-center gap-1.5">
            Optional context JSON
            <HelpTooltip label="Optional context JSON help">
              Structured data for the next message. Use this for schema IDs, formats, fields, or payload snippets when the chat text alone is not enough.
            </HelpTooltip>
          </span>
          <Textarea
            className="min-h-48 resize-y font-mono text-xs"
            onChange={(event) => onContextTextChange(event.target.value)}
            spellCheck={false}
            value={contextText}
          />
        </Label>
      </div>
    </details>
  );
}
